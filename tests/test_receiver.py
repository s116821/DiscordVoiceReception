from __future__ import annotations

import asyncio
import inspect
from types import SimpleNamespace

from discord.opus import Decoder, Encoder
from discord.voice_state import VoiceConnectionState

from discord_voice_reception import AudioFrame, Receiver, VoiceRecvClient
from test_transport import state, wire


class Sink:
    def __init__(self, expected: int = 1) -> None:
        self.frames: list[AudioFrame] = []
        self.closed: list[str] = []
        self.event = asyncio.Event()
        self.expected = expected

    async def write(self, frame: AudioFrame) -> None:
        self.frames.append(frame)
        if len(self.frames) >= self.expected:
            self.event.set()

    async def close(self, reason: str) -> None:
        self.closed.append(reason)


def test_multiple_speakers_and_consumers() -> None:
    async def run() -> None:
        sinks = [Sink(2), Sink(2)]
        receiver = Receiver(1, 2, state, sinks, decode_pcm=False, reorder_seconds=0)
        receiver.bind(42, 100)
        receiver.bind(43, 200)
        receiver.start()
        receiver.feed_datagram(wire(b"one"))
        receiver.feed_datagram(wire(b"two", ssrc=43))
        await asyncio.wait_for(sinks[0].event.wait(), 1)
        assert [f.member_id for f in sinks[0].frames] == [100, 200]
        assert [f.opus for f in sinks[1].frames] == [b"one", b"two"]
        assert receiver.health.capture_ready and receiver.health.last_frame_at is not None
        await receiver.close("test finished")
        await receiver.close("again")
        assert all(s.closed == ["test finished"] for s in sinks)
        assert not receiver.health.listening

    asyncio.run(run())


def test_ssrc_reuse_unknown_source_and_reconnect() -> None:
    async def run() -> None:
        sink = Sink()
        receiver = Receiver(1, 2, state, [sink], decode_pcm=False, reorder_seconds=0)
        receiver.bind(42, 100)
        receiver.start()
        receiver.feed_datagram(wire(b"old"))
        receiver.bind(42, 200)
        receiver.feed_datagram(wire(b"unknown", ssrc=99))
        receiver.feed_datagram(wire(b"new"))
        await asyncio.wait_for(sink.event.wait(), 1)
        assert [(f.member_id, f.opus) for f in sink.frames] == [(200, b"new")]
        receiver.reset(3)
        receiver.feed_datagram(wire(b"after reset"))
        receiver.bind(42, 300)
        sink.event.clear()
        sink.expected = 2
        receiver.feed_datagram(wire(b"fresh"))
        await asyncio.wait_for(sink.event.wait(), 1)
        assert sink.frames[-1].channel_id == 3 and sink.frames[-1].member_id == 300
        assert receiver.health.dropped_frames >= 3
        await receiver.close()

    asyncio.run(run())


def test_reordering_duplicate_and_sequence_wrap() -> None:
    async def run() -> None:
        sink = Sink(3)
        receiver = Receiver(1, 2, state, [sink], decode_pcm=False, reorder_seconds=0.01)
        receiver.bind(42, 100)
        receiver.start()
        receiver.feed_datagram(wire(b"b", seq=65535))
        receiver.feed_datagram(wire(b"a", seq=65534))
        receiver.feed_datagram(wire(b"c", seq=0))
        receiver.feed_datagram(wire(b"duplicate", seq=0))
        await asyncio.wait_for(sink.event.wait(), 1)
        assert [f.sequence for f in sink.frames] == [65534, 65535, 0]
        assert receiver.health.dropped_frames == 1
        await receiver.close()

    asyncio.run(run())


def test_bounded_queue_and_close_before_task_runs() -> None:
    async def run() -> None:
        sink = Sink()
        receiver = Receiver(1, 2, state, [sink], decode_pcm=False, max_queue=2)
        receiver.bind(42, 100)
        receiver.start()
        for seq in range(10):
            receiver.feed_datagram(wire(b"x", seq=seq))
        assert receiver.health.backlog == 2 and receiver.health.dropped_frames == 8
        await receiver.close("immediate")
        assert sink.closed == ["immediate"]

    asyncio.run(run())


def test_real_opus_decode_and_bounded_concealment() -> None:
    async def run() -> None:
        encoded = Encoder().encode(bytes(Encoder.FRAME_SIZE), Encoder.SAMPLES_PER_FRAME)
        sink = Sink()
        receiver = Receiver(1, 2, state, [sink], reorder_seconds=0)
        receiver.bind(42, 100)
        receiver.start()
        receiver.feed_datagram(wire(encoded))
        await asyncio.wait_for(sink.event.wait(), 1)
        assert len(sink.frames[0].pcm or b"") == Decoder.FRAME_SIZE
        sink.expected = 3
        sink.event.clear()
        receiver.feed_datagram(wire(encoded, seq=3))
        await asyncio.wait_for(sink.event.wait(), 1)
        assert sink.frames[1].concealed
        assert sink.frames[1].opus == b"" and len(sink.frames[1].pcm or b"") == Decoder.FRAME_SIZE
        await receiver.close()

    asyncio.run(run())


def test_sdk_seam_and_mapping_reset_contract() -> None:
    assert "hook" in inspect.signature(VoiceConnectionState).parameters
    assert callable(VoiceConnectionState.add_socket_listener)
    assert callable(VoiceConnectionState.remove_socket_listener)

    async def run() -> None:
        client = object.__new__(VoiceRecvClient)
        client._receiver = None
        client._speakers = {}
        client.channel = SimpleNamespace(id=20)
        await client._voice_hook(None, {"op": 5, "d": {"ssrc": 42, "user_id": "100"}})
        assert client._speakers == {42: 100}
        await client._voice_hook(None, {"op": 5, "d": {"ssrc": 42, "user_id": "200"}})
        assert client._speakers == {42: 200}
        await client._voice_hook(None, {"op": 13, "d": {"user_id": "200"}})
        assert client._speakers == {}
        await client._voice_hook(None, {"op": 5, "d": {"ssrc": 42, "user_id": "100"}})
        await client._voice_hook(None, {"op": 2, "d": {}})
        assert client._speakers == {}

    asyncio.run(run())


def test_sink_failure_cancellation_and_encryption_recovery() -> None:
    async def run() -> None:
        good = Sink()

        class Broken(Sink):
            async def write(self, frame: AudioFrame) -> None:
                raise RuntimeError("Synthetic consumer failure")

        bad = Broken()
        connection = state()
        connection.dave_protocol_version = 1
        connection.dave_session = SimpleNamespace(ready=False, decrypt=lambda user, media, data: data)
        receiver = Receiver(1, 2, lambda: connection, [bad, good], decode_pcm=False, reorder_seconds=0)
        receiver.bind(42, 100)
        receiver.start()
        receiver.feed_datagram(wire(b"not ready"))
        await asyncio.sleep(0.03)
        assert receiver.health.dropped_frames == 1 and not receiver.health.capture_ready
        connection.dave_session.ready = True
        receiver.feed_datagram(wire(b"valid", seq=2))
        await asyncio.wait_for(good.event.wait(), 1)
        assert receiver.health.sink_errors == 1 and receiver.health.capture_ready
        receiver._task.cancel()
        try:
            await receiver._task
        except asyncio.CancelledError:
            pass
        assert bad.closed == ["stopped"] and good.closed == ["stopped"]

    asyncio.run(run())


def test_cancellation_during_slow_sink_and_decode_failure_isolation() -> None:
    async def run() -> None:
        entered = asyncio.Event()

        class Slow(Sink):
            async def write(self, frame: AudioFrame) -> None:
                entered.set()
                await asyncio.sleep(100)

        slow = Slow()
        receiver = Receiver(1, 2, state, [slow], decode_pcm=False, reorder_seconds=0)
        receiver.bind(42, 100)
        receiver.start()
        receiver.feed_datagram(wire(b"payload"))
        await asyncio.wait_for(entered.wait(), 1)
        await asyncio.wait_for(receiver.close("cancelled"), 1)
        assert slow.closed == ["cancelled"]

        good = Sink()
        receiver = Receiver(1, 2, state, [good], reorder_seconds=0)
        receiver.bind(42, 100)
        receiver.bind(43, 200)
        receiver.start()
        encoded = Encoder().encode(bytes(Encoder.FRAME_SIZE), Encoder.SAMPLES_PER_FRAME)
        receiver.feed_datagram(wire(bytes([255]) * 7))
        receiver.feed_datagram(wire(encoded, ssrc=43))
        await asyncio.wait_for(good.event.wait(), 1)
        assert any(f.member_id == 200 for f in good.frames)
        assert receiver.health.decode_errors >= 1
        await receiver.close()

    asyncio.run(run())
