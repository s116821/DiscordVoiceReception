"""Bounded single-loop audio dispatch fed from the SDK socket reader thread."""

from __future__ import annotations

import asyncio
import contextlib
import threading
import time
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from discord.opus import Decoder, OpusError

from .audio import AudioFrame, AudioSink
from .transport import TRANSPORT_MODE, Packet, TransportState, decode_dave, transport_decode


@dataclass(frozen=True, slots=True)
class Health:
    listening: bool
    capture_ready: bool
    delivered_frames: int
    dropped_frames: int
    decode_errors: int
    sink_errors: int
    backlog: int
    last_frame_at: datetime | None


@dataclass(slots=True)
class Stream:
    member_id: int
    started: bool = False
    expected: int | None = None
    timestamp: int = 0
    pending: dict[int, tuple[Packet, datetime, float]] = field(default_factory=dict)
    decoder: Decoder | None = None


@dataclass(frozen=True, slots=True)
class Ingress:
    data: bytes = field(repr=False)
    binding: tuple[int, int] | None
    generation: int
    received_at: datetime


class Receiver:
    def __init__(
        self,
        server_id: int,
        channel_id: int,
        state: Callable[[], TransportState],
        sinks: Sequence[AudioSink],
        *,
        decode_pcm: bool = True,
        max_queue: int = 256,
        max_streams: int = 128,
        reorder_seconds: float = 0.04,
        sink_timeout: float = 1.0,
    ) -> None:
        if not sinks or min(max_queue, max_streams) < 1 or not 0 <= reorder_seconds <= 1 or sink_timeout <= 0:
            raise ValueError("Invalid receiver limits or sinks")
        if len({id(s) for s in sinks}) != len(sinks):
            raise ValueError("Duplicate sink")
        self.server_id, self.channel_id = server_id, channel_id
        self.state = state
        self.sinks = tuple(sinks)
        self.decode_pcm = decode_pcm
        self.max_queue, self.max_streams = max_queue, max_streams
        self.reorder_seconds, self.sink_timeout = reorder_seconds, sink_timeout
        self._lock = threading.Lock()
        self._queue: deque[Ingress] = deque()
        self._bindings: dict[int, tuple[int, int]] = {}
        self._streams: dict[int, Stream] = {}
        self._generation = 0
        self._binding_serial = 0
        self._wake_pending = False
        self._event = asyncio.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task[None] | None = None
        self._closed = False
        self._sinks_closed = False
        self._reason = "stopped"
        self.delivered_frames = self.dropped_frames = self.decode_errors = self.sink_errors = 0
        self.last_frame_at: datetime | None = None
        self._failed_capture = False

    def bind(self, ssrc: int, member_id: int) -> None:
        if ssrc < 0 or member_id <= 0:
            raise ValueError("Invalid speaker identity")
        with self._lock:
            if self._bindings.get(ssrc, (None,))[0] == member_id:
                return
            if len(self._bindings) >= self.max_streams and ssrc not in self._bindings:
                self.dropped_frames += 1
                return
            for old, binding in list(self._bindings.items()):
                if binding[0] == member_id:
                    self._bindings.pop(old)
                    self._streams.pop(old, None)
            self._binding_serial += 1
            self._bindings[ssrc] = (member_id, self._binding_serial)
            self._streams.pop(ssrc, None)

    def unbind(self, member_id: int) -> None:
        with self._lock:
            for ssrc, binding in list(self._bindings.items()):
                if binding[0] == member_id:
                    self._bindings.pop(ssrc)
                    self._streams.pop(ssrc, None)

    def reset(self, channel_id: int | None = None) -> None:
        with self._lock:
            self._generation += 1
            self._queue.clear()
            self._bindings.clear()
            self._streams.clear()
            if channel_id is not None:
                self.channel_id = channel_id
        self._failed_capture = False

    def start(self) -> None:
        if self._task is not None or self._closed:
            raise RuntimeError("Receiver already started or closed")
        self._loop = asyncio.get_running_loop()
        if self.decode_pcm:
            Decoder()  # Fail startup intentionally if the native codec is unavailable.
        self._task = self._loop.create_task(self._run(), name="voice-reception")

    def feed_datagram(self, data: bytes) -> None:
        # Called by the SDK reader thread; only one wake callback can be pending.
        if len(data) < 12 or len(data) > 4096 or data[1] & 0x7F != 120:
            return
        ssrc = int.from_bytes(data[8:12], "big")
        with self._lock:
            if self._closed or self._loop is None:
                return
            binding = self._bindings.get(ssrc)
            if binding is None:
                self.dropped_frames += 1
                return
            if len(self._queue) >= self.max_queue:
                self._queue.popleft()
                self.dropped_frames += 1
            self._queue.append(Ingress(bytes(data), binding, self._generation, datetime.now(UTC)))
            if not self._wake_pending:
                self._wake_pending = True
                self._loop.call_soon_threadsafe(self._event.set)

    @property
    def health(self) -> Health:
        state = self.state()
        session = state.dave_session
        ready = (
            state.mode == TRANSPORT_MODE
            and state.is_connected()
            and (state.dave_protocol_version == 0 or session is not None and session.ready)
        )
        listening = self._task is not None and not self._task.done() and not self._closed
        return Health(
            listening,
            listening and ready and not self._failed_capture,
            self.delivered_frames,
            self.dropped_frames,
            self.decode_errors,
            self.sink_errors,
            len(self._queue),
            self.last_frame_at,
        )

    def request_stop(self, reason: str = "stopped") -> None:
        with self._lock:
            self._closed = True
            self._reason = reason
            self._queue.clear()
        if self._task is not None and not self._task.done():
            self._task.cancel()

    async def close(self, reason: str = "stopped") -> None:
        self.request_stop(reason)
        if self._task is not None:
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        await self._close_sinks()

    async def _run(self) -> None:
        try:
            while True:
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(self._event.wait(), 0.02)
                self._event.clear()
                with self._lock:
                    items = list(self._queue)
                    self._queue.clear()
                    self._wake_pending = False
                for item in items:
                    self._ingest(item)
                for ssrc, stream in list(self._streams.items()):
                    await self._flush(ssrc, stream)
        finally:
            self._closed = True
            self._queue.clear()
            self._streams.clear()
            await self._close_sinks()

    async def _close_sinks(self) -> None:
        if self._sinks_closed:
            return
        self._sinks_closed = True
        for sink in self.sinks:
            try:
                await asyncio.wait_for(sink.close(self._reason), self.sink_timeout)
            except (Exception, asyncio.CancelledError):
                self.sink_errors += 1

    def _ingest(self, item: Ingress) -> None:
        ssrc = int.from_bytes(item.data[8:12], "big")
        if item.generation != self._generation or item.binding != self._bindings.get(ssrc):
            self.dropped_frames += 1
            return
        state = self.state()
        if not state.is_connected() or item.binding is None:
            self.dropped_frames += 1
            return
        try:
            packet = transport_decode(item.data, state)
        except Exception:
            self._failed_capture = True
            self.dropped_frames += 1
            return
        stream = self._streams.setdefault(ssrc, Stream(item.binding[0]))
        if stream.expected is None:
            stream.expected = packet.sequence
        distance = (packet.sequence - stream.expected) % 65536
        if distance >= 32768 and not stream.started and (stream.expected - packet.sequence) % 65536 <= 50:
            stream.expected = packet.sequence
            distance = 0
        if distance >= 32768 or packet.sequence in stream.pending:
            self.dropped_frames += 1
            return
        # Large jumps reset state rather than generating unbounded concealment.
        if distance > 50:
            stream.pending.clear()
            stream.decoder = None
            stream.expected = packet.sequence
        if len(stream.pending) >= 50:
            self.dropped_frames += 1
            return
        stream.pending[packet.sequence] = (packet, item.received_at, time.monotonic())

    async def _flush(self, ssrc: int, stream: Stream) -> None:
        while stream.pending and stream.expected is not None:
            if self._streams.get(ssrc) is not stream:
                return
            if not self.state().is_connected():
                self.dropped_frames += len(stream.pending)
                stream.pending.clear()
                return
            expected = stream.expected
            seq = min(stream.pending, key=lambda n: (n - expected) % 65536)
            packet, received, queued = stream.pending[seq]
            if time.monotonic() - queued < self.reorder_seconds:
                return
            missing = (seq - stream.expected) % 65536
            if missing and self.decode_pcm and stream.decoder is not None:
                for i in range(min(missing, 5)):
                    pcm = self._pcm(stream, None)
                    await self._deliver(
                        AudioFrame(
                            self.server_id,
                            self.channel_id,
                            stream.member_id,
                            ssrc,
                            (stream.expected + i) % 65536,
                            (stream.timestamp + 960 * (i + 1)) % 2**32,
                            received,
                            b"",
                            pcm,
                            concealed=True,
                        )
                    )
            stream.pending.pop(seq)
            stream.started = True
            stream.expected = (seq + 1) % 65536
            stream.timestamp = packet.timestamp
            try:
                packet = decode_dave(packet, stream.member_id, self.state())
            except BaseException as error:
                if isinstance(error, (KeyboardInterrupt, SystemExit, asyncio.CancelledError)):
                    raise
                self._failed_capture = True
                self.dropped_frames += 1
                continue
            self._failed_capture = False
            pcm = self._pcm(stream, packet.payload) if self.decode_pcm else None
            if self.decode_pcm and pcm is None:
                self.dropped_frames += 1
                continue
            await self._deliver(
                AudioFrame(
                    self.server_id,
                    self.channel_id,
                    stream.member_id,
                    ssrc,
                    seq,
                    packet.timestamp,
                    received,
                    packet.payload,
                    pcm,
                )
            )

    def _pcm(self, stream: Stream, payload: bytes | None) -> bytes | None:
        try:
            if stream.decoder is None:
                stream.decoder = Decoder()
            return stream.decoder.decode(payload, fec=False)
        except (OpusError, RuntimeError):
            self.decode_errors += 1
            return None

    async def _deliver(self, frame: AudioFrame) -> None:
        # Isolate sink failure and bound the time spent on each consumer.
        delivered = False
        for sink in self.sinks:
            try:
                await asyncio.wait_for(sink.write(frame), self.sink_timeout)
                delivered = True
            except Exception:
                self.sink_errors += 1
        if delivered:
            self.delivered_frames += 1
            self.last_frame_at = frame.received_at
        else:
            self._failed_capture = True
