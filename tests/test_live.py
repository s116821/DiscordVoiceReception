from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from examples.qualify import MetricsSink, Settings, permitted_server, qualify

from discord_voice_reception.client import VoiceRecvClient, _SafeVoiceLogs


def settings() -> Settings:
    return Settings("secret-should-not-appear", 1, (10, 20), frozenset({100, 200}))


def test_live_guards_and_metadata_sink() -> None:
    config = settings()
    assert config.token not in repr(config)
    client = SimpleNamespace(guilds=[SimpleNamespace(id=1), SimpleNamespace(id=2)])
    with pytest.raises(ValueError, match="only"):
        permitted_server(client, config)
    client = SimpleNamespace(guilds=[SimpleNamespace(id=1)], get_guild=lambda i: SimpleNamespace(name="Production"))
    with pytest.raises(ValueError, match="guard"):
        permitted_server(client, config)
    sink = MetricsSink(config)
    frame = SimpleNamespace(server_id=2, channel_id=10, member_id=100, pcm=b"private")
    asyncio.run(sink.write(frame))
    assert sink.rejected == 1 and not sink.frames
    frame.server_id = 1
    asyncio.run(sink.write(frame))
    assert sink.frames == {100: 1} and sink.signal == {100}
    assert not hasattr(sink, "pcm")


def test_sdk_wire_debug_cannot_expose_received_session_keys() -> None:
    class Private:
        def __str__(self):
            raise AssertionError("Filter must not format raw wire payload")

    guard = _SafeVoiceLogs()
    for message in (
        "Received voice %s",
        "Sending voice websocket frame: %s.",
        "Sending voice websocket binary frame: opcode=%s size=%d",
    ):
        record = logging.LogRecord("discord.gateway", logging.DEBUG, "sdk", 1, message, (Private(),), None)
        assert not guard.filter(record)
    record = logging.LogRecord("discord.gateway", logging.WARNING, "sdk", 1, "Voice reconnect failed", (), None)
    assert guard.filter(record)
    assert VoiceRecvClient.supported_modes == ("aead_xchacha20_poly1305_rtpsize",)


def test_live_disposable_server() -> None:
    path = os.environ.get("DISCORD_TEST_CONFIG")
    if os.environ.get("DISCORD_LIVE_TESTS") != "1" or not path:
        pytest.skip("Live Discord requires explicit opt-in and a protected disposable test config")
    result = asyncio.run(qualify(Settings.load(Path(path))))
    assert result["pcm_attribution_phases_passed"], "Controlled PCM attribution phases did not qualify"
