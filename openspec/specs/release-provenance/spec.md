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
Receiver CI SHALL check code once, then build/install packages on Windows/Linux in parallel, then publish on main only after both builds succeed. Saved packages MUST match final semantic-release source/tag and verified checksums before public tagging. Publication MUST NOT rebuild. PRs MUST NOT publish. PyPI SHALL consume only a successful main release artifact and retain trusted-publisher retry.

#### Scenario: Build or artifact mismatch
- **WHEN** a platform fails or a saved package differs from the final release identity
- **THEN** no public tag, GitHub release or PyPI publication is created

#### Scenario: Documentation or pull request
- **WHEN** a documentation-only main run or any PR completes its builds
- **THEN** it produces no publishable release-distributions artifact
