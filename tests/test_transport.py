from __future__ import annotations

import struct
from types import SimpleNamespace

import pytest
from nacl.exceptions import CryptoError
from nacl.secret import Aead

from discord_voice_reception.transport import SILENCE, TRANSPORT_MODE, decode_dave, transport_decode


def state() -> SimpleNamespace:
    return SimpleNamespace(
        mode=TRANSPORT_MODE,
        secret_key=bytes(range(32)),
        dave_protocol_version=0,
        dave_session=None,
        is_connected=lambda: True,
    )


def wire(
    payload: bytes,
    *,
    ssrc: int = 42,
    seq: int = 1,
    extension: bool = False,
    csrc: bool = False,
    padding: bool = False,
    key: bytes = bytes(range(32)),
) -> bytes:
    flags = 0x80 | (0x10 if extension else 0) | (1 if csrc else 0) | (0x20 if padding else 0)
    header = struct.pack(">BBHII", flags, 120, seq, seq * 960, ssrc)
    if csrc:
        header += struct.pack(">I", 999)
    if extension:
        header += struct.pack(">HH", 0xBEDE, 1)
        payload = bytes(4) + payload
    if padding:
        payload += bytes([2, 2])
    nonce = (seq + 1).to_bytes(4, "big") + bytes(20)
    return header + Aead(key).encrypt(payload, header, nonce).ciphertext + nonce[:4]


@pytest.mark.parametrize(
    "extension,csrc,padding", [(False, False, False), (True, False, False), (True, True, True), (False, True, True)]
)
def test_authenticated_rtp_round_trip(extension: bool, csrc: bool, padding: bool) -> None:
    packet = transport_decode(wire(b"encoded", extension=extension, csrc=csrc, padding=padding), state())
    assert (packet.ssrc, packet.sequence, packet.timestamp, packet.payload) == (42, 1, 960, b"encoded")


def test_transport_rejects_tampering_and_malformed_data() -> None:
    data = bytearray(wire(b"encoded"))
    data[3] ^= 1
    with pytest.raises(CryptoError):
        transport_decode(bytes(data), state())
    for data in (b"", bytes(11), bytes(32), wire(b"encoded")[:-17]):
        with pytest.raises((ValueError, CryptoError)):
            transport_decode(data, state())
    invalid = state()
    invalid.mode = "unsupported"
    with pytest.raises(ValueError, match="Unsupported"):
        transport_decode(wire(b"encoded"), invalid)


def test_encryption_readiness_failure_and_recovery() -> None:
    calls = []

    def decrypt(member: int, media: object, data: bytes) -> bytes:
        calls.append(member)
        if data != b"ciphertext":
            raise ValueError("Synthetic failed epoch")
        return b"opus"

    connection = state()
    connection.dave_protocol_version = 1
    connection.dave_session = SimpleNamespace(ready=False, decrypt=decrypt)
    packet = transport_decode(wire(b"ciphertext"), connection)
    with pytest.raises(ValueError, match="not ready"):
        decode_dave(packet, 123, connection)
    connection.dave_session.ready = True
    assert decode_dave(packet, 123, connection).payload == b"opus"
    assert calls == [123]
    with pytest.raises(ValueError):
        decode_dave(transport_decode(wire(b"bad epoch"), connection), 123, connection)
    assert decode_dave(packet, 123, connection).payload == b"opus"
    assert decode_dave(transport_decode(wire(SILENCE), connection), 123, connection).payload == SILENCE
    assert len(calls) == 3  # plaintext silence never enters DAVE decrypt


def test_sdk_native_dave_session_is_unready_without_negotiation() -> None:
    import davey

    connection = state()
    connection.dave_protocol_version = 1
    connection.dave_session = davey.DaveSession(1, 123, 456)
    assert not connection.dave_session.ready
    with pytest.raises(ValueError, match="not ready"):
        decode_dave(transport_decode(wire(b"ciphertext"), connection), 123, connection)
