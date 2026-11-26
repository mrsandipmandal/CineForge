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
