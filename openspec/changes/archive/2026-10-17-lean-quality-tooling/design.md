# Design

## Context and goals
Keep checks once, builds in parallel and verified saved-artifact publication. The user specifically requests removing release-tool fixture tests from code checks in both repos.

## Decisions
Use top-level `UV_PYTHON: "3.12"` for all CI jobs and remove `.python-version`, including its scaffold/copy references. Keep npm manifests and manual analyzer tests because they own real release classification. Leave publish.yml and its registered PyPI identity unchanged.

## Risks and verification
A missing selector could silently change Python; workflow assertions verify explicit selection. Run Ruff, ty, pytest and canonical/archive checks. A tooling maintenance merge should release via the unchanged analyzer.
