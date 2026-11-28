"""Tests for the CineForge Typer CLI and MCP config installer."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from cineforge_cli.main import app
from cineforge_mcp.installer import install_mcp_config

runner = CliRunner()


def test_cli_version_and_help() -> None:
    for flag in ("--version", "-V", "-v"):
        res = runner.invoke(app, [flag])
        assert res.exit_code == 0, flag
        assert "cineforge" in res.stdout

    help_res = runner.invoke(app, ["--help"])
    assert help_res.exit_code == 0
    for cmd in ("init", "setup", "doctor", "studio", "demo", "tools", "pipelines", "mcp", "update", "repair"):
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


def test_cli_setup_pasted_keys_and_pty_masked_echo(tmp_path: Path, monkeypatch) -> None:
    import os
    import pty
    import select
    import subprocess
    import sys

    from cineforge_cli.core import POPULAR_API_KEYS, load_all_env_var_specs
    from cineforge_cli.main import _mask_secret_preview, _normalize_pasted_key

    # 1. Normalization, preview & catalog helpers
    assert _normalize_pasted_key('\x1b[200~"AIzaTestSecret9876"\x1b[201~', "GEMINI_API_KEY") == "AIzaTestSecret9876"
    assert _normalize_pasted_key("export GEMINI_API_KEY='AIzaXYZ'", "GEMINI_API_KEY") == "AIzaXYZ"
    assert _mask_secret_preview("AIzaTestSecret9876") == "AIza••••9876 (18 chars)"
    assert _mask_secret_preview("short") == "***** (5 chars)"

    all_specs = load_all_env_var_specs()
    spec_names = [s["name"] for s in all_specs]
    assert len(spec_names) == len(set(spec_names))
    assert len(spec_names) >= 95
    for expected_var in (
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "KLING_API_KEY",
        "MINIMAX_REGION",
        "REPLICATE_API_TOKEN",
        "HIGGSFIELD_KEY",
        "FREESOUND_API_KEY",
        "BFL_API_KEY",
        "TTS_OFFLINE",
        "BACKLOT_PORT",
        "NVIDIA_NIM_API_KEY",
        "NVIDIA_API_KEY",
    ):
        assert expected_var in spec_names

    # 2. Full interactive `cineforge setup` iterates ALL .env variables one by one
    ws = tmp_path / "setup-ws"
    for var_name in spec_names:
        monkeypatch.delenv(var_name, raising=False)
    monkeypatch.setattr("cineforge_mcp.installer.detect_mcp_clients", lambda project_dir=None: [])

    answers_map = {
        "GEMINI_API_KEY": 'GEMINI_API_KEY="test_gemini_111111111"',
        "KLING_API_KEY": "test_kling_1111111111",
        "FREESOUND_API_KEY": "test_free_1111111111",
    }
    responses = [answers_map.get(name, "") for name in spec_names] + ["n", "n", "n"]
    res = runner.invoke(app, ["--workspace", str(ws), "setup"], input="\n".join(responses) + "\n")
    assert res.exit_code == 0, res.stdout
    assert f"Environment Variables & API Keys ({len(spec_names)} total)" in res.stdout
    assert "── Kling official direct API ──" in res.stdout
    assert "── Additional Stock Media Sources ──" in res.stdout
    assert "[current: global, Enter to keep]" in res.stdout
    assert "✓ Captured GEMINI_API_KEY (test••••1111 (21 chars))" in res.stdout
    assert "✓ Captured KLING_API_KEY (test••••1111 (21 chars))" in res.stdout
    assert "✓ Captured FREESOUND_API_KEY (test••••1111 (20 chars))" in res.stdout
    env_text = (ws / ".env").read_text(encoding="utf-8")
    assert "GEMINI_API_KEY=test_gemini_111111111" in env_text
    assert "KLING_API_KEY=test_kling_1111111111" in env_text
    assert "FREESOUND_API_KEY=test_free_1111111111" in env_text
    assert "# FREESOUND_API_KEY=" not in env_text
    assert "MINIMAX_REGION=global" in env_text

    # 3. Re-running setup allows updating an already-set key, keeping others via Enter, or stopping early with :done
    rerun = runner.invoke(
        app,
        ["--workspace", str(ws), "setup", "--keys-only"],
        input="test_gemini_222222222\n:done\n",
    )
    assert rerun.exit_code == 0, rerun.stdout
    assert "[set: test••••1111 (21 chars), Enter to keep]" in rerun.stdout
    assert "Finished key entry." in rerun.stdout
    updated_env = (ws / ".env").read_text(encoding="utf-8")
    assert updated_env.count("GEMINI_API_KEY=") == 1
    assert "GEMINI_API_KEY=test_gemini_222222222" in updated_env
    assert "KLING_API_KEY=test_kling_1111111111" in updated_env

    # 4. --popular-only prompts only the 9 popular keys and --skip-keys bypasses key prompts
    pop_ws = tmp_path / "pop-ws"
    for key_name, _, _ in POPULAR_API_KEYS:
        monkeypatch.delenv(key_name, raising=False)
    pop_res = runner.invoke(
        app,
        ["--workspace", str(pop_ws), "setup", "--popular-only", "--keys-only"],
        input="test_pop_111111111\n" + "\n" * (len(POPULAR_API_KEYS) - 1),
    )
    assert pop_res.exit_code == 0, pop_res.stdout
    assert f"({len(POPULAR_API_KEYS)} total)" in pop_res.stdout
    assert "GEMINI_API_KEY=test_pop_111111111" in (pop_ws / ".env").read_text(encoding="utf-8")

    skip_res = runner.invoke(app, ["--workspace", str(pop_ws), "setup", "--skip-keys"], input="n\nn\nn\n")
    assert skip_res.exit_code == 0, skip_res.stdout
    assert "Environment Variables & API Keys" not in skip_res.stdout

    # 3. Real POSIX PTY test verifying bracketed paste echoes '*' and captures value cleanly
    if os.name == "posix":
        master_fd, slave_fd = pty.openpty()
        proc = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "from cineforge_cli.main import _prompt_api_key_value; "
                "print('RESULT=' + repr(_prompt_api_key_value('  KEY', env_name='GEMINI_API_KEY')))",
            ],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
        )
        os.close(slave_fd)
        try:
            # Wait briefly for prompt, send bracketed paste + backspace + '9' + Enter
            select.select([master_fd], [], [], 2.0)
            os.write(master_fd, b"\x1b[200~AIzaPasteTestX\x1b[201~\x7f9\r")
            output = b""
            while True:
                ready, _, _ = select.select([master_fd], [], [], 2.0)
                if not ready:
                    break
                try:
                    chunk = os.read(master_fd, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                output += chunk
                if b"RESULT=" in output:
                    break
        finally:
            os.close(master_fd)
            proc.wait(timeout=5)
        decoded = output.decode("utf-8", errors="replace")
        assert "*" in decoded
        assert "RESULT='AIzaPasteTest9'" in decoded


def test_cli_error_handling_edges() -> None:
    bad_json = runner.invoke(app, ["tools", "run", "local_hardware_probe", "--input", "{bad}"])
    assert bad_json.exit_code == 1
    assert "Invalid JSON input" in bad_json.stdout

    bad_type = runner.invoke(app, ["tools", "run", "local_hardware_probe", "--input", "[1, 2]"])
    assert bad_type.exit_code == 1
    assert "JSON object" in bad_type.stdout

    missing_file = runner.invoke(app, ["tools", "run", "local_hardware_probe", "--input-file", "/tmp/no-such-file-999.json"])
    assert missing_file.exit_code == 1
    assert "Failed to read input file" in missing_file.stdout

    bad_status = runner.invoke(app, ["tools", "list", "--status", "bogus"])
    assert bad_status.exit_code == 1
    assert "Invalid --status" in bad_status.stdout

    bad_client = runner.invoke(app, ["mcp", "config", "--client", "bogus"])
    assert bad_client.exit_code == 1
    assert "Unsupported client" in bad_client.stdout

    bad_transport = runner.invoke(app, ["mcp", "run", "--transport", "bogus"])
    assert bad_transport.exit_code == 1
    assert "Unsupported MCP transport" in bad_transport.stdout
