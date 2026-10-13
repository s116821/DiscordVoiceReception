# Proposal

## Why

The independent package has a verified engineering baseline but no receiver. DEG-3 and DEG-7 through DEG-10 need a narrow reusable audio API with current DAVE support before DisCuss can integrate it.

## What Changes

- Pin the inspected discord.py 2.7.1 and davey 0.1.7 receive seam.
- Add attributed Opus/PCM frames, asynchronous sinks and bounded receiver lifecycle.
- Parse/decrypt RTP using PyNaCl and the SDK-owned DAVE session; retain SDK negotiation/reconnect machinery.
- Drop malformed, stale, unknown and undecryptable frames; expose readiness, activity and failure counters.
- Include local multi-speaker, transport, epoch, queue and cleanup regressions plus a sample consumer.
- Record MIT upstream attribution and compatibility evidence. Live human/OS acceptance remains DEG-11; no claim of live qualification.

## Capabilities

### New Capabilities

- `audio-reception`: Attributed bounded Opus/PCM audio delivery with safe lifecycle and encryption handling.

### Modified Capabilities

None.

## Impact

Library runtime dependencies and documented Python API. No STT, profanity, bot coordination, storage or custom encryption primitives.
