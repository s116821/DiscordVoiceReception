from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def service_version() -> str:
    try:
        return version("discord-voice-reception")
    except PackageNotFoundError:
        return "0.0.0"
