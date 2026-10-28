# Proposal

## Why

The library audit found the same active release-wrapper chain as DisCuss, plus dead bot packaging and development-only source-archive contents. Keep appropriate Python library distributions while simplifying orchestration.

## What Changes

- Replace wrapper files with short workflow commands and the maintained semantic-release action/exec plugin; quality performs no version planning.
- Consolidate package identity/checksum/receipt validation in one helper; retain the standalone dependency-free PyPI recovery verifier.
- Keep wheel, source distribution and checksums as the library's public assets; trim the source archive to code, licenses, build inputs, examples and documentation and verify it rebuilds.
- Move optional release fixtures into tests/tools and document remaining tools.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `release-provenance`: keep version orchestration out of quality, preserve official publication/recovery integration and define appropriate lean library assets.

## Impact

CI/release configuration, packaging inputs, tools and tests. Public Python API, dependency pins, PyPI trusted publisher identity and bot runtime remain unchanged.
