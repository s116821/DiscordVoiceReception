# Verification

- Audited v1.0.3: wheel/source SHA-256 values match the actual PyPI version API, and the wheel contains the expected modules, py.typed and GPL/NOTICE/upstream-license records.
- Full offline suite: 50 passed, one live test intentionally skipped. Updated package/source/recovery tests: 22 passed. Real tagged source archive rebuilt a version-matching wheel; an isolated Python process imported that rebuilt wheel, and tests verified typing and license notices plus exclusion of development-only content.
- Ruff lint/format, ty, strict change and all four canonical specs pass. Actual-engine release fixtures pass for docs/fix/feat/breaking and official pre-tag guard rejection; source/tags remain unchanged by previews.
- Six orchestration files removed, two optional fixture tools moved to tests/tools, package verification consolidated and dead bot packaging removed. Five top-level code files remain; scripts/README.md explains each one.
- Existing publish.yml/OIDC identity and explicit source/tag/published-byte recovery rules remain unchanged. Standard action publication flag gates release-distributions. No runtime API/dependency-pin change or live Discord test.
- Hosted Windows/Linux package/install validation and final GitHub/PyPI publication are tracked in DEG-50 and the implementation PR.
