"""Opt-in disposable-server sample; no audio is stored or printed."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import discord

from discord_voice_reception import AudioFrame, VoiceRecvClient


class CounterSink:
    async def write(self, frame: AudioFrame) -> None:
        # A consumer can process frame.pcm here; keep it ephemeral.
        pass

    async def close(self, reason: str) -> None:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Protected local JSON file")
    parser.add_argument("--temporary-server-confirmed", action="store_true", required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    intents = discord.Intents.none()
    intents.guilds = intents.voice_states = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        server = client.get_guild(int(config["server_id"]))
        channel = server.get_channel(int(config["channel_id"])) if server else None
        if not isinstance(channel, discord.VoiceChannel):
            await client.close()
            return
        if server.voice_client is None:
            voice = await channel.connect(cls=VoiceRecvClient, self_deaf=False)
            voice.listen(CounterSink())

    async def run() -> None:
        async with client:
            await client.start(config["token"])

    asyncio.run(run())


if __name__ == "__main__":
    main()
