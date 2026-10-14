## ADDED Requirements

### Requirement: Ordered receiver package publication
Receiver CI SHALL check code once, then build/install packages on Windows/Linux in parallel, then publish on main only after both builds succeed. Saved packages MUST match final semantic-release source/tag and verified checksums before public tagging. Publication MUST NOT rebuild. PRs MUST NOT publish. PyPI SHALL consume only a successful main release artifact and retain trusted-publisher retry.

#### Scenario: Build or artifact mismatch
- **WHEN** a platform fails or a saved package differs from the final release identity
- **THEN** no public tag, GitHub release or PyPI publication is created

#### Scenario: Documentation or pull request
- **WHEN** a documentation-only main run or any PR completes its builds
- **THEN** it produces no publishable release-distributions artifact
