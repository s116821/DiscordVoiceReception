"""discord.py adapter; private SDK terminology stays inside this module."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, cast

import discord
from discord.voice_state import VoiceConnectionState

from .audio import AudioSink
from .receiver import Health, Receiver
from .transport import TransportState


class _SafeVoiceLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Upstream DEBUG wire logs can contain a SESSION_DESCRIPTION transport key.
        message = str(record.msg).lower()
        return "voice websocket frame" not in message and "voice websocket binary frame" not in message


class VoiceRecvClient(discord.VoiceClient):
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable) -> None:
        self._receiver: Receiver | None = None
        self._speakers: dict[int, int] = {}
        self._cleanup_tasks: set[asyncio.Task[None]] = set()
        super().__init__(client, channel)
        logger = logging.getLogger("discord.gateway")
        if not any(isinstance(f, _SafeVoiceLogs) for f in logger.filters):
            logger.addFilter(_SafeVoiceLogs())

    def create_connection_state(self) -> VoiceConnectionState:
        return VoiceConnectionState(self, hook=self._voice_hook)

    async def _voice_hook(self, websocket: Any, message: dict[str, Any]) -> None:
        op = message.get("op")
        data = message.get("d") or {}
        if op == 2:  # READY: a fresh transport session cannot reuse old mappings.
            self._reset_receiver()
        elif op in (5, 12):  # SPEAKING or CLIENT_CONNECT with audio SSRC.
            ssrc = data.get("ssrc") if op == 5 else data.get("audio_ssrc")
            member = data.get("user_id")
            if ssrc is not None and member is not None:
                source, member_id = int(ssrc), int(member)
                for old, user in list(self._speakers.items()):
                    if user == member_id or old == source:
                        self._speakers.pop(old)
                if len(self._speakers) < 128:
                    self._speakers[source] = member_id
                    if self._receiver is not None:
                        self._receiver.bind(source, member_id)
        elif op == 13:
            member_id = int(data["user_id"])
            self._speakers = {s: m for s, m in self._speakers.items() if m != member_id}
            if self._receiver is not None:
                self._receiver.unbind(member_id)

    def _reset_receiver(self) -> None:
        self._speakers.clear()
        if self._receiver is not None:
            self._receiver.reset(self.channel.id)

    async def on_voice_state_update(self, data: Any) -> None:
        old = self.channel.id
        await super().on_voice_state_update(data)
        if data.get("channel_id") is None or int(data["channel_id"]) != old:
            self._reset_receiver()

    async def on_voice_server_update(self, data: Any) -> None:
        self._reset_receiver()
        await super().on_voice_server_update(data)

    async def move_to(self, channel: discord.abc.Snowflake | None, *, timeout: float | None = 30.0) -> None:
        self._reset_receiver()
        await super().move_to(channel, timeout=timeout)
        self._reset_receiver()

    def listen(self, *sinks: AudioSink, decode_pcm: bool = True, max_queue: int = 256) -> None:
        if not self.is_connected():
            raise discord.ClientException("Not connected to voice")
        if self._receiver is not None:
            raise discord.ClientException("Already listening; stop the previous session first")
        receiver = Receiver(
            self.guild.id,
            self.channel.id,
            lambda: cast(TransportState, self._connection),
            sinks,
            decode_pcm=decode_pcm,
            max_queue=max_queue,
        )
        for ssrc, member in self._speakers.items():
            receiver.bind(ssrc, member)
        receiver.start()
        self._receiver = receiver
        self._connection.add_socket_listener(receiver.feed_datagram)

    @property
    def receiver_health(self) -> Health | None:
        return self._receiver.health if self._receiver is not None else None

    def is_listening(self) -> bool:
        return self._receiver is not None and self._receiver.health.listening

    async def stop_listening(self, reason: str = "stopped") -> None:
        receiver, self._receiver = self._receiver, None
        if receiver is not None:
            self._connection.remove_socket_listener(receiver.feed_datagram)
            await receiver.close(reason)

    def stop(self) -> None:
        # The SDK calls this synchronous method during connection cleanup.
        super().stop()
        if self._receiver is not None:
            receiver, self._receiver = self._receiver, None
            self._connection.remove_socket_listener(receiver.feed_datagram)
            receiver.request_stop("connection stopped")
            task = asyncio.get_running_loop().create_task(receiver.close("connection stopped"))
            self._cleanup_tasks.add(task)
            task.add_done_callback(self._cleanup_tasks.discard)

    async def disconnect(self, *, force: bool = False) -> None:
        await self.stop_listening("disconnected")
        await super().disconnect(force=force)
        if self._cleanup_tasks:
            await asyncio.gather(*tuple(self._cleanup_tasks))

    def cleanup(self) -> None:
        self.stop()
        self._speakers.clear()
        super().cleanup()
