# Proposal
## Why
Live DAVE remains unqualified. A reproducible opt-in harness must fail closed against production servers and preserve only objective metadata so external test setup can be supplied safely.
## What Changes
- Dedicated disposable-server-only PCM attribution/reconnect/move harness with explicit consented member allowlist, bounded phase duration and metadata output.
- Pytest live test skips unless both explicit opt-in and a protected local config path are supplied; normal CI never logs in.
- Operator instructions and manual rekey/overlap acceptance checklist, clearly separate from offline tests.
## Capabilities
### New Capabilities
- `live-qualification`: guarded metadata-only disposable-server acceptance.
### Modified Capabilities
None.
## Impact
DEG-5 fixture and DEG-11 acceptance tooling only. No live run without supplied test-bot configuration; no voice recording or application dependencies.
