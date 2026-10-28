# release-provenance Specification

## Purpose
Give operators and downstream consumers verifiable package versions and release provenance after successful quality checks.

## Requirements

### Requirement: One tag-derived version
The package SHALL derive its version solely from Git tags and expose installed metadata with a 0.0.0 fallback when metadata is absent. A release MUST reject wheel or archive identifiers that disagree with its tag.

#### Scenario: Tagged build
- **WHEN** a package is built at tag v1.2.3
- **THEN** its wheel metadata and release artifact identifiers agree on version 1.2.3

### Requirement: Quality-gated release classification
Main-branch release evaluation SHALL run only after all quality checks succeed. Scoped Conventional Commit titles are required. The configured analyzer SHALL produce no release for docs, minor for feat, patch for configured maintenance types and major for breaking changes.

#### Scenario: Documentation-only merge
- **WHEN** the configured analyzer evaluates a docs-only commit
- **THEN** it produces no release

#### Scenario: Failed quality check
- **WHEN** a main-branch quality check fails
- **THEN** release evaluation does not run

### Requirement: Qualified publication with integrity evidence
Every successful main-branch quality run SHALL evaluate releases with the configured semantic-release analyzer, without a readiness variable or manual qualification gate. Published artifacts SHALL have SHA-256 checksums and attestations. Library PyPI publication SHALL automatically consume artifacts from a successful main push using a standalone trusted OIDC workflow, with retry support. Live and reboot qualification evidence SHALL remain documented separately from release automation.

#### Scenario: Development merge
- **WHEN** a release-worthy development change merges to main and quality succeeds
- **THEN** its tag-derived GitHub release and verified assets are published without readiness configuration

#### Scenario: Trusted publisher retry
- **WHEN** the owner registers the PyPI trusted publisher after an upload failed
- **THEN** the original successful CI run's verified distributions can be retried without rebuilding or changing their version

### Requirement: Ordered receiver package publication
Receiver CI SHALL check code once without version planning, then build/install packages on Windows/Linux in parallel, then publish on main after both builds succeed. Builds MAY preview the actual analyzer for a local tag. Standard release integration MUST verify saved source/tag/checksums before public tagging, without rebuilding. PRs MUST NOT publish. PyPI SHALL consume only a successful main release artifact and retain trusted-publisher retry.

#### Scenario: Build or artifact mismatch
- **WHEN** a platform fails or a saved package differs from the final release identity
- **THEN** no public tag, GitHub release or PyPI publication is created

#### Scenario: Documentation or pull request
- **WHEN** a documentation-only main run or any PR completes its builds
- **THEN** it produces no publishable release-distributions artifact

#### Scenario: Quality has no release orchestration
- **WHEN** quality runs on main or a pull request
- **THEN** it executes checks with no release preview or version outputs

### Requirement: Verified saved-build PyPI recovery
Explicit PyPI retries MAY use a saved Linux build when a successful original main CI run lacks release-distributions. The receipt MUST match that run's source, a published stable GitHub release/tag and all published package/checksum digests. Package metadata MUST match the tag. Unpublished, altered or mismatched artifacts MUST fail before upload. Recovery MUST NOT rebuild or retag; automatic docs/stale runs MUST NOT use this fallback.

#### Scenario: Publication recovered after tag push
- **WHEN** original main CI is successful after a failed-job retry and its GitHub release was recovered from saved packages
- **THEN** explicit PyPI retry verifies and publishes those same bytes

#### Scenario: Source or published bytes differ
- **WHEN** the receipt, tag, version or published hashes differ from the requested original run
- **THEN** PyPI upload does not run

### Requirement: Explicit lean quality toolchain
CI SHALL select Python 3.12 explicitly without a repository `.python-version` file. Ordinary code checks MUST NOT run the release analyzer fixture suite. Node manifests SHALL remain available for OpenSpec and semantic-release, and release fixture tests SHALL remain callable on demand. These choices MUST preserve the ordered quality, platform build and main publication gates.

#### Scenario: Ordinary pull request
- **WHEN** a pull request runs quality checks
- **THEN** Python is selected explicitly and release fixture tests are omitted while code and specification checks gate both platform builds

### Requirement: Lean Python library distributions
Library releases SHALL publish a wheel, source distribution and SHA-256 checksums with provenance. The source archive SHALL include library code, build inputs, documentation, examples and required license notices while excluding agent, CI and release orchestration. A wheel rebuilt from that source SHALL preserve version, importable code, typing metadata and license notices. Library releases MUST NOT contain application installers.

#### Scenario: Source-only consumer
- **WHEN** a consumer builds a wheel from the published source distribution without the Git checkout
- **THEN** the resulting wheel retains the release version, library modules, typing marker and required notices

#### Scenario: Published library assets
- **WHEN** both platform validation jobs pass and the release publishes
- **THEN** GitHub and PyPI receive the same wheel/source bytes, with no bot installer assets or development orchestration in the source archive
