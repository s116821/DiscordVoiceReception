# Verification

- Read current release provenance, preserve the three ordered jobs, actual analyzer, saved-package checksums and trusted PyPI workflow.
- Ruff, format, ty and all offline pytest checks passed locally on Windows with Python 3.12.
- Workflow regression assertion verifies explicit Python 3.12, no .python-version and no test:release quality command; manual package script retained.
- Specification validated strictly; canonical addition synchronized and the completed lifecycle archived in this PR.
- Hosted PR/main checks and release publication will be recorded in Linear after execution; they are not claimed as pre-merge evidence.
