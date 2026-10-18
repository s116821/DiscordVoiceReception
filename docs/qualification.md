# Disposable-server qualification

Live acceptance is unrun. Default pytest/CI is offline and the live test skips. Do not use a real community server. Create a temporary server under the currently signed-in operator account named `DisCuss-Codex-Temporary` plus a suffix, and a dedicated separately authorized test bot invited **only** to that server. Create two voice channels. The harness discovers speakers automatically, so no participant IDs are configured. One person can run initial receive/move/reconnect checks; add your buddy to exercise multiple-speaker attribution. Never record or save member voice. Do not use user tokens.

Create a separate local JSON outside the checkout:

```json
{
  "temporary_server_confirmed": true,
  "token": "SET-LOCALLY-NEVER-COMMIT",
  "server_id": "123",
  "channel_ids": ["456", "789"],
  "phase_seconds": 30
}
```

Protect this file: Linux mode0600; Windows private NTFS ACL with only the operator/Administrators/SYSTEM, no broad Users/Everyone/Authenticated Users read. Grant the receiving-only harness View Channel/Connect permissions and use guilds+voice_states intents (no privileged message content). Applications that also transmit audio need Speak; DisCuss replay setup is covered in its [application setup guide](https://github.com/s116821/DisCuss/blob/main/docs/discord-setup.md). Verify bot/server/channel identity before enabling live tests. Tokens are entered locally, never in CI logs, issue comments or task arguments.

```sh
uv run python -m examples.qualify --config /protected/temporary-test.json --temporary-server-confirmed --output /protected/receiver-metrics.json
```

Or explicitly set DISCORD_LIVE_TESTS=1 and DISCORD_TEST_CONFIG to that protected file before `uv run pytest tests/test_live.py`. With either missing the live test skips. CI sets live tests to0. The harness rejects foreign server membership, a server lacking the temporary name prefix, unexpected channel frames. It runs bounded initial, second-channel and disconnect/reconnect phases. Move the test speakers between channels and speak during each phase. Output contains only member/frame counts, signal presence and capture readiness; PCM is processed transiently and never retained.

The result separately reports `multiple_speakers_exercised_in_all_phases`; a solo pass leaves that false. Passing these phases demonstrates received nonzero PCM attributed to dynamically discovered speakers, not perfect audio or comprehensive DAVE key rotation. Record separately: overlapping simultaneous speech remains correctly attributed; encoded→PCM quality supports downstream VAD; membership join/leave induces a genuine observed SDK DAVE epoch transition without key dumps; restart/rekey/reconnect resume cleanly; Linux/Windows supported pinned installs pass. Test missing permissions/disconnection safely and turn off/delete temporary test applications/server through the operator after qualification. Never disclose token/key material in failure reports.

DEG-11 stays incomplete until these live/manual checks have objective evidence on both OSes. Offline fixtures, this harness and synthetic DAVE contract tests cannot substitute for live MLS proof. Development releases run automatically after successful main CI; the registered trusted publisher uploads the exact validated release artifacts to PyPI without readiness variables. See [release and publication operations](../README.md#version-and-releases). Publication does not imply broader live qualification has passed.
