# Design

Use quality → parallel Windows/Linux build → main-only release. Quality owns all code/analyzer/spec tests. An isolated local mirror and checkout run the actual semantic-release engine in dry-run mode using the unchanged analyzer, without requiring remote write permission. Local candidate tags give versioned main builds their Git-derived metadata; PR/doc-only builds use normal development versions.

Each build produces one wheel/sdist pair, verifies versions and installs its wheel with native dependencies in an isolated environment. Runtime imports/version and native Opus construction validate the saved wheel. A packaging-only dependency group avoids installing test/lint tooling in build jobs. Source/tag/platform/hash receipts and distributions become immutable workflow artifacts. Final collection verifies both platforms and selects Linux's canonical distributions without rebuilding. A verifyRelease plugin rejects candidate/source changes before public tagging; GitHub publication uploads saved files with checksums/attestations.

Only a successful semantic-release result produces the release-distributions artifact consumed by the existing publish.yml trusted publisher. Stale/docs-only runs cannot feed PyPI. Keep the registered workflow/environment identity and original-artifact retry unchanged; main concurrency serializes publication.
