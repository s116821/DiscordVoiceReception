"""RTP framing and maintained transport/DAVE decryption.

Receive layout informed by discord-ext-voice-recv (MIT), see NOTICE.
No cryptographic primitives or negotiation state are implemented here.
"""

from __future__ import annotations

import struct
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

import davey
from nacl.secret import Aead

SILENCE = bytes.fromhex("f8fffe")
TRANSPORT_MODE = "aead_xchacha20_poly1305_rtpsize"


class DaveSession(Protocol):
    @property
    def ready(self) -> bool: ...
    def decrypt(self, user_id: int, media_type: object, data: bytes) -> bytes: ...


class TransportState(Protocol):
    mode: str
    secret_key: Sequence[int]
    dave_protocol_version: int
    dave_session: DaveSession | None

    def is_connected(self) -> bool: ...


@dataclass(frozen=True, slots=True)
class Packet:
    ssrc: int
    sequence: int
    timestamp: int
    payload: bytes = field(repr=False)


def transport_decode(data: bytes, state: TransportState) -> Packet:
    if state.mode != TRANSPORT_MODE:
        raise ValueError("Unsupported voice transport mode")
    if len(data) < 32 or len(data) > 4096 or data[0] >> 6 != 2 or data[1] & 0x7F != 120:
        raise ValueError("Invalid audio RTP packet")
    count = data[0] & 0x0F
    extended = bool(data[0] & 0x10)
    padded = bool(data[0] & 0x20)
    offset = 12 + count * 4
    extension_length = 0
    if extended:
        if len(data) < offset + 4 + 20:
            raise ValueError("Truncated RTP extension header")
        _, words = struct.unpack_from(">HH", data, offset)
        extension_length = words * 4
        offset += 4
    if len(data) < offset + 20:
        raise ValueError("Truncated authenticated payload")
    sequence, timestamp, ssrc = struct.unpack_from(">HII", data, 2)
    nonce = data[-4:] + bytes(20)
    payload = Aead(bytes(state.secret_key)).decrypt(data[offset:-4], data[:offset], nonce)
    if extension_length > len(payload):
        raise ValueError("Truncated RTP extension values")
    payload = payload[extension_length:]
    if padded:
        if not payload or not 0 < payload[-1] <= len(payload):
            raise ValueError("Invalid RTP padding")
        payload = payload[: -payload[-1]]
    if not payload:
        raise ValueError("Empty audio payload")
    return Packet(ssrc, sequence, timestamp, payload)


def decode_dave(packet: Packet, member_id: int, state: TransportState) -> Packet:
    if packet.payload == SILENCE or state.dave_protocol_version == 0:
        return packet
    session = state.dave_session
    if session is None or not session.ready:
        raise ValueError("Voice encryption session is not ready")
    payload = session.decrypt(member_id, davey.MediaType.audio, packet.payload)
    if not payload:
        raise ValueError("Empty decrypted audio")
    return Packet(packet.ssrc, packet.sequence, packet.timestamp, payload)
