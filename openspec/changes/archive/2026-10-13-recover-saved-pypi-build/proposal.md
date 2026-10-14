# Retry PyPI from an already published saved build

## Why
A GitHub notes-push failure occurred after tag creation and before GitHub release publication. The original validated packages were used to recover that release. Retrying the failed job makes CI successful but semantic-release skips the existing tag, so no release-distributions artifact is emitted and normal PyPI retry has nothing to publish.

## What Changes
Allow explicit publish.yml original-run retries to fall back to the successful main run's saved Linux build. Require its receipt to match the run source, published GitHub tag and exact asset hashes before trusted PyPI publication. Keep normal automatic publication unchanged.

## Capabilities
### Modified Capabilities
- `release-provenance`: original-artifact retry after recovered publication.

## Impact
PyPI artifact selection and a standard-library integrity validator; no package rebuild, retag or runtime changes.
