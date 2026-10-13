## Purpose

Provide explicitly authorized disposable-server acceptance without exposing tokens or retaining raw member speech.

## ADDED Requirements

### Requirement: Fail-closed opt-in live fixtures
Live fixtures MUST skip by default and require explicit opt-in plus separate local test configuration. They SHALL reject bots attached to foreign servers, production-named servers and unconsented channel occupants. Audio MUST remain ephemeral and results SHALL contain metadata only. Unrun live scenarios cannot qualify publication.

#### Scenario: Normal CI
- **WHEN** explicit opt-in or a local test configuration is absent
- **THEN** live tests skip without logging in to Discord

#### Scenario: Foreign server membership
- **WHEN** a dedicated test bot is attached to a server outside the disposable allowlist
- **THEN** the harness aborts before connecting voice
