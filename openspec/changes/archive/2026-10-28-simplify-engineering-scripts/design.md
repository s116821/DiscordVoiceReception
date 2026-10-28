# Design

## Decisions

- Follow quality -> parallel build/install -> release. Inline the actual analyzer preview from the coordinated DisCuss cleanup only on main builds, using disposable local Git without mirror clones. Keep one tag-derived version.
- Inline uv build/export and isolated wheel install/import/Opus validation. Consolidate distributions, checksums and receipt collection in package_release.py; remove dead application-installer code.
- Publish with cycjimmy/semantic-release-action and the official exec plugin pre-tag guard. Map the action's published flag to release-distributions upload. Preserve publish.yml, its environment/OIDC identity, successful-source checks and explicit saved-build recovery restrictions.
- Keep check_pypi_recovery.py dependency-free: its independent source/tag/published-byte verification is an intentional custom trust boundary, not a routine wrapper.
- Keep wheel+sdist+SHA256SUMS. Unlike DisCuss, the independently consumed PyPI library needs Python distribution files. Explicit Hatch sdist inputs include source, pyproject, uv.lock, README, examples/docs and all licenses; omit agent, CI and release tooling. Verify a wheel rebuilt from the extracted sdist has the right version, modules, typing marker and notices.

## Risks

- Removing release-distributions on docs/stale runs is essential: use the maintained action's new_release_published output, retain recovery tests and original source gating.
- Lean source could miss build/licensing inputs: test real tagged source rebuild and installed imports/codecs on the existing OS matrix. Existing published assets stay intact.
- Two candidates can disagree: reject both receipts against source/tag before official pre-tag verification.
