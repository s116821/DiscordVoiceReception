# live-qualification Specification

## Purpose
Provide explicitly authorized disposable-server acceptance without exposing tokens or retaining raw member speech.

## Requirements

### Requirement: Fail-closed opt-in live fixtures
Live fixtures MUST skip by default and require explicit opt-in plus separate local configuration. They SHALL reject foreign-server bots and production-named servers. Configured temporary voice channels SHALL accept new participants automatically without a consent/member-ID allowlist. Audio MUST remain ephemeral and results SHALL contain metadata only. Unrun live scenarios cannot qualify publication.

#### Scenario: Normal CI
- **WHEN** explicit opt-in or a local test configuration is absent
- **THEN** live tests skip without logging in to Discord

#### Scenario: Foreign server membership
- **WHEN** a dedicated test bot is attached to a server outside the disposable allowlist
- **THEN** the harness aborts before connecting voice

#### Scenario: New test participant
- **WHEN** another speaker joins a configured temporary channel
- **THEN** capture accepts their attributed frames without changing configuration

#### Scenario: Solo test
- **WHEN** one speaker provides signal in all bounded phases
- **THEN** phase success can pass and multiple-speaker coverage is reported false
