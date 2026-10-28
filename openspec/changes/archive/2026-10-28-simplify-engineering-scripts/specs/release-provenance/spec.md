## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Lean Python library distributions
Library releases SHALL publish a wheel, source distribution and SHA-256 checksums with provenance. The source archive SHALL include library code, build inputs, documentation, examples and required license notices while excluding agent, CI and release orchestration. A wheel rebuilt from that source SHALL preserve version, importable code, typing metadata and license notices. Library releases MUST NOT contain application installers.

#### Scenario: Source-only consumer
- **WHEN** a consumer builds a wheel from the published source distribution without the Git checkout
- **THEN** the resulting wheel retains the release version, library modules, typing marker and required notices

#### Scenario: Published library assets
- **WHEN** both platform validation jobs pass and the release publishes
- **THEN** GitHub and PyPI receive the same wheel/source bytes, with no bot installer assets or development orchestration in the source archive
