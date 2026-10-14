"""Build once, verify metadata and install the saved wheel on this platform."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.create_release import ROOT, artifact_version, assemble


def git(*args: str) -> str:
    return subprocess.check_output(["pwsh", "-File", str(ROOT / "scripts/git.ps1"), *args], cwd=ROOT, text=True).strip()


def build(platform: str, candidate: str = "") -> str:
    output = ROOT / "dist"
    if output.exists() and any(output.iterdir()):
        raise ValueError("Build output must be empty")
    commit = git("rev-parse", "HEAD")
    if candidate:
        git("tag", candidate, commit)
    os.environ["SOURCE_DATE_EPOCH"] = git("show", "-s", "--format=%ct", commit)
    subprocess.run(["uv", "build"], cwd=ROOT, check=True)
    wheel = next(output.glob("*.whl"))
    tag = candidate or "v" + artifact_version(wheel)
    assets = assemble(ROOT, output, tag)
    check = ROOT / "package-check"
    if check.exists():
        raise ValueError("Package install environment must be new")
    subprocess.run(["uv", "venv", "--python", sys.executable, str(check)], check=True)
    python = check / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    requirements = ROOT / "package-requirements.txt"
    subprocess.run(
        [
            "uv",
            "export",
            "--locked",
            "--no-dev",
            "--no-emit-project",
            "--format",
            "requirements-txt",
            "--output-file",
            str(requirements),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(["uv", "pip", "sync", "--python", str(python), "--require-hashes", str(requirements)], check=True)
    subprocess.run(["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel)], check=True)
    subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "import discord_voice_reception as r; from discord.opus import Decoder; "
            "import sys; assert r.service_version()==sys.argv[1]; Decoder()",
            tag[1:],
        ],
        check=True,
    )
    receipt = {
        "source_commit": commit,
        "tag": tag,
        "platform": platform,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in assets},
    }
    (output / "build-receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    if os.environ.get("GITHUB_OUTPUT"):
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
            stream.write(f"tag={tag}\n")
    return tag


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=("linux-x64", "windows-x64"))
    parser.add_argument("--candidate", default="")
    args = parser.parse_args()
    print(build(args.platform, args.candidate))
