# Design

## Context

Both upstream receive PRs #54 and #65 remain open. discord.py 2.7.1 already negotiates DAVE and owns its session; its VoiceConnectionState exposes a websocket hook and socket listener registration. Upstream reader logs include raw packet/key debug data, so copying its entire reader is unsuitable.

## Goals / Non-Goals

Goals: maintained SDK extension with a small isolated import namespace, bounded memory, correct attribution and no sensitive logs.
Non-goals: second SDK, STT, video, legacy optional sinks, perfect packet recovery or functional/live release qualification.

## Decisions

- Implement a focused VoiceClient subclass using the inspected state hook/listener seam. Pin dependencies and document the private extension seam.
- Support the SDK's negotiated AEAD XChaCha20 RTP-size mode only. Use nacl.secret.Aead directly; reject unsupported modes. Preserve complete authenticated RTP header including CSRC/extension header; strip validated extension and padding after decryption.
- Use the current SDK DaveSession for decryption. No forced plaintext passthrough or custom key lifecycle. Known plaintext Opus silence is allowed; encrypted failures are dropped. Read session readiness each frame so epoch transitions recover automatically.
- A thread-safe bounded ingress queue wakes one asyncio consumer. Per-stream bounded jitter buffering orders sequences modulo 16 bits. Bound stream count and emit PCM loss concealment only for missing packets, capped per gap. Drop malformed frames without disrupting other speakers.
- Bind ingress to a speaker generation; reset pending buffers/decoders on SSRC reuse and reconnect. Never attribute unknown audio speculatively.
- Sinks run on the application's event loop. Close/cancel joins tasks and closes each sink once. Health distinguishes capture readiness from recent actual audio and includes drops/backlog/decode errors.
- The implementation is newly authored from inspected wire contracts; retain upstream MIT notice and cite inspected commits and PR authors for receive/DAVE design ancestry.

## Risks / Trade-offs

- Private SDK seams can change → exact pins plus contract tests and explicit compatibility matrix.
- Synthetic tests cannot prove Discord key negotiation/live behavior → release gates stay disabled until DEG-11.
- A slow consumer drops oldest queued audio → counters and readiness expose backpressure; no unbounded buffering.
- No FEC → bounded reordering and PCM PLC provide a documented baseline; no invented recovered Opus frames.
