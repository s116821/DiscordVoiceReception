# Tasks

## 1. Tools and workflow

- [x] 1.1 Consolidate package validation and remove dead/wrapper files; inline routine build/install commands and replace publication/guard integration; verify existing corruption/recovery tests and actual release fixtures, and document retained tools.
- [x] 1.2 Keep quality free of version planning and map standard action publication output to the PyPI handoff; verify workflow gate tests and unchanged recovery trust boundaries.

## 2. Distribution audit

- [x] 2.1 Inspect published GitHub/PyPI assets and licenses, trim source payload, and verify real source-to-wheel rebuild with version/import/typing/license checks; document why wheel/sdist are appropriate library assets.

## 3. Integration

- [x] 3.1 Run required lint/format/types, full offline suite, actual-engine fixtures and strict specs; record evidence.

## Workflow follow-up

- Sync and archive this complete change in the implementation PR and verify consistency.
- Publish/validate the coordinated PR as s116821; record hosted build/install, release and PyPI results in DEG-50.
