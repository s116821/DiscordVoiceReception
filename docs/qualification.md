# Disposable-server qualification

Live acceptance is unrun. Default pytest/CI is offline and the live test skips. Do not use a real community server. Create a temporary server under the currently signed-in operator account named `DisCuss-Codex-Temporary` plus a suffix, and a dedicated separately authorized test bot invited **only** to that server. Invite only explicitly consenting test participants. Create two voice channels and coordinate at least two known human IDs; synthetic original speech played by consenting participants is suitable. Never record or save member voice. Do not use user tokens.

Create a separate local JSON outside the checkout:

```json
{
  "temporary_server_confirmed": true,
  "token": "SET-LOCALLY-NEVER-COMMIT",
  "server_id": "123",
  "channel_ids": ["456", "789"],
  "consented_member_ids": ["111", "222"],
  "phase_seconds": 30
}
```

Protect this file: Linux mode0600; Windows private NTFS ACL with only the operator/Administrators/SYSTEM, no broad Users/Everyone/Authenticated Users read. Grant the bot only View Channel/Connect permissions and use guilds+voice_states intents (no privileged message content). Verify bot/server/channel identity before enabling live tests. Tokens are entered locally, never in CI logs, issue comments or task arguments.

```sh
uv run python -m examples.qualify --config /protected/temporary-test.json --temporary-server-confirmed --output /protected/receiver-metrics.json
```

Or explicitly set DISCORD_LIVE_TESTS=1 and DISCORD_TEST_CONFIG to that protected file before `uv run pytest tests/test_live.py`. With either missing the live test skips. CI sets live tests to0. The harness rejects foreign server membership, a server lacking the temporary name prefix, unconsented channel occupants, and unexpected channel frames. It runs bounded initial, second-channel and disconnect/reconnect phases. Move both consenting speakers between channels and speak during each phase. Output contains only member/frame counts, signal presence and capture readiness; PCM is processed transiently and never retained.

Passing these phases demonstrates received nonzero PCM attributed to every allowed speaker, not perfect audio or comprehensive DAVE key rotation. Record separately: overlapping simultaneous speech remains correctly attributed; encoded→PCM quality supports downstream VAD; membership join/leave induces a genuine observed SDK DAVE epoch transition without key dumps; restart/rekey/reconnect resume cleanly; Linux/Windows supported pinned installs pass. Test missing permissions/disconnection safely and turn off/delete temporary test applications/server through the operator after qualification. Never disclose token/key material in failure reports.

DEG-11 stays incomplete until these live/manual checks have objective evidence on both OSes. Trusted PyPI publisher registration/name ownership and explicit RELEASE_READY/PYPI_PUBLISH_READY follow only after qualification. Offline fixtures, this harness and synthetic DAVE contract tests cannot substitute for live MLS proof.
