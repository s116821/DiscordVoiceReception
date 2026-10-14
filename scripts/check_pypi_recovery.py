"""Verify an original successful build against its already published GitHub release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tarfile
import zipfile
from collections.abc import Callable
from email.parser import Parser
from pathlib import Path
from typing import Any


def gh_api(endpoint: str) -> Any:
    return json.loads(subprocess.check_output(["gh", "api", endpoint], text=True))


def version(path: Path) -> str | None:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
            if len(names) != 1:
                raise ValueError("Expected one wheel metadata record")
            text = archive.read(names[0]).decode()
    else:
        with tarfile.open(path) as archive:
            names = [m for m in archive.getmembers() if m.name.count("/") == 1 and m.name.endswith("/PKG-INFO")]
            if len(names) != 1:
                raise ValueError("Expected one source metadata record")
            stream = archive.extractfile(names[0])
            if stream is None:
                raise ValueError("Missing source metadata")
            text = stream.read().decode()
    return Parser().parsestr(text).get("Version")


def verify(directory: Path, source: str, repository: str, api: Callable[[str], Any] = gh_api) -> None:
    receipt = json.loads((directory / "build-receipt.json").read_text(encoding="utf-8"))
    tag = receipt["tag"]
    if receipt["source_commit"] != source or receipt["platform"] != "linux-x64" or not tag.startswith("v"):
        raise ValueError("Build receipt does not match original main source/platform")
    wheels, sources = list(directory.glob("*.whl")), list(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError("Expected one wheel and one sdist")
    expected = {wheels[0].name, sources[0].name, "SHA256SUMS"}
    if set(receipt["files"]) != expected or {p.name for p in directory.iterdir()} != expected | {"build-receipt.json"}:
        raise ValueError("Unexpected recovery artifact contents")
    for path in wheels + sources:
        if version(path) != tag[1:]:
            raise ValueError("Package metadata differs from original release tag")
    release = api(f"repos/{repository}/releases/tags/{tag}")
    ref = api(f"repos/{repository}/git/ref/tags/{tag}")
    if release["draft"] or release["prerelease"] or release["tag_name"] != tag:
        raise ValueError("Recovery requires a published stable release")
    if ref["object"].get("type") != "commit" or ref["object"].get("sha") != source:
        raise ValueError("Published tag does not match original main source")
    published = {a["name"]: a.get("digest") for a in release["assets"]}
    for name, digest in receipt["files"].items():
        if (
            hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest
            or published.get(name) != f"sha256:{digest}"
        ):
            raise ValueError("Saved bytes differ from original published release")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "s116821/DiscordVoiceReception"))
    args = parser.parse_args()
    verify(args.directory, args.source, args.repository)
    print("Saved build source, tag, versions and published package hashes verified.")
