from __future__ import annotations

import importlib
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

import pytest
import yaml
from packaging.version import Version
from scripts.package_release import artifact_version, assemble

ROOT = Path(__file__).resolve().parents[1]
PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
MODULE = "discuss" if PROJECT["project"]["name"] == "discuss" else "discord_voice_reception"


def run_git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["pwsh", "-File", str(ROOT / "scripts/git.ps1"), *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_dynamic_version_only() -> None:
    assert PROJECT["project"]["dynamic"] == ["version"]
    assert "version" not in PROJECT["project"]
    assert PROJECT["tool"]["hatch"]["version"]["source"] == "uv-dynamic-versioning"
    assert PROJECT["tool"]["uv-dynamic-versioning"] == {
        "vcs": "git",
        "style": "pep440",
        "fallback-version": "0.0.0",
    }


def test_runtime_metadata_and_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module(f"{MODULE}.version")
    assert isinstance(Version(module.service_version()), Version)
    monkeypatch.setattr(module, "version", lambda name: "1.2.3")
    assert module.service_version() == "1.2.3"

    def missing(name: str) -> str:
        raise module.PackageNotFoundError(name)

    monkeypatch.setattr(module, "version", missing)
    assert module.service_version() == "0.0.0"


def test_actual_tag_build_and_release_assets(tmp_path: Path) -> None:
    repo = tmp_path / "tagged"
    repo.mkdir()
    for name in ("pyproject.toml", "README.md", "LICENSE", "NOTICE", "uv.lock", ".gitignore"):
        shutil.copy2(ROOT / name, repo / name)
    shutil.copytree(ROOT / "src", repo / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "docs", repo / "docs")
    for name in (".agents/noise.md", ".github/workflows/noise.yml", "openspec/noise.md", "scripts/noise.py"):
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("development-only fixture")
    (repo / "package.json").write_text("{}")
    run_git(repo, "init")
    run_git(repo, "add", ".")
    run_git(
        repo,
        "-c",
        "user.name=s116821",
        "-c",
        "user.email=99853371+s116821@users.noreply.github.com",
        "commit",
        "-m",
        "chore(fixture): initialize",
    )
    run_git(repo, "tag", "v1.2.3")
    assert run_git(repo, "describe", "--tags", "--abbrev=0") == "v1.2.3"
    subprocess.run(["uv", "build", "--out-dir", str(repo / "dist")], cwd=repo, check=True, capture_output=True)
    wheel = next((repo / "dist").glob("*.whl"))
    assert artifact_version(wheel) == "1.2.3"
    assets = assemble(repo, repo / "dist", "v1.2.3")
    assert (repo / "dist/SHA256SUMS").is_file()
    assert all("1.2.3" in p.name or p.name == "SHA256SUMS" for p in assets)
    source = next((repo / "dist").glob("*.tar.gz"))
    extracted = tmp_path / "extracted"
    with tarfile.open(source) as archive:
        names = {"/".join(member.name.split("/")[1:]) for member in archive.getmembers()}
        assert not any(name.startswith((".agents/", ".cursor/", ".github/", "openspec/", "scripts/")) for name in names)
        assert "package.json" not in names and "package-lock.json" not in names
        assert {"LICENSE", "NOTICE", "docs/licenses/discord-ext-voice-recv.txt", "pyproject.toml", "uv.lock"} <= names
        assert any(name.startswith("docs/") for name in names)
        assert any(name.startswith("docs/examples/") for name in names)
        archive.extractall(extracted, filter="data")
    source_root = next(extracted.iterdir())
    rebuilt = tmp_path / "rebuilt"
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(rebuilt)], cwd=source_root, check=True, capture_output=True
    )
    rebuilt_wheel = next(rebuilt.glob("*.whl"))
    assert artifact_version(rebuilt_wheel) == "1.2.3"
    with zipfile.ZipFile(rebuilt_wheel) as archive:
        names = archive.namelist()
        assert "discord_voice_reception/__init__.py" in names and "discord_voice_reception/py.typed" in names
        assert any(name.endswith("/licenses/LICENSE") for name in names)
        assert any(name.endswith("/licenses/NOTICE") for name in names)
        assert any(name.endswith("/licenses/docs/licenses/discord-ext-voice-recv.txt") for name in names)
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys; sys.path.insert(0, sys.argv[1]); import discord_voice_reception as r; "
            "assert r.__file__.startswith(sys.argv[1]); assert r.service_version()=='1.2.3'",
            str(rebuilt_wheel),
        ],
        check=True,
        capture_output=True,
    )
    with pytest.raises(ValueError, match="metadata does not match"):
        # Fresh build output: exclude the already created deployment tarball.
        clean = tmp_path / "mismatch"
        clean.mkdir()
        for p in (repo / "dist").iterdir():
            if p.name.startswith(PROJECT["project"]["name"].replace("-", "_")):
                shutil.copy2(p, clean / p.name)
        assemble(repo, clean, "v9.9.9")


def test_gitignore_covers_local_secrets() -> None:
    for pattern in ("config.json", ".env", ".venv/lib", "data/example.db", "models/weights", "secret.token"):
        result = subprocess.run(
            ["pwsh", "-File", str(ROOT / "scripts/git.ps1"), "check-ignore", "-q", pattern],
            cwd=ROOT,
        )
        assert result.returncode == 0, pattern


def test_reference_analyzer_config_and_release_gate() -> None:
    config = json.loads((ROOT / ".releaserc.json").read_text(encoding="utf-8"))
    plugin, options = config["plugins"][0]
    assert plugin == "@semantic-release/commit-analyzer"
    assert options["preset"] == "conventionalcommits"
    assert {"type": "docs", "release": False} in options["releaseRules"]
    assert {"breaking": True, "release": "major"} in options["releaseRules"]
    assert not (ROOT / f"src/{MODULE}/release_policy.py").exists()
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    jobs = yaml.load(ci, Loader=yaml.BaseLoader)["jobs"]
    for gate in ("ruff check", "ruff format --check", "ty check", "pytest", "spec:validate"):
        assert gate in ci
    assert set(jobs) == {"quality", "build", "release"}
    assert "strategy" not in jobs["quality"]
    assert jobs["build"]["needs"] == "quality"
    assert jobs["release"]["needs"] == ["quality", "build"]
    assert "github.event_name == 'push'" in jobs["release"]["if"]
    assert not (ROOT / ".github/workflows/release.yml").exists()
    for job in (jobs["build"], jobs["release"]):
        commands = "\n".join(step.get("run", "") for step in job["steps"])
        assert all(check not in commands for check in ("ruff", "pytest", "ty check", "test:release", "spec:validate"))
    upload = jobs["release"]["steps"][-1]
    assert upload["with"]["name"] == "release-distributions"
    assert upload["if"] == "steps.semantic.outputs.new_release_published == 'true'"
    assert "outputs" not in jobs["quality"]
    assert "semantic" not in "\n".join(step.get("run", "") for step in jobs["quality"]["steps"])
    assert "RELEASE_READY" not in ci
    assert "PYPI_PUBLISH_READY" not in ci
    publish = (ROOT / ".github/workflows/publish.yml").read_text(encoding="utf-8")
    assert "workflow_run:" in publish and "workflow_dispatch:" in publish
    assert "workflow_call:" not in publish
    assert "run.conclusion !== 'success'" in publish and "run.event !== 'push'" in publish
    assert "run.head_branch !== 'main'" in publish
    assert "workflow.path !== '.github/workflows/ci.yml'" in publish
    assert "sha256sum --strict --check SHA256SUMS" in publish
    assert "run-id: ${{ needs.distributions.outputs.run }}" in publish
    assert "environment: pypi" in publish and "id-token: write" in publish
    assert "context.eventName === 'workflow_dispatch'" in publish
    assert "a.name === 'build-linux-x64'" in publish
    assert "check_pypi_recovery.py" in publish
    assert "core.setOutput('source', run.head_sha)" in publish
    pr = (ROOT / ".github/workflows/pr-title.yml").read_text(encoding="utf-8")
    assert "requireScope: true" in pr
    assert "fetch-depth: 0" in ci


def test_ruff_rejects_invalid_source(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("def bad(\n", encoding="utf-8")
    result = subprocess.run(["uv", "run", "--locked", "ruff", "check", str(bad)], cwd=ROOT, capture_output=True)
    assert result.returncode != 0


def test_no_static_version_constant() -> None:
    source = (ROOT / f"src/{MODULE}/version.py").read_text(encoding="utf-8")
    assert not re.search(r"(?m)^__version__\s*=", source)


def test_explicit_ci_python_and_optional_release_fixtures():
    import yaml

    root = Path(__file__).resolve().parents[1]
    ci = yaml.safe_load((root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    assert ci["env"]["UV_PYTHON"] == "3.12"
    assert not (root / ".python-version").exists()
    commands = " ".join(step.get("run", "") for step in ci["jobs"]["quality"]["steps"])
    assert "test:release" not in commands
    assert "test:release" in (root / "package.json").read_text(encoding="utf-8")
