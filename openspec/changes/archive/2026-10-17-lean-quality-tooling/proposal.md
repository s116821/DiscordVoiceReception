# Proposal

## Why
The October 17 operator notes request lean code checks without release-tool fixture tests or a repository-level Python selector. Keep the existing ordered build/publication contract intact.

## What Changes
- Remove `.python-version`; select Python 3.12 in CI explicitly.
- Remove `test:release` from ordinary quality gates, retaining the manual fixture command.
- Explain required Node development dependencies and preserve trusted publishing.

## Capabilities
### New Capabilities
None.
### Modified Capabilities
- `release-provenance`: explicit CI toolchain selection and opt-in release-tool fixture checks.

## Impact
CI, scaffold expectations, packaging copy list and contributor documentation; no receiver API/audio changes. Coordinated with DisCuss DEG-46.
