"""Artifact handoff must preserve validated bytes and reject altered receipts."""

from __future__ import annotations

import hashlib
import json
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from scripts.check_pypi_recovery import verify as verify_recovery
from scripts.package_release import collect


def fixture(root: Path) -> None:
    for platform in ("linux-x64", "windows-x64"):
        directory = root / f"build-{platform}"
        directory.mkdir(parents=True)
        wheel = directory / "discuss-1.1.1-py3-none-any.whl"
        with zipfile.ZipFile(wheel, "w") as archive:
            archive.writestr("discuss-1.1.1.dist-info/METADATA", "Version: 1.1.1\n")
        with tarfile.open(directory / "discuss-1.1.1.tar.gz", "w:gz") as archive:
            payload = b"Version: 1.1.1\n"
            member = tarfile.TarInfo("discuss-1.1.1/PKG-INFO")
            member.size = len(payload)
            archive.addfile(member, BytesIO(payload))
        (directory / "SHA256SUMS").write_text("validated checksum fixture\n")
        receipt = {
            "source_commit": "abc",
            "tag": "v1.1.1",
            "platform": platform,
            "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()},
        }
        (directory / "build-receipt.json").write_text(json.dumps(receipt))


def test_collection_preserves_saved_bytes(tmp_path: Path) -> None:
    source, output = tmp_path / "saved", tmp_path / "dist"
    fixture(source)
    collect(source, output, "v1.1.1", "abc")
    assert len(list(output.iterdir())) == 3
    for path in output.iterdir():
        if path.name != "SHA256SUMS":
            assert path.read_bytes() == (source / "build-linux-x64" / path.name).read_bytes()


@pytest.mark.parametrize("damage", ["source", "version", "checksum", "extra", "metadata"])
def test_collection_rejects_invalid_handoff(tmp_path: Path, damage: str) -> None:
    source = tmp_path / "saved"
    fixture(source)
    directory = source / "build-windows-x64"
    receipt_path = directory / "build-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    if damage == "source":
        receipt["source_commit"] = "def"
    elif damage == "version":
        receipt["tag"] = "v1.1.2"
    elif damage == "extra":
        (directory / "unexpected.txt").write_text("unrecorded")
    else:
        wheel = next(directory.glob("*.whl"))
        if damage == "checksum":
            wheel.write_bytes(b"tampered")
        else:
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr("discuss-1.1.1.dist-info/METADATA", "Version: 9.9.9\n")
            receipt["files"][wheel.name] = hashlib.sha256(wheel.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        collect(source, tmp_path / "dist", "v1.1.1", "abc")
    assert not (tmp_path / "dist").exists()


@pytest.mark.parametrize(
    "damage", [None, "source", "tag", "published_hash", "draft", "prerelease", "checksum", "extra"]
)
def test_pypi_recovery_requires_original_published_bytes(tmp_path: Path, damage: str | None) -> None:
    fixture(tmp_path)
    directory = tmp_path / "build-linux-x64"
    receipt = json.loads((directory / "build-receipt.json").read_text())
    release = {
        "tag_name": "v1.1.1",
        "draft": False,
        "prerelease": False,
        "assets": [{"name": name, "digest": "sha256:" + digest} for name, digest in receipt["files"].items()],
    }
    ref = {"object": {"type": "commit", "sha": "abc", "url": "fixture"}}
    source = "def" if damage == "source" else "abc"
    if damage == "tag":
        ref["object"]["sha"] = "def"
    elif damage == "published_hash":
        release["assets"][0]["digest"] = "sha256:changed"
    elif damage in ("draft", "prerelease"):
        release[damage] = True
    elif damage == "checksum":
        (directory / "SHA256SUMS").write_text("altered")
    elif damage == "extra":
        (directory / "extra.txt").write_text("unrecorded")

    def api(endpoint: str) -> dict:
        return release if "/releases/" in endpoint else ref

    if damage is None:
        verify_recovery(directory, source, "fixture/repo", api)
    else:
        with pytest.raises(ValueError):
            verify_recovery(directory, source, "fixture/repo", api)
