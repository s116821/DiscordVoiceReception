"""Bounded opt-in acceptance; never stores audio or prints credentials."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import discord

from discord_voice_reception import AudioFrame, VoiceRecvClient


@dataclass(frozen=True)
class Settings:
    token: str = field(repr=False)
    server_id: int
    channels: tuple[int, int]
    phase_seconds: int = 30

    @classmethod
    def load(cls, path: Path) -> Settings:
        if os.name != "nt" and path.stat().st_mode & 0o077:
            raise ValueError("Test config requires private file permissions")
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            if data["temporary_server_confirmed"] is not True:
                raise ValueError
            channels = tuple(int(c) for c in data["channel_ids"])
            seconds = int(data.get("phase_seconds", 30))
            if len(channels) != 2 or channels[0] == channels[1] or not 10 <= seconds <= 120:
                raise ValueError
            return cls(str(data["token"]), int(data["server_id"]), (channels[0], channels[1]), seconds)
        except (ValueError, KeyError, TypeError):
            raise ValueError("Invalid disposable test configuration") from None


def permitted_server(client: discord.Client, settings: Settings):
    if {s.id for s in client.guilds} != {settings.server_id}:
        raise ValueError("Dedicated test bot must belong only to the disposable server")
    server = client.get_guild(settings.server_id)
    if server is None or not server.name.startswith("DisCuss-Codex-Temporary"):
        raise ValueError("Disposable server name guard rejected this server")
    for channel_id in settings.channels:
        channel = server.get_channel(channel_id)
        if not isinstance(channel, discord.VoiceChannel):
            raise ValueError("Test voice channel is unavailable")
    return server


class MetricsSink:
    def __init__(self, settings: Settings, channel_id: int | None = None) -> None:
        self.settings = settings
        self.channel_id = channel_id or settings.channels[0]
        self.frames: dict[int, int] = {}
        self.signal: set[int] = set()
        self.rejected = 0

    async def write(self, frame: AudioFrame) -> None:
        if frame.server_id != self.settings.server_id or frame.channel_id != self.channel_id:
            self.rejected += 1
            return
        self.frames[frame.member_id] = self.frames.get(frame.member_id, 0) + 1
        if frame.pcm and any(frame.pcm):
            self.signal.add(frame.member_id)

    async def close(self, reason: str) -> None:
        pass


def coverage(phases: list[dict]) -> tuple[bool, bool]:
    passed = len(phases) == 3 and all(p["capture_ready"] and p["members_with_signal"] for p in phases)
    multiple = passed and all(len(p["members_with_signal"]) >= 2 for p in phases)
    return bool(passed), bool(multiple)


async def qualify(settings: Settings) -> dict:
    intents = discord.Intents.none()
    intents.guilds = intents.voice_states = True
    client = discord.Client(intents=intents)
    ready = asyncio.Event()
    abort = asyncio.Event()

    @client.event
    async def on_ready() -> None:
        ready.set()

    @client.event
    async def on_voice_state_update(member, before, after) -> None:
        if client.user is not None and member.id == client.user.id:
            if after.channel is not None and after.channel.id not in settings.channels:
                abort.set()
                voice = member.guild.voice_client
                if voice:
                    await voice.disconnect(force=True)

    task = asyncio.create_task(client.start(settings.token))
    phases = []
    try:
        await asyncio.wait_for(ready.wait(), 30)
        for name, channel_id in zip(
            ("initial", "move", "reconnect"), (*settings.channels, settings.channels[1]), strict=True
        ):
            if abort.is_set():
                raise ValueError("Test bot moved outside configured channels")
            server = permitted_server(client, settings)
            channel = server.get_channel(channel_id)
            if name == "move" and isinstance(server.voice_client, VoiceRecvClient):
                voice = server.voice_client
                await voice.stop_listening("phase transition")
                await voice.move_to(channel, timeout=20)
            else:
                if server.voice_client:
                    await server.voice_client.disconnect(force=True)
                voice = await channel.connect(cls=VoiceRecvClient, self_deaf=False, timeout=20)
            sink = MetricsSink(settings, channel_id)
            voice.listen(sink, decode_pcm=True)
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(abort.wait(), settings.phase_seconds)
            if abort.is_set():
                raise ValueError("Test bot moved outside configured channels")
            health = voice.receiver_health
            phases.append(
                {
                    "phase": name,
                    "channel_id": channel_id,
                    "frames": sink.frames,
                    "members_with_signal": sorted(sink.signal),
                    "rejected_frames": sink.rejected,
                    "capture_ready": bool(health and health.capture_ready),
                }
            )
            if name == "reconnect":
                await voice.disconnect(force=True)
        passed, multiple = coverage(phases)
        return {
            "pcm_attribution_phases_passed": passed,
            "multiple_speakers_exercised_in_all_phases": multiple,
            "phases": phases,
            "manual_gate": "Confirm overlapping speech, audible/PCM quality, epoch/rekey and OS reboot separately.",
        }
    finally:
        for voice in list(client.voice_clients):
            with contextlib.suppress(Exception):
                await voice.disconnect(force=True)
        await client.close()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await task


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--temporary-server-confirmed", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = asyncio.run(qualify(Settings.load(args.config)))
    except Exception:
        raise SystemExit(
            "Live qualification failed; check local setup and speaker signal. No credentials logged."
        ) from None
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    raise SystemExit(0 if result["pcm_attribution_phases_passed"] else 2)


if __name__ == "__main__":
    main()
