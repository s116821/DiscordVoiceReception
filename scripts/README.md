# Maintenance tooling

Routine CI belongs in [.github/workflows/ci.yml](../.github/workflows/ci.yml), using existing actions/CLIs and short workflow commands. Keep custom code for package-specific invariants rather than wrappers.

| Tool | Purpose |
| --- | --- |
| `package_release.py` | Verify wheel/source versions, create checksums/build receipts and collect exact tested bytes for publication. |
| `check_pypi_recovery.py` | Dependency-free trust check for explicit recovery: match original successful source, stable published tag, metadata and every published digest before PyPI upload. |
| `check_openspec.py` | Enforce completed archives/canonical consistency beyond schema validation. |
| `git.ps1` | Preserve the workstation's required PowerShell profile/identity hook in Python/Node fixtures. |

Optional actual-engine release fixtures live in [tests/tools](../tests/tools) and run with `npm run test:release`; they are outside the ordinary quality gate.

Quality does no version planning. Main platform builds preview the actual configured analyzer locally because wheels embed their version; PRs use their normal tag-derived development version. Standard artifact actions transfer saved files, the maintained semantic-release action publishes them, and the official exec plugin checks source/tag before public tagging. No package is rebuilt for publication.

This project is a Python library: **wheel + source distribution + SHA256SUMS** are deliberate release assets. The source archive includes library code, build inputs, docs/examples and license notices; agent/CI/release tooling stays in Git. There are no DisCuss installers here. GitHub's automatic source-code links are separate from the Python source distribution.

The registered standalone `publish.yml` / `pypi` trusted publisher and manual original-run recovery retain their existing successful-source and published-byte restrictions. The recovery verifier intentionally works without installing the package or packaging dependencies.
