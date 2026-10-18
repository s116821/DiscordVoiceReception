# Compatibility and dependency review (DEG-3)

Reviewed October 13, 2026. Pinned runtime: CPython 3.12, discord.py 2.7.1 (voice extra), davey 0.1.7, PyNaCl 1.5.0 via uv.lock. PCM uses libopus through discord.py; Windows ships the SDK Opus DLL, Linux requires libopus0. CI covers Windows x64 and Linux x64. Python 3.13+ has not been qualified.

The current maintained SDK owns voice negotiation, DAVE epochs/key transitions and reconnection. DiscordVoiceReception uses its VoiceConnectionState websocket hook and add/remove_socket_listener seam; these are private extension points. Exact pins plus offline contract tests protect against accidental SDK drift. Check compatible versions before upgrades.

A bot identity can connect to one voice channel per Discord server and can connect independently to separate servers. Concurrent channels in one server require separately authorized bot applications; this library does not create accounts or run multiple processes.

## Upstream findings

[discord.py](https://github.com/Rapptz/discord.py) was inspected alongside the installed 2.7.1 package. [Receive extension](https://github.com/imayhaveborkedit/discord-ext-voice-recv) main ac04ea7b0941112e83767cf1c1469b408fa06748 exposes the same state hook/socket seam. [PR #54](https://github.com/imayhaveborkedit/discord-ext-voice-recv/pull/54) and [PR #65](https://github.com/imayhaveborkedit/discord-ext-voice-recv/pull/65) were open when inspected. Their heads are recorded in NOTICE.

The packet layout/receive approach informed this focused implementation. Upstream debug packet/key dumps are excluded. DAVE is called once after transport authentication using the identified sender and current SDK session. No forced passthrough is enabled; undecryptable frames are dropped. Epoch transitions can temporarily drop frames and resume once keys are ready. The SDK governs genuine passthrough negotiation.

Supported transport is aead_xchacha20_poly1305_rtpsize, negotiated by the pinned SDK. Unsupported modes fail closed. Video/RTCP consumers and legacy transport modes are outside this API. Optional PCM supports bounded packet loss concealment; Opus has no fabricated loss frames. Forward error correction is not implemented.

## Qualification evidence and remaining work

Offline tests exercise actual PyNaCl transport round trips and authentication, real Opus encoder/decoder, native davey session readiness, simulated DAVE epoch failure/recovery, packet reordering/wrap, SSRC reuse, reconnect resets, independent sinks, bounded queues and cancellation. Synthetic DAVE fixtures verify the adapter contract; they do not prove live MLS decryption.

**DEG-11 remains incomplete:** controlled disposable-server evidence is still needed for DAVE negotiation/decrypt, genuine rekey, reconnect/move, simultaneous speakers and both target OS installations. The [qualification harness](qualification.md) discovers participants automatically; no per-member ID allowlist is configured. These acceptance limits are documented separately from automatic quality-gated development releases and trusted PyPI publication; no readiness switches gate publication. No production Discord server has been used for qualification testing.
