# Single quality gate and saved package builds

## Why
The operator requests one code-check gate before OS package builds; the receiver currently repeats Ruff/ty/pytest and other checks on both OSes and rebuilds packages after public tagging.

## What Changes
Run checks once on Linux, preview the real semantic-release candidate without remote writes, build/install each OS package once, then verify saved source/version/hash receipts and publish the same distributions. PRs stop after builds. Retain the standalone trusted PyPI publisher and original-artifact retry.

## Capabilities
### Modified Capabilities
- `release-provenance`: ordered stages and exact-artifact publication.

## Impact
CI, packaging helpers, release guard and behavior tests; no receiver behavior or Discord testing changes.
