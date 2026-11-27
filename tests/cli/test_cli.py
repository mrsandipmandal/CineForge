"""Tests for the CineForge Typer CLI and MCP config installer."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from cineforge_cli.main import app
from cineforge_mcp.installer import install_mcp_config

runner = CliRunner()


def test_cli_version_and_help() -> None:
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "cineforge" in res.stdout

    help_res = runner.invoke(app, ["--help"])
    assert help_res.exit_code == 0
    for cmd in ("init", "setup", "doctor", "studio", "demo", "tools", "pipelines", "mcp"):
        assert cmd in help_res.stdout


def test_cli_init_and_doctor_json(tmp_path: Path, monkeypatch) -> None:
    ws = tmp_path / "my-studio"
    init_res = runner.invoke(app, ["init", str(ws)])
    assert init_res.exit_code == 0, init_res.stdout
    assert (ws / ".cineforge").is_dir()
    assert (ws / "projects").is_dir()

    monkeypatch.setenv("CINEFORGE_HOME", str(ws))
    monkeypatch.setenv("CINEFORGE_PROJECTS_DIR", str(ws / "projects"))
    doc_res = runner.invoke(app, ["--workspace", str(ws), "doctor", "--json"])
    assert doc_res.exit_code == 0, doc_res.stdout
    payload = json.loads(doc_res.stdout)
    assert payload["total_tools_discovered"] > 50
    assert payload["paths"]["workspace_root"] == str(ws.resolve())
    assert "capabilities" in payload["provider_summary"]


def test_cli_pipelines_and_tools_commands() -> None:
    p_res = runner.invoke(app, ["pipelines", "list", "--json"])
    assert p_res.exit_code == 0, p_res.stdout
    pipelines = json.loads(p_res.stdout)
    names = {item["name"] for item in pipelines}
    assert "animated-explainer" in names
    assert "cinematic" in names

    t_res = runner.invoke(app, ["tools", "list", "--capability", "tts", "--json"])
    assert t_res.exit_code == 0, t_res.stdout
    tools = json.loads(t_res.stdout)
    assert any(t["name"] == "tts_selector" for t in tools)

    dry_res = runner.invoke(app, ["tools", "run", "tts_selector", "--dry-run"])
    assert dry_res.exit_code == 0, dry_res.stdout
    dry = json.loads(dry_res.stdout)
    assert dry["tool"] == "tts_selector"
    assert dry["would_execute"] is True


def test_cli_mcp_config_and_install_preserves_existing(tmp_path: Path, monkeypatch) -> None:
    cfg_res = runner.invoke(app, ["mcp", "config", "--client", "claude", "--uvx"])
    assert cfg_res.exit_code == 0, cfg_res.stdout
    cfg = json.loads(cfg_res.stdout)
    assert cfg["mcpServers"]["cineforge"]["command"] == "uvx"

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    existing_mcp = project_dir / ".mcp.json"
    existing_mcp.write_text(
        json.dumps({"mcpServers": {"other": {"command": "echo", "args": ["hi"]}}}),
        encoding="utf-8",
    )

    out = install_mcp_config(
        "claude-code",
        workspace=tmp_path / "ws",
        project_dir=project_dir,
        use_uvx=True,
    )
    assert Path(out["backup_path"]).is_file()
    merged = json.loads(existing_mcp.read_text(encoding="utf-8"))
    assert "other" in merged["mcpServers"]
    assert merged["mcpServers"]["cineforge"]["command"] == "uvx"
    assert merged["mcpServers"]["cineforge"]["env"]["CINEFORGE_HOME"] == str((tmp_path / "ws").resolve())


def test_cli_skills_list_and_install(tmp_path: Path) -> None:
    list_res = runner.invoke(app, ["skills", "list", "--json"])
    assert list_res.exit_code == 0, list_res.stdout
    skills = json.loads(list_res.stdout)
    assert any(s["name"] == "cineforge" for s in skills)

    proj = tmp_path / "any-project"
    proj.mkdir()
    for target in ("agents", "claude", "cursor"):
        inst_res = runner.invoke(
            app, ["skills", "install", "--target", target, "--project-dir", str(proj)]
        )
        assert inst_res.exit_code == 0, inst_res.stdout

    assert (proj / ".agents" / "skills" / "cineforge" / "SKILL.md").is_file()
    assert (proj / ".claude" / "skills" / "cineforge" / "SKILL.md").is_file()
    assert (proj / ".claude" / "commands" / "backlot.md").is_file()
    assert (proj / ".cursor" / "rules" / "cineforge-mcp.mdc").is_file()


def test_cli_skills_install_all_stays_within_project_dir(tmp_path: Path, monkeypatch) -> None:
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    proj = tmp_path / "isolated-proj"
    proj.mkdir()
    res = runner.invoke(app, ["skills", "install", "--target", "all", "--project-dir", str(proj)])
    assert res.exit_code == 0, res.stdout
    assert (proj / ".codex" / "prompts" / "backlot.md").is_file()
    assert not (fake_home / ".codex").exists()
    assert not (fake_home / ".agents").exists()


def test_cli_doctor_prioritizes_popular_unlocks_and_tools_list_includes_reason(
    tmp_path: Path, monkeypatch
) -> None:
    ws = tmp_path / "doc-ws"
    monkeypatch.setenv("CINEFORGE_HOME", str(ws))
    monkeypatch.setenv("CINEFORGE_PROJECTS_DIR", str(ws / "projects"))
    for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "PEXELS_API_KEY"):
        monkeypatch.delenv(key, raising=False)

    res = runner.invoke(app, ["--workspace", str(ws), "doctor", "--json"])
    assert res.exit_code == 0, res.stdout
    payload = json.loads(res.stdout)
    assert "status_counts" in payload
    assert "popular_unlocks" in payload
    unlock_vars = [u["env_var"] for u in payload["popular_unlocks"]]
    assert unlock_vars[:2] == ["GEMINI_API_KEY", "PEXELS_API_KEY"]

    t_res = runner.invoke(app, ["tools", "list", "--status", "unavailable", "--json"])
    assert t_res.exit_code == 0, t_res.stdout
    tools = json.loads(t_res.stdout)
    assert tools
    assert all("reason" in t and t["reason"] for t in tools)


def test_cli_doctor_check_keys_and_env_warnings(tmp_path: Path, monkeypatch) -> None:
    ws = tmp_path / "chk-ws"
    ws.mkdir()
    (ws / ".env").write_text("FOO=bar\nFOO=baz\n", encoding="utf-8")
    monkeypatch.setenv("CINEFORGE_HOME", str(ws))
    monkeypatch.setenv("CINEFORGE_PROJECTS_DIR", str(ws / "projects"))
    monkeypatch.setenv("TTS_OFFLINE", "true")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setattr(
        "cineforge_cli.main.check_api_keys",
        lambda timeout=5.0: {
            "ElevenLabs": {
                "present": True,
                "valid": False,
                "status_code": 401,
                "env_var": "ELEVENLABS_API_KEY",
                "error": "HTTP 401",
            }
        },
    )

    res = runner.invoke(app, ["--workspace", str(ws), "doctor", "--check-keys", "--json"])
    assert res.exit_code == 0, res.stdout
    payload = json.loads(res.stdout)
    assert "key_probes" in payload
    assert payload["key_probes"]["ElevenLabs"]["status_code"] == 401
    warnings = payload.get("env_warnings") or []
    assert any("FOO" in w for w in warnings)
    assert any("TTS_OFFLINE=true" in w for w in warnings)


def test_cli_tools_info_and_pipelines_show_tables_and_json() -> None:
    # Default view is structured Rich panels/tables (not raw JSON)
    info_res = runner.invoke(app, ["tools", "info", "edge_tts"])
    assert info_res.exit_code == 0, info_res.stdout
    assert "Tool Info: edge_tts" in info_res.stdout
    assert "Input Parameters" in info_res.stdout
    assert "Capabilities & Guidance" in info_res.stdout
    assert "cineforge[tts-local]" in info_res.stdout

    # --json preserves machine-readable JSON output
    info_json = runner.invoke(app, ["tools", "info", "edge_tts", "--json"])
    assert info_json.exit_code == 0, info_json.stdout
    parsed = json.loads(info_json.stdout)
    assert parsed["name"] == "edge_tts"
    assert "text" in parsed["input_schema"]["properties"]

    pipe_res = runner.invoke(app, ["pipelines", "show", "animated-explainer"])
    assert pipe_res.exit_code == 0, pipe_res.stdout
    assert "Pipeline: animated-explainer" in pipe_res.stdout
    assert "Production Stages" in pipe_res.stdout

    pipe_json = runner.invoke(app, ["pipelines", "show", "animated-explainer", "--json"])
    assert pipe_json.exit_code == 0, pipe_json.stdout
    p_parsed = json.loads(pipe_json.stdout)
    assert p_parsed["name"] == "animated-explainer"
    assert p_parsed["stages"]


def test_cli_mcp_detect_and_interactive_install(tmp_path: Path, monkeypatch) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    proj = tmp_path / "proj"
    proj.mkdir()
    ws = tmp_path / "ws"
    ws.mkdir()

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    monkeypatch.setattr("cineforge_mcp.installer.platform.system", lambda: "Linux")
    monkeypatch.setattr("cineforge_mcp.installer.shutil.which", lambda _name: None)

    (fake_home / ".config" / "opencode").mkdir(parents=True)
    (fake_home / ".config" / "Code" / "User").mkdir(parents=True)

    # 1. `cineforge mcp detect` table and JSON
    detect_tbl = runner.invoke(app, ["mcp", "detect", "--project-dir", str(proj)])
    assert detect_tbl.exit_code == 0, detect_tbl.stdout
    assert "Detected IDEs & MCP Clients" in detect_tbl.stdout
    assert "OpenCode" in detect_tbl.stdout

    detect_json = runner.invoke(app, ["mcp", "detect", "--project-dir", str(proj), "--json"])
    assert detect_json.exit_code == 0, detect_json.stdout
    rows = json.loads(detect_json.stdout)
    by_id = {r["client"]: r for r in rows}
    assert by_id["vscode"]["installed"] is True
    assert by_id["opencode"]["installed"] is True
    assert by_id["claude"]["installed"] is False

    # 2. Interactive `cineforge mcp install` selecting vscode + opencode globally, decline skills
    interactive_res = runner.invoke(
        app,
        ["mcp", "install", "--workspace", str(ws), "--project-dir", str(proj), "--uvx"],
        input="vscode,opencode\nglobal\nn\n",
    )
    assert interactive_res.exit_code == 0, interactive_res.stdout
    assert "Configured vscode (global)" in interactive_res.stdout
    assert "Configured opencode (global)" in interactive_res.stdout
    assert (fake_home / ".config" / "Code" / "User" / "mcp.json").is_file()
    assert (fake_home / ".config" / "opencode" / "opencode.json").is_file()

    # 3. Interactive `cineforge mcp install` abort with 'none'
    abort_res = runner.invoke(
        app,
        ["mcp", "install", "--project-dir", str(proj)],
        input="none\n",
    )
    assert abort_res.exit_code == 0, abort_res.stdout
    assert "No MCP client selected." in abort_res.stdout

    # 4. Non-interactive `--client detected --dry-run`
    dry_res = runner.invoke(
        app,
        ["mcp", "install", "--client", "detected", "--scope", "global", "--project-dir", str(proj), "--dry-run"],
    )
    assert dry_res.exit_code == 0, dry_res.stdout
    assert "Would update vscode (global)" in dry_res.stdout
    assert "Would update opencode (global)" in dry_res.stdout

    # 5. `cineforge mcp config --client codex --uvx` prints TOML
    codex_cfg = runner.invoke(app, ["mcp", "config", "--client", "codex", "--uvx"])
    assert codex_cfg.exit_code == 0, codex_cfg.stdout
    assert "[mcp_servers.cineforge]" in codex_cfg.stdout
