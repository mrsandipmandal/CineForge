"""Tests for IDE / AI client MCP detection and multi-client config merging."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from cineforge_mcp.installer import (
    SUPPORTED_CLIENTS,
    build_client_payload,
    client_config_path,
    detect_mcp_clients,
    format_client_config,
    install_mcp_config,
)


def _mock_empty_environment(monkeypatch: pytest.MonkeyPatch, home: Path) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr("cineforge_mcp.installer.platform.system", lambda: "Linux")
    monkeypatch.setattr("cineforge_mcp.installer.shutil.which", lambda _name: None)


def test_detect_mcp_clients_reports_all_clients_without_false_positives(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    proj = tmp_path / "project"
    proj.mkdir()
    _mock_empty_environment(monkeypatch, fake_home)

    # Create Antigravity dir only — must NOT falsely detect gemini-cli!
    (fake_home / ".gemini" / "antigravity").mkdir(parents=True)
    # Also simulate VS Code, OpenCode, Claude Code, Codex, Windsurf, Cursor
    (fake_home / ".claude").mkdir()
    (fake_home / ".cursor").mkdir()
    (fake_home / ".codeium" / "windsurf").mkdir(parents=True)
    (fake_home / ".config" / "opencode").mkdir(parents=True)
    (fake_home / ".codex").mkdir()
    (fake_home / ".config" / "Code" / "User").mkdir(parents=True)

    rows = detect_mcp_clients(project_dir=proj)
    by_id = {r["client"]: r for r in rows}
    assert set(by_id.keys()) == set(SUPPORTED_CLIENTS)

    assert by_id["antigravity"]["installed"] is True
    assert by_id["gemini-cli"]["installed"] is False
    assert by_id["claude"]["installed"] is False
    assert by_id["claude-code"]["installed"] is True
    assert by_id["cursor"]["installed"] is True
    assert by_id["windsurf"]["installed"] is True
    assert by_id["opencode"]["installed"] is True
    assert by_id["codex"]["installed"] is True
    assert by_id["vscode"]["installed"] is True
    assert all(not r["configured"] for r in rows)


def test_detect_mcp_clients_detects_gemini_cli_and_configured_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    proj = tmp_path / "project"
    proj.mkdir()
    _mock_empty_environment(monkeypatch, fake_home)
    monkeypatch.setattr(
        "cineforge_mcp.installer.shutil.which",
        lambda name: "/usr/local/bin/gemini" if name == "gemini" else None,
    )
    gemini_cfg = fake_home / ".gemini" / "settings.json"
    gemini_cfg.parent.mkdir(parents=True)
    gemini_cfg.write_text('{"mcpServers": {"cineforge": {"command": "cineforge-mcp"}}}\n', encoding="utf-8")

    rows = detect_mcp_clients(project_dir=proj)
    by_id = {r["client"]: r for r in rows}
    assert by_id["gemini-cli"]["installed"] is True
    assert by_id["gemini-cli"]["configured"] is True
    assert by_id["gemini-cli"]["configured_scopes"] == ["global"]
    assert by_id["antigravity"]["installed"] is False


def test_install_preserves_backwards_compat_auto_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    proj = tmp_path / "project"
    proj.mkdir()
    _mock_empty_environment(monkeypatch, fake_home)

    assert client_config_path("claude-code", project_dir=proj, scope="auto") == proj.resolve() / ".mcp.json"
    assert client_config_path("claude-code", project_dir=proj, scope="global") == fake_home / ".claude.json"
    assert client_config_path("vscode", project_dir=proj, scope="auto") == proj.resolve() / ".vscode" / "mcp.json"
    assert client_config_path("vscode", project_dir=proj, scope="global") == fake_home / ".config" / "Code" / "User" / "mcp.json"


def test_install_opencode_vscode_global_and_codex_toml_merge_with_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    ws = tmp_path / "ws"
    ws.mkdir()
    _mock_empty_environment(monkeypatch, fake_home)

    # 1) OpenCode with JSONC comments and existing server + $schema
    oc_path = fake_home / ".config" / "opencode" / "opencode.json"
    oc_path.parent.mkdir(parents=True)
    oc_path.write_text(
        '// OpenCode config\n{\n  "$schema": "https://opencode.ai/config.json",\n  "mcp": {\n    "other": {"type": "local", "command": ["echo"], "enabled": true}\n  }\n}\n',
        encoding="utf-8",
    )
    oc_res = install_mcp_config("opencode", workspace=ws, scope="global", use_uvx=True)
    assert oc_res["backup_path"] == str(oc_path) + ".bak"
    assert Path(oc_res["backup_path"]).is_file()
    oc_loaded = json.loads(oc_path.read_text(encoding="utf-8"))
    assert oc_loaded["$schema"] == "https://opencode.ai/config.json"
    assert "other" in oc_loaded["mcp"]
    assert oc_loaded["mcp"]["cineforge"]["type"] == "local"
    assert oc_loaded["mcp"]["cineforge"]["command"] == ["uvx", "--from", "cineforge", "cineforge-mcp"]
    assert oc_loaded["mcp"]["cineforge"]["environment"] == {"CINEFORGE_HOME": str(ws.resolve())}

    # 2) VS Code global User/mcp.json preserving existing servers
    vsc_path = fake_home / ".config" / "Code" / "User" / "mcp.json"
    vsc_path.parent.mkdir(parents=True)
    vsc_path.write_text('{"servers": {"existing": {"type": "stdio", "command": "npx"}}}\n', encoding="utf-8")
    vsc_res = install_mcp_config("vscode", workspace=ws, scope="global", use_uvx=True)
    assert Path(vsc_res["backup_path"]).is_file()
    vsc_loaded = json.loads(vsc_path.read_text(encoding="utf-8"))
    assert "existing" in vsc_loaded["servers"]
    assert vsc_loaded["servers"]["cineforge"]["type"] == "stdio"

    # 3) Codex config.toml preserving unrelated sections and replacing existing cineforge block
    codex_path = fake_home / ".codex" / "config.toml"
    codex_path.parent.mkdir(parents=True)
    codex_path.write_text(
        'model = "o3"\n\n[mcp_servers.cineforge]\ncommand = "old"\n\n[mcp_servers.other]\ncommand = "npx"\n',
        encoding="utf-8",
    )
    codex_res = install_mcp_config("codex", workspace=ws, scope="global", use_uvx=True)
    assert Path(codex_res["backup_path"]).is_file()
    codex_text = codex_path.read_text(encoding="utf-8")
    assert 'model = "o3"' in codex_text
    assert "[mcp_servers.other]" in codex_text
    assert 'command = "old"' not in codex_text
    assert 'command = "uvx"' in codex_text
    if sys.version_info >= (3, 11):
        import tomllib

        parsed = tomllib.loads(codex_text)
        assert parsed["mcp_servers"]["cineforge"]["env"]["CINEFORGE_HOME"] == str(ws.resolve())
        assert parsed["mcp_servers"]["other"]["command"] == "npx"

    # Confirm detect now sees all three configured globally
    detected = {r["client"]: r for r in detect_mcp_clients()}
    assert detected["opencode"]["configured_scopes"] == ["global"]
    assert detected["vscode"]["configured_scopes"] == ["global"]
    assert detected["codex"]["configured_scopes"] == ["global"]


def test_install_rejects_malformed_json_and_format_codex_toml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    _mock_empty_environment(monkeypatch, fake_home)

    bad_cfg = fake_home / ".cursor" / "mcp.json"
    bad_cfg.parent.mkdir(parents=True)
    bad_cfg.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        install_mcp_config("cursor", scope="global", use_uvx=True)

    payload = build_client_payload("opencode", {"command": "uvx", "args": [], "env": {"CINEFORGE_HOME": "/tmp/ws"}})
    assert "mcp" in payload and "cineforge" in payload["mcp"]
    toml_str = format_client_config("codex", {"command": "uvx", "args": ["--from", "cineforge", "cineforge-mcp"]})
    assert toml_str.startswith("[mcp_servers.cineforge]")
