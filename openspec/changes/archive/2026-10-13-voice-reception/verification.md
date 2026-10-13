# Verification — voice reception

Windows x64 local: Ruff, format and ty pass; 28 pytest checks pass, 13 actual semantic-release analyzer cases pass, uv wheel/sdist build and strict delta validation pass.

Requirement evidence:
- Attributed frames: simultaneous members/consumers, unmapped source dropping, SSRC reassignment, reconnect reset and channel metadata tests.
- Maintained encryption: real PyNaCl authenticated round trips including CSRC/extensions/padding, tamper rejection, native davey unready-session check and synthetic failure/readiness recovery.
- Bounded independent streams: queue overflow, reorder/duplicate/16-bit wrap, real Opus/PCM and bounded concealment, malformed decoder isolation.
- Lifecycle/health: close-before-task-start, double close, cancellation during a sink, sink exception isolation, SDK hook/mapping contracts and capture/activity diagnostics.
- Packaging includes GPL license, NOTICE and retained upstream MIT notice; no upstream logging or optional modules are vendored.

Remaining external evidence: Windows/Linux feature CI, actual disposable-server DAVE negotiation/decryption, rekey, human speakers and OS installation qualification in DEG-11. Native cryptographic primitives are exercised for transport, but synthetic DAVE contract fixtures are not represented as live MLS acceptance. RELEASE_READY remains disabled.
