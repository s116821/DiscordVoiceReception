"""Verify tag-derived metadata and assemble lean release assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]


def artifact_version(path: Path) -> str:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
            if len(names) != 1:
                raise ValueError("Wheel must contain exactly one metadata record")
            text = archive.read(names[0]).decode("utf-8")
    else:
        with tarfile.open(path) as archive:
            members = [m for m in archive.getmembers() if m.name.count("/") == 1 and m.name.endswith("/PKG-INFO")]
            if len(members) != 1:
                raise ValueError("Source archive must contain exactly one root metadata record")
            stream = archive.extractfile(members[0])
            if stream is None:
                raise ValueError("Missing source metadata")
            text = stream.read().decode("utf-8")
    value = Parser().parsestr(text).get("Version")
    if value is None:
        raise ValueError("Missing package version")
    return value


def assemble(root: Path, output: Path, tag: str) -> list[Path]:
    if not tag.startswith("v") or str(Version(tag[1:])) != tag[1:]:
        raise ValueError("Release tag must be v followed by the canonical package version")
    wheels = list(output.glob("*.whl"))
    sources = list(output.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError("Expected one wheel and one sdist in a clean output directory")
    for path in wheels + sources:
        if artifact_version(path) != tag[1:]:
            raise ValueError(f"Artifact metadata does not match tag: {path.name}")
    assets = wheels + sources
    checksums = output / "SHA256SUMS"
    checksums.write_text(
        "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in sorted(assets)), encoding="utf-8"
    )
    return assets + [checksums]


def collect(source: Path, output: Path, tag: str, commit: str) -> None:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Publication output must be empty")
    selected: list[Path] = []
    for platform in ("linux-x64", "windows-x64"):
        directory = source / f"build-{platform}"
        receipt = json.loads((directory / "build-receipt.json").read_text(encoding="utf-8"))
        if (receipt["source_commit"], receipt["tag"], receipt["platform"]) != (commit, tag, platform):
            raise ValueError("Build receipt does not match final release source/version/platform")
        if set(receipt["files"]) != {p.name for p in directory.iterdir() if p.name != "build-receipt.json"}:
            raise ValueError("Build contains unrecorded or missing artifacts")
        for name, digest in receipt["files"].items():
            if Path(name).name != name or hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
                raise ValueError("Build artifact checksum mismatch")
        wheels = list(directory.glob("*.whl"))
        sources = list(directory.glob("*.tar.gz"))
        if len(wheels) != 1 or len(sources) != 1:
            raise ValueError("Expected one wheel and one sdist")
        for path in wheels + sources:
            if artifact_version(path) != tag.removeprefix("v"):
                raise ValueError("Package metadata differs from final release version")
        if platform == "linux-x64":
            selected.extend(wheels + sources)
    output.mkdir(parents=True, exist_ok=True)
    for path in selected:
        shutil.copyfile(path, output / path.name)
    (output / "SHA256SUMS").write_text(
        "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in sorted(output.iterdir())),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    assembly = commands.add_parser("assemble")
    assembly.add_argument("--tag", default="")
    assembly.add_argument("--platform", required=True, choices=("linux-x64", "windows-x64"))
    assembly.add_argument("--commit", required=True)
    publication = commands.add_parser("collect")
    publication.add_argument("source", type=Path)
    publication.add_argument("--tag", required=True)
    publication.add_argument("--commit", required=True)
    args = parser.parse_args()
    output = ROOT / "dist"
    if args.command == "collect":
        collect(args.source, output, args.tag, args.commit)
        return
    tag = args.tag or "v" + artifact_version(next(output.glob("*.whl")))
    assets = assemble(ROOT, output, tag)
    receipt = {
        "source_commit": args.commit,
        "tag": tag,
        "platform": args.platform,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in assets},
    }
    (output / "build-receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    if os.environ.get("GITHUB_OUTPUT"):
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
            stream.write(f"tag={tag}\n")


if __name__ == "__main__":
    main()
