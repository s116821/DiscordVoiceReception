# Receive API

```python
from discord_voice_reception import AudioFrame, VoiceRecvClient


class Consumer:
    async def write(self, frame: AudioFrame) -> None:
        # Process ephemeral frame.pcm, or request decode_pcm=False for frame.opus.
        # Attributes: server_id, channel_id, member_id, ssrc, sequence,
        # timestamp (48 kHz RTP clock), received_at (UTC), sample_rate, channels.
        pass

    async def close(self, reason: str) -> None:
        # Discard buffers and release resources. Called once per listening session.
        pass


voice = await channel.connect(cls=VoiceRecvClient, self_deaf=False)
voice.listen(Consumer(), decode_pcm=True, max_queue=256)
health = voice.receiver_health
await voice.stop_listening()
await voice.disconnect()
```

Sinks run on the application's asyncio loop. Offload blocking work to threads; sink calls time out after a bounded interval and failure in one sink does not stop others. Multiple sink objects can receive the same frame; never reuse the same sink twice in a session. A standalone Receiver is available for local transports/tests; pass an SDK-compatible state getter and call start then await close.

PCM is signed 16-bit little endian, 48000 Hz, stereo. concealed=True identifies PLC frames with empty Opus data. received_at is reception UTC wall time; RTP timestamp is the stream clock, not absolute time. Unknown speakers are discarded until the SDK mapping arrives. Stream state is reset on SSRC rebinding, channel moves and fresh sessions.

Health reports listening, capture_ready, delivered_frames, dropped_frames, decode_errors, sink_errors, backlog and last_frame_at. Capture readiness describes connection/encryption capability and recent decryption failure; last_frame_at records actual frame activity. Silent channels can be ready without recent activity. Connection/encryption drops and sink failures are distinct counters.

Bounded ingress drops oldest audio on overflow. Each mapped speaker has at most 50 pending reorder packets, 128 streams maximum, and a default 40 ms reorder wait. Missing PCM frames use at most five concealment frames per gap; larger discontinuities reset decoder state. No recordings/transcripts are stored. Frame repr excludes raw audio. The adapter suppresses SDK voice websocket wire debug records because those can contain session keys; its own receiver never logs payloads, keys or tokens.
