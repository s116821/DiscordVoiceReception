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
npm run test:release
npm run spec:validate
uv run python scripts/check_openspec.py
uv build
```

PowerShell 7 is required for Git fixture operations so workstation identity profiles remain active. Tests use generated local data and do not connect to Discord. Do not use production servers for tests; later live qualification must explicitly opt in to a disposable server and never store third-party audio.

## Contributions

Use scoped Conventional Commit PR titles, e.g. `feat(receiver): add audio sinks` and `docs(setup): clarify installation`. Prefer squash merge. Each substantive change completes proposal, design, delta specs, implementation/tasks, tests and verification, then archive plus canonical spec synchronization **in the same PR**. Root AGENTS.md is the contributor contract. CI rejects active or incomplete changes. Related Linear issues may share one cohesive change.

## Version and releases

Git tags are the sole version source. Hatchling and uv-dynamic-versioning derive PEP 440 metadata; the runtime version helper reads importlib.metadata and falls back to 0.0.0. There is no editable version constant. The configured semantic-release 25 analyzer owns classification: breaking changes major, feats minor, configured maintenance patch, documentation alone no release.

Every successful main-branch quality run automatically calls the reusable release workflow. Release-worthy development merges publish without readiness switches; docs-only changes do not release. The workflow creates the tag, builds from that tag, validates metadata, attaches SHA-256 checksums and GitHub artifact attestations in the same run. It does not depend on GITHUB_TOKEN tag events launching a separate workflow.

For PyPI, the owner must confirm name availability and register a trusted publisher for owner s116821, repository DiscordVoiceReception, workflow publish.yml, environment pypi. The standalone `publish.yml` workflow automatically uploads the original successful main CI run’s distributions; no readiness variable or PyPI API token is used. After publisher registration, failed uploads can be retried with its CI run ID. The independently versioned distribution name is discord-voice-reception and the import is discord_voice_reception.

## Provenance and license

GPL-3.0-only; preserve the existing LICENSE. Engineering/versioning baseline adapted from s116821/OnVelvetVelma at commit a5964e3fe7d83e7a27d655c324a76eda28cb387c (corrected PR #11). Receive/DAVE design ancestry and retained MIT notices are recorded in NOTICE and licenses/. Dependency licenses remain applicable.
