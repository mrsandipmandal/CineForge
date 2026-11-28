"""Tests for `cineforge update` and `cineforge repair` CLI & maintenance helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from cineforge_cli import __version__
from cineforge_cli.main import app
from cineforge_cli.maintenance import (
    detect_install_info,
    fetch_latest_pypi_version,
    run_repair,
    run_update,
)
from cineforge_mcp.installer import inspect_configured_mcp_entries

runner = CliRunner()


def test_detect_install_info_modes(tmp_path: Path, monkeypatch) -> None:
    # 1. uv tool from PyPI (`uv-receipt.toml` without `directory`)
    uv_pypi_prefix = tmp_path / "uv" / "tools" / "cineforge"
    uv_pypi_prefix.mkdir(parents=True)
    (uv_pypi_prefix / "uv-receipt.toml").write_text(
        '[tool]\nrequirements = [{ name = "cineforge" }]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "prefix", str(uv_pypi_prefix))
    monkeypatch.setattr("cineforge_cli.maintenance.get_package_root", lambda: uv_pypi_prefix / "lib" / "site-packages" / "cineforge_assets")
    info_pypi = detect_install_info()
    assert info_pypi["mode"] == "uv-tool-pypi"

    # 2. uv tool from local directory
    local_repo = tmp_path / "local_repo"
    (local_repo / ".git").mkdir(parents=True)
    uv_local_prefix = tmp_path / "uv_local" / "tools" / "cineforge"
    uv_local_prefix.mkdir(parents=True)
    (uv_local_prefix / "uv-receipt.toml").write_text(
        f'[tool]\nrequirements = [{{ name = "cineforge", directory = "{local_repo}" }}]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "prefix", str(uv_local_prefix))
    info_local = detect_install_info()
    assert info_local["mode"] == "uv-tool-local"
    assert info_local["source_dir"] == str(local_repo.resolve())

    # 3. git-editable repo checkout
    venv_prefix = tmp_path / "repo" / ".venv"
    venv_prefix.mkdir(parents=True)
    git_root = tmp_path / "repo"
    (git_root / ".git").mkdir()
    (git_root / "pyproject.toml").write_text('[project]\nname = "cineforge"\n', encoding="utf-8")
    monkeypatch.setattr(sys, "prefix", str(venv_prefix))
    monkeypatch.setattr("cineforge_cli.maintenance.get_package_root", lambda: git_root)
    info_git = detect_install_info()
    assert info_git["mode"] == "git-editable"


def test_fetch_latest_pypi_version_handles_success_and_offline(monkeypatch) -> None:
    class _FakeResp:
        def __init__(self, ver: str) -> None:
            self._payload = json.dumps({"info": {"version": ver}}).encode("utf-8")

        def read(self) -> bytes:
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr("cineforge_cli.maintenance._urllib_request.urlopen", lambda _req, timeout=5: _FakeResp("99.0.0"))
    res_new = fetch_latest_pypi_version()
    assert res_new["ok"] is True
    assert res_new["latest_version"] == "99.0.0"
    assert res_new["update_available"] is True

    monkeypatch.setattr("cineforge_cli.maintenance._urllib_request.urlopen", lambda _req, timeout=5: _FakeResp(__version__))
    res_same = fetch_latest_pypi_version()
    assert res_same["ok"] is True
    assert res_same["update_available"] is False

    def _boom(_req, timeout=5):
        raise OSError("network disabled")

    monkeypatch.setattr("cineforge_cli.maintenance._urllib_request.urlopen", _boom)
    res_off = fetch_latest_pypi_version()
    assert res_off["ok"] is False
    assert res_off["latest_version"] is None


def test_update_check_dry_run_and_dirty_git_guard(tmp_path: Path, monkeypatch) -> None:
    ws = tmp_path / "ws"
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / "pyproject.toml").write_text('[project]\nname = "cineforge"\n', encoding="utf-8")

    monkeypatch.setattr(
        "cineforge_cli.maintenance.detect_install_info",
        lambda: {
            "mode": "git-editable",
            "current_version": __version__,
            "python_executable": sys.executable,
            "prefix": str(repo / ".venv"),
            "package_root": str(repo),
            "source_dir": str(repo),
            "is_git_repo": True,
            "uv_available": True,
            "uv_path": "/usr/bin/uv",
            "editable": True,
        },
    )
    monkeypatch.setattr(
        "cineforge_cli.maintenance.fetch_latest_pypi_version",
        lambda timeout=5: {
            "ok": True,
            "current_version": __version__,
            "latest_version": "0.9.0",
            "update_available": True,
            "error": None,
        },
    )
    monkeypatch.setattr("cineforge_cli.maintenance._git_is_dirty", lambda _repo: True)

    res = runner.invoke(app, ["-w", str(ws), "update", "--check", "--json"])
    assert res.exit_code == 0, res.stdout
    payload = json.loads(res.stdout)
    assert payload["mode"] == "check"
    assert payload["pypi"]["update_available"] is True
    assert any("uncommitted changes" in w for w in payload["warnings"])
    # Dirty repo skips git pull and keeps only editable reinstall
    assert all("pull" not in " ".join(s["command"]) for s in payload["steps"])

    # Switching to --from-pypi targets PyPI package with extras
    dry_pypi = run_update(workspace=ws, dry_run=True, from_pypi=True, extras="tts,whisper")
    assert any("cineforge[tts,whisper]" in " ".join(s["command"]) for s in dry_pypi["steps"])


def test_repair_workspace_env_config_and_broken_mcp_configs(tmp_path: Path, monkeypatch) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    ws = tmp_path / "ws"
    ws.mkdir()
    proj = tmp_path / "proj"
    proj.mkdir()

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    monkeypatch.setattr("cineforge_mcp.installer.platform.system", lambda: "Linux")

    # Corrupted config.yaml, duplicate/ANSI/CRLF .env, stale lock & mux temp file
    (ws / ".backlot").mkdir()
    (ws / ".backlot" / "server.lock").write_text("123", encoding="utf-8")
    (ws / "projects" / "demo").mkdir(parents=True)
    (ws / "projects" / "demo" / ".clip.audio-mux-999.mp4").write_bytes(b"partial")
    (ws / "config.yaml").write_text("::: [broken yaml", encoding="utf-8")
    (ws / ".env").write_bytes(
        b'# header\r\nGEMINI_API_KEY="\x1b[200~old_key\x1b[201~"\r\nGEMINI_API_KEY=fresh_key_123\r\nOTHER_KEY=ok\r\n'
    )

    # Broken MCP config (nonexistent executable + missing workspace) + one healthy config pointing at valid other workspace
    opencode_cfg = fake_home / ".config" / "opencode" / "opencode.json"
    opencode_cfg.parent.mkdir(parents=True)
    opencode_cfg.write_text(
        json.dumps(
            {
                "$schema": "https://opencode.ai/config.json",
                "mcp": {
                    "cineforge": {
                        "type": "local",
                        "command": ["/nonexistent/dead/bin/cineforge-mcp"],
                        "enabled": True,
                        "environment": {"CINEFORGE_HOME": str(tmp_path / "deleted_ws")},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    valid_other_ws = tmp_path / "valid_other_ws"
    valid_other_ws.mkdir()
    cursor_cfg = fake_home / ".cursor" / "mcp.json"
    cursor_cfg.parent.mkdir(parents=True)
    cursor_cfg.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "cineforge": {
                        "command": sys.executable,
                        "args": ["-m", "cineforge_mcp"],
                        "env": {"CINEFORGE_HOME": str(valid_other_ws)},
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    # Verify inspect_configured_mcp_entries flags broken opencode entry without false-positiving healthy cursor entry
    entries = inspect_configured_mcp_entries(project_dir=proj)
    by_client = {e["client"]: e for e in entries}
    assert by_client["opencode"]["needs_repair"] is True
    assert len(by_client["opencode"]["reasons"]) >= 2
    assert by_client["cursor"]["needs_repair"] is False

    # Dry-run MUST leave files untouched!
    dry = runner.invoke(app, ["-w", str(ws), "repair", "--workspace-only", "--dry-run", "--json"])
    assert dry.exit_code == 0, dry.stdout
    dry_data = json.loads(dry.stdout)
    assert any(a["status"] == "needs_repair" for a in dry_data["actions"])
    assert not (ws / ".env.bak").exists()
    assert (ws / ".backlot" / "server.lock").exists()

    # Apply workspace + env + mcp repair via CLI
    rep_ws = runner.invoke(app, ["-w", str(ws), "repair", "--workspace-only", "--mcp", "--project-dir", str(proj), "--yes", "--json"])
    assert rep_ws.exit_code == 0, rep_ws.stdout
    rep_data = json.loads(rep_ws.stdout)
    assert rep_data["success"] is True

    # Verify .env deduplication + ANSI strip + backup
    assert (ws / ".env.bak").is_file()
    cleaned_env = (ws / ".env").read_text(encoding="utf-8")
    assert cleaned_env.count("GEMINI_API_KEY=") == 1
    assert "GEMINI_API_KEY=fresh_key_123" in cleaned_env
    assert "\x1b[200~" not in cleaned_env
    assert "\r\n" not in (ws / ".env").read_bytes().decode("latin1")

    # Verify corrupted config.yaml restored with .bak backup
    assert (ws / "config.yaml.bak").is_file()
    assert (ws / "config.yaml").is_file()
    assert "broken yaml" not in (ws / "config.yaml").read_text(encoding="utf-8")

    # Verify stale lock & mux temp deleted
    assert not (ws / ".backlot" / "server.lock").exists()
    assert not (ws / "projects" / "demo" / ".clip.audio-mux-999.mp4").exists()

    # Verify broken OpenCode MCP config was repaired with backup while healthy Cursor config was untouched
    assert (opencode_cfg.with_suffix(".json.bak")).is_file()
    assert not (cursor_cfg.with_suffix(".json.bak")).exists()
    repaired_oc = json.loads(opencode_cfg.read_text(encoding="utf-8"))
    assert repaired_oc["$schema"] == "https://opencode.ai/config.json"
    assert repaired_oc["mcp"]["cineforge"]["environment"]["CINEFORGE_HOME"] == str(ws.resolve())
    assert repaired_oc["mcp"]["cineforge"]["command"][0] != "/nonexistent/dead/bin/cineforge-mcp"
