# Verification

48 offline pytest checks passed with one intentionally skipped live case. Eight recovery cases accept verified original bytes and reject source/tag/hash/draft/prerelease/extra-file changes. Workflow checks preserve successful-main-push/workflow/repository validation and require workflow_dispatch for fallback selection. npm ci, locked uv sync, Ruff/format/ty, actual analyzer and engine preview/guard regressions, and uv build passed; canonical/archive validation accompanies completion.

The validator also passed against actual immutable Linux artifact 11863903826 from main run 38497700801, source b2f4549b5a9967533db4628c27e612f9e02f3431 and recovered GitHub release v1.0.1. Wheel/sdist/checksum digests match the original build receipt and verified GitHub attestation. A Windows newline change in regenerated checksums was caught; the original attested checksum bytes were restored. No package was rebuilt or tag rewritten during recovery. The original failed-job retry completed successfully, satisfying the unchanged CI gate.

Normal automatic main publication and explicit original-run PyPI retry are exercised after merge and recorded in DEG-45 with their hosted run IDs. Those external results do not bypass the source/hash checks. No Discord login or production test occurred; all writes used process-scoped s116821 authentication and loaded PowerShell identity hooks.
