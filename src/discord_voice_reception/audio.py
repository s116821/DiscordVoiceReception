"""Public attributed frames and asynchronous consumer contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AudioFrame:
    server_id: int
    channel_id: int
    member_id: int
    ssrc: int
    sequence: int
    timestamp: int
    received_at: datetime
    opus: bytes = field(repr=False)
    pcm: bytes | None = field(default=None, repr=False)
    sample_rate: int = 48000
    channels: int = 2
    concealed: bool = False


class AudioSink(Protocol):
    async def write(self, frame: AudioFrame) -> None: ...
    async def close(self, reason: str) -> None: ...
