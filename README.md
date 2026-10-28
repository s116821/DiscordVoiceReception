# DiscordVoiceReception

A reusable Python voice-reception library extending discord.py. Speech recognition, profanity rules and leaderboard logic belong in consumers.

**Current status: experimental receiver, awaiting live qualification.** The package provides bounded speaker-attributed Opus/PCM delivery through VoiceRecvClient and asynchronous sinks. Offline fixtures cover transport authentication, decoding, DAVE session readiness, mapping and lifecycle. Live DAVE negotiation/decryption acceptance remains DEG-11; no functional release is qualified.

See [receive API](docs/api.md), [dependency review and compatibility](docs/compatibility.md) and the opt-in [disposable-server example](examples/receive.py). Runtime pins are discord.py 2.7.1 and davey 0.1.7, with PyNaCl 1.5.0 in uv.lock. The library owns no speech recognition, profanity, analytics or persistent audio.

The [guarded qualification harness](docs/qualification.md) runs bounded PCM attribution/move/reconnect checks only with explicit opt-in and a separate disposable test configuration. Normal pytest skips live tests without logging in.

## Development

Install uv and Node.js 24, then run:

```sh
npm ci
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
npm run spec:validate
uv run python scripts/check_openspec.py
uv build
```

PowerShell 7 is required for Git fixture operations so workstation identity profiles remain active. Tests use generated local data and do not connect to Discord. Do not use production servers for tests; later live qualification must explicitly opt in to a disposable server and never store third-party audio.

## Contributions

Use scoped Conventional Commit PR titles, e.g. `feat(receiver): add audio sinks` and `docs(setup): clarify installation`. Prefer squash merge. Each substantive change completes proposal, design, delta specs, implementation/tasks, tests and verification, then archive plus canonical spec synchronization **in the same PR**. Root AGENTS.md is the contributor contract. CI rejects active or incomplete changes. Related Linear issues may share one cohesive change.

## Version and releases

Git tags are the sole version source. Hatchling and uv-dynamic-versioning derive PEP 440 metadata; the runtime version helper reads importlib.metadata and falls back to 0.0.0. There is no editable version constant. The configured semantic-release 25 analyzer owns classification: breaking changes major, feats minor, configured maintenance patch, documentation alone no release.

CI runs code checks once on Linux, then builds and installs saved wheels on Linux/Windows in parallel, then resolves and publishes main releases from those saved distributions. Quality contains no release planning. Main build jobs resolve their local package version using the actual semantic-release engine; final source/version guards run before public tagging. PRs stop after builds, docs-only changes do not release, and publication never rebuilds. Checksums and attestations accompany the exact validated bytes. Build jobs use the packaging-only dependency group rather than repeating code checks.

PyPI uses the registered trusted publisher for owner s116821, repository DiscordVoiceReception, workflow publish.yml, environment pypi. The standalone `publish.yml` workflow automatically uploads the original successful main CI runâ€™s distributions; no readiness variable or PyPI API token is used. Only a successful GitHub release produces its release-distributions artifact, so stale/docs-only runs cannot publish. Failed uploads can be retried with the original CI run ID. An explicit retry may recover its saved Linux build when a post-tag failure omitted that artifact, but only after original CI succeeds and the source/tag/package hashes match an already published GitHub release. Nothing is rebuilt or retagged. The independently versioned distribution name is discord-voice-reception and the import is discord_voice_reception.

## Provenance and license

GPL-3.0-only; preserve the existing LICENSE. Receive/DAVE design ancestry and retained MIT notices are recorded in NOTICE and licenses/. Dependency licenses remain applicable.

Node manifests pin the OpenSpec and actual semantic-release development/release toolchain; Node is not required by the installed receiver runtime. CI explicitly selects Python 3.12 without a repository selector file. `npm run test:release` remains available for deliberate release-tool changes and is omitted from ordinary code checks.

Release assets are the Python wheel, source distribution and SHA256SUMS; both package files are published unchanged to PyPI. The source archive contains code, docs/examples, build inputs and all license notices, excluding agent/CI/release tooling. See [maintenance tooling](scripts/README.md) for the purpose of each retained custom script.
