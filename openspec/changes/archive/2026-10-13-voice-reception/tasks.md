# Tasks

## 1. Dependency and receive contract

- [x] 1.1 Record dependency/seam/license findings and document compatibility plus live acceptance boundaries; verify locked dependency installation.
- [x] 1.2 Implement transport parser and DAVE adapter; verify actual PyNaCl round trips, malformed/header/extension failures and epoch readiness fixtures.

## 2. Attributed delivery and lifecycle

- [x] 2.1 Implement typed frames/sinks, bounded per-speaker delivery and jitter handling; verify simultaneous speakers, SSRC reuse, sequence wrap, queue overflow and PCM tests.
- [x] 2.2 Implement SDK receive client and health/lifecycle ownership; verify socket hook contract, reconnection reset and cancellation/sink-close tests; document sample consumer.
- [x] 2.3 Run lint, format, types, all offline tests and strict delta validation; record verification evidence and retain live qualification as an external gate.

## Workflow follow-up

- Archive, sync canonical specs and validate merge readiness in this PR.
