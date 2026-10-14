## ADDED Requirements

### Requirement: Verified saved-build PyPI recovery
Explicit PyPI retries MAY use a saved Linux build when a successful original main CI run lacks release-distributions. The receipt MUST match that run's source, a published stable GitHub release/tag and all published package/checksum digests. Package metadata MUST match the tag. Unpublished, altered or mismatched artifacts MUST fail before upload. Recovery MUST NOT rebuild or retag; automatic docs/stale runs MUST NOT use this fallback.

#### Scenario: Publication recovered after tag push
- **WHEN** original main CI is successful after a failed-job retry and its GitHub release was recovered from saved packages
- **THEN** explicit PyPI retry verifies and publishes those same bytes

#### Scenario: Source or published bytes differ
- **WHEN** the receipt, tag, version or published hashes differ from the requested original run
- **THEN** PyPI upload does not run
