"""Auto-detector, config snippet generator, and safe installer for MCP clients."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Optional

from lib.paths import get_workspace_root

try:  # Python 3.11+ stdlib
    import tomllib  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - Python 3.10 fallback
    tomllib = None  # type: ignore[assignment]


SUPPORTED_CLIENTS = (
    "claude",
    "claude-code",
    "cursor",
    "antigravity",
    "windsurf",
    "vscode",
    "opencode",
    "gemini-cli",
    "codex",
)

SUPPORTED_SCOPES = ("auto", "global", "project")

_CLIENT_META: dict[str, dict[str, Any]] = {
    "claude": {
        "display_name": "Claude Desktop",
        "supports_project_scope": False,
        "default_scope": "global",
        "skill_target": "claude",
    },
    "claude-code": {
        "display_name": "Claude Code",
        "supports_project_scope": True,
        "default_scope": "project",
        "skill_target": "claude",
    },
    "cursor": {
        "display_name": "Cursor",
        "supports_project_scope": True,
        "default_scope": "global",
        "skill_target": "cursor",
    },
    "antigravity": {
        "display_name": "Antigravity",
        "supports_project_scope": False,
        "default_scope": "global",
        "skill_target": "antigravity",
    },
    "windsurf": {
        "display_name": "Windsurf",
        "supports_project_scope": False,
        "default_scope": "global",
        "skill_target": "agents",
    },
    "vscode": {
        "display_name": "VS Code",
        "supports_project_scope": True,
        "default_scope": "project",
        "skill_target": "agents",
    },
    "opencode": {
        "display_name": "OpenCode",
        "supports_project_scope": True,
        "default_scope": "global",
        "skill_target": "agents",
    },
    "gemini-cli": {
        "display_name": "Gemini CLI",
        "supports_project_scope": True,
        "default_scope": "global",
        "skill_target": "agents",
    },
    "codex": {
        "display_name": "Codex CLI",
        "supports_project_scope": True,
        "default_scope": "global",
        "skill_target": "codex",
    },
}


def _platform_app_data_dir(app_dir_name: str, subpath: tuple[str, ...]) -> Path:
    """Resolve a standard OS user config path under Application Support / APPDATA / ~/.config."""
    system = platform.system()
    home = Path.home()
    if system == "Darwin":
        return home.joinpath("Library", "Application Support", app_dir_name, *subpath)
    if system == "Windows":
        appdata = Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
        return appdata.joinpath(app_dir_name, *subpath)
    return home.joinpath(".config", app_dir_name, *subpath)


def _validate_client_and_scope(client: str, scope: str) -> str:
    if client not in SUPPORTED_CLIENTS:
        raise ValueError(
            f"Unsupported client {client!r}. Choose from: {', '.join(SUPPORTED_CLIENTS)}"
        )
    if scope not in SUPPORTED_SCOPES:
        raise ValueError(
            f"Unsupported scope {scope!r}. Choose from: {', '.join(SUPPORTED_SCOPES)}"
        )
    meta = _CLIENT_META[client]
    if scope == "auto":
        return str(meta["default_scope"])
    if scope == "project" and not meta["supports_project_scope"]:
        return "global"
    return scope


def resolve_mcp_launch_spec(
    *,
    workspace: Optional[Path] = None,
    all_tools: bool = False,
    profile: Optional[str] = None,
    use_uvx: bool = False,
) -> dict[str, Any]:
    """Return the safest command/args/env entry for launching cineforge-mcp."""
    ws = workspace.expanduser().resolve() if workspace else get_workspace_root()
    extra_args: list[str] = []
    if all_tools:
        extra_args.append("--all-tools")
    if profile:
        extra_args.extend(["--profile", profile])

    if use_uvx:
        command = "uvx"
        args = ["--from", "cineforge", "cineforge-mcp", *extra_args]
    else:
        exe = shutil.which("cineforge-mcp")
        if exe:
            command = exe
            args = extra_args
        else:
            # Running directly with the active Python interpreter works even when
            # a virtualenv bin directory is not on an IDE's GUI PATH.
            command = sys.executable
            args = ["-m", "cineforge_mcp", *extra_args]

    return {
        "command": command,
        "args": args,
        "env": {
            "CINEFORGE_HOME": str(ws),
        },
    }


def client_config_path(
    client: str,
    *,
    project_dir: Optional[Path] = None,
    scope: str = "auto",
) -> Path:
    """Return the standard MCP configuration file path for a given client and scope."""
    resolved_scope = _validate_client_and_scope(client, scope)
    home = Path.home()
    proj = (project_dir or Path.cwd()).resolve()

    if client == "claude":
        return _platform_app_data_dir("Claude", ("claude_desktop_config.json",))

    if client == "claude-code":
        return (home / ".claude.json") if resolved_scope == "global" else (proj / ".mcp.json")

    if client == "cursor":
        return (home / ".cursor" / "mcp.json") if resolved_scope == "global" else (proj / ".cursor" / "mcp.json")

    if client == "antigravity":
        return home / ".gemini" / "antigravity" / "mcp_config.json"

    if client == "windsurf":
        return home / ".codeium" / "windsurf" / "mcp_config.json"

    if client == "vscode":
        if resolved_scope == "global":
            return _platform_app_data_dir("Code", ("User", "mcp.json"))
        return proj / ".vscode" / "mcp.json"

    if client == "opencode":
        if resolved_scope == "global":
            return home / ".config" / "opencode" / "opencode.json"
        return proj / "opencode.json"

    if client == "gemini-cli":
        if resolved_scope == "global":
            return home / ".gemini" / "settings.json"
        return proj / ".gemini" / "settings.json"

    if client == "codex":
        if resolved_scope == "global":
            return home / ".codex" / "config.toml"
        return proj / ".codex" / "config.toml"

    raise ValueError(f"Unsupported client {client!r}. Choose from: {', '.join(SUPPORTED_CLIENTS)}")


def build_client_payload(client: str, server_spec: dict[str, Any], server_name: str = "cineforge") -> dict[str, Any]:
    """Wrap server_spec in the config structure expected by the target MCP client."""
    if client not in SUPPORTED_CLIENTS:
        raise ValueError(
            f"Unsupported client {client!r}. Choose from: {', '.join(SUPPORTED_CLIENTS)}"
        )
    if client == "vscode":
        return {
            "servers": {
                server_name: {
                    "type": "stdio",
                    **server_spec,
                }
            }
        }
    if client == "opencode":
        cmd = [server_spec["command"], *(server_spec.get("args") or [])]
        entry: dict[str, Any] = {
            "type": "local",
            "command": cmd,
            "enabled": True,
        }
        if server_spec.get("env"):
            entry["environment"] = dict(server_spec["env"])
        return {"mcp": {server_name: entry}}
    if client == "codex":
        return {
            "mcp_servers": {
                server_name: server_spec,
            }
        }
    return {
        "mcpServers": {
            server_name: server_spec,
        }
    }


def format_client_config(
    client: str,
    server_spec: dict[str, Any],
    server_name: str = "cineforge",
) -> str:
    """Format a ready-to-paste client configuration string (TOML for Codex, JSON otherwise)."""
    if client == "codex":
        return _render_codex_server_toml(server_name, server_spec).rstrip()
    return json.dumps(build_client_payload(client, server_spec, server_name=server_name), indent=2)


def _strip_json_comments(raw: str) -> str:
    """Strip // line comments and /* ... */ block comments from JSONC while keeping strings intact."""
    out: list[str] = []
    i = 0
    n = len(raw)
    in_string = False
    escaped = False
    while i < n:
        ch = raw[i]
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
        elif ch == "/" and i + 1 < n and raw[i + 1] == "/":
            i += 2
            while i < n and raw[i] not in ("\n", "\r"):
                i += 1
        elif ch == "/" and i + 1 < n and raw[i + 1] == "*":
            i += 2
            while i + 1 < n and not (raw[i] == "*" and raw[i + 1] == "/"):
                i += 1
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _read_config_dict(path: Path, client: str) -> dict[str, Any]:
    if not path.is_file():
        return {}
    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    if not raw:
        return {}
    if client == "codex":
        if tomllib is None:
            return (
                {"mcp_servers": {"cineforge": {}}}
                if re.search(r"(?m)^\[mcp_servers\.cineforge\]\s*$", raw)
                else {}
            )
        loaded = tomllib.loads(raw)
        return loaded if isinstance(loaded, dict) else {}
    cleaned = _strip_json_comments(raw) if client == "opencode" else raw
    loaded = json.loads(cleaned)
    if not isinstance(loaded, dict):
        raise ValueError(f"Existing config at {path} must be a JSON object.")
    return loaded


def _server_is_configured(path: Path, client: str, server_name: str = "cineforge") -> bool:
    if not path.is_file():
        return False
    try:
        data = _read_config_dict(path, client)
    except Exception:
        return False
    root_key = next(iter(build_client_payload(client, {"command": "x", "args": []}).keys()))
    section = data.get(root_key)
    return isinstance(section, dict) and server_name in section


def _render_codex_server_toml(server_name: str, server_spec: dict[str, Any]) -> str:
    lines = [
        f"[mcp_servers.{server_name}]",
        f"command = {json.dumps(server_spec['command'])}",
        f"args = {json.dumps(list(server_spec.get('args') or []))}",
    ]
    env = server_spec.get("env") or {}
    if env:
        lines.append("")
        lines.append(f"[mcp_servers.{server_name}.env]")
        for k, v in env.items():
            lines.append(f"{k} = {json.dumps(str(v))}")
    return "\n".join(lines) + "\n"


def _upsert_codex_toml(existing_text: str, server_name: str, server_spec: dict[str, Any]) -> str:
    """Replace or append [mcp_servers.<server_name>] cleanly inside a Codex config.toml."""
    header_re = re.compile(
        rf"^\[mcp_servers\.{re.escape(server_name)}(?:\.[^\]]+)?\]\s*$"
    )
    any_section_re = re.compile(r"^\[[^\]]+\]\s*$")
    kept: list[str] = []
    skipping = False
    for line in existing_text.splitlines():
        stripped = line.strip()
        if any_section_re.match(stripped):
            skipping = bool(header_re.match(stripped))
        if not skipping:
            kept.append(line)
    body = "\n".join(kept).rstrip()
    block = _render_codex_server_toml(server_name, server_spec)
    return f"{body}\n\n{block}" if body else block


def detect_mcp_clients(
    *,
    project_dir: Optional[Path] = None,
    server_name: str = "cineforge",
) -> list[dict[str, Any]]:
    """Scan the system for installed IDEs/AI clients and check CineForge MCP status."""
    home = Path.home()
    proj = (project_dir or Path.cwd()).resolve()
    system = platform.system()

    claude_dir = _platform_app_data_dir("Claude", ())
    vscode_user_dir = _platform_app_data_dir("Code", ("User",))

    signals_map: dict[str, list[tuple[str, bool]]] = {
        "claude": [
            ("Claude Desktop config dir", claude_dir.is_dir()),
            ("Claude Desktop.app", system == "Darwin" and Path("/Applications/Claude.app").exists()),
        ],
        "claude-code": [
            ("`claude` CLI", bool(shutil.which("claude"))),
            ("~/.claude", (home / ".claude").is_dir()),
            ("~/.claude.json", (home / ".claude.json").is_file()),
            ("project .mcp.json", (proj / ".mcp.json").is_file()),
        ],
        "cursor": [
            ("`cursor` CLI", bool(shutil.which("cursor"))),
            ("~/.cursor", (home / ".cursor").is_dir()),
            ("Cursor config dir", _platform_app_data_dir("Cursor", ()).is_dir()),
        ],
        "antigravity": [
            ("`antigravity` CLI", bool(shutil.which("antigravity"))),
            ("~/.gemini/antigravity", (home / ".gemini" / "antigravity").is_dir()),
            ("Antigravity config dir", _platform_app_data_dir("Antigravity", ()).is_dir()),
        ],
        "windsurf": [
            ("`windsurf` CLI", bool(shutil.which("windsurf"))),
            ("~/.codeium/windsurf", (home / ".codeium" / "windsurf").is_dir()),
            ("Windsurf config dir", _platform_app_data_dir("Windsurf", ()).is_dir()),
        ],
        "vscode": [
            ("`code` CLI", bool(shutil.which("code") or shutil.which("code-insiders"))),
            ("VS Code User dir", vscode_user_dir.is_dir()),
            ("project .vscode", (proj / ".vscode").is_dir()),
        ],
        "opencode": [
            ("`opencode` CLI", bool(shutil.which("opencode") or (home / ".opencode" / "bin" / "opencode").is_file())),
            ("~/.config/opencode", (home / ".config" / "opencode").is_dir()),
        ],
        "gemini-cli": [
            ("`gemini` CLI", bool(shutil.which("gemini"))),
            ("~/.gemini/settings.json", (home / ".gemini" / "settings.json").is_file()),
        ],
        "codex": [
            ("`codex` CLI", bool(shutil.which("codex"))),
            ("~/.codex", (home / ".codex").is_dir()),
        ],
    }

    rows: list[dict[str, Any]] = []
    for client in SUPPORTED_CLIENTS:
        meta = _CLIENT_META[client]
        matched = [label for label, hit in signals_map[client] if hit]
        global_path = client_config_path(client, project_dir=proj, scope="global")
        project_path = (
            client_config_path(client, project_dir=proj, scope="project")
            if meta["supports_project_scope"]
            else None
        )

        configured_scopes: list[str] = []
        if _server_is_configured(global_path, client, server_name):
            configured_scopes.append("global")
        if project_path is not None and project_path != global_path and _server_is_configured(project_path, client, server_name):
            configured_scopes.append("project")

        rows.append(
            {
                "client": client,
                "display_name": meta["display_name"],
                "installed": bool(matched),
                "detection_reason": ", ".join(matched) if matched else "-",
                "configured": bool(configured_scopes),
                "configured_scopes": configured_scopes,
                "supports_project_scope": bool(meta["supports_project_scope"]),
                "default_scope": meta["default_scope"],
                "skill_target": meta["skill_target"],
                "config_path": str(global_path if meta["supports_project_scope"] and meta["default_scope"] == "global" else (project_path or global_path)),
                "global_config_path": str(global_path),
                "project_config_path": str(project_path) if project_path else None,
            }
        )
    return rows


def install_mcp_config(
    client: str,
    *,
    workspace: Optional[Path] = None,
    project_dir: Optional[Path] = None,
    scope: str = "auto",
    server_name: str = "cineforge",
    all_tools: bool = False,
    profile: Optional[str] = None,
    use_uvx: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Merge the CineForge MCP entry into a client's config file with a backup."""
    resolved_scope = _validate_client_and_scope(client, scope)
    config_path = client_config_path(client, project_dir=project_dir, scope=resolved_scope)
    spec = resolve_mcp_launch_spec(
        workspace=workspace,
        all_tools=all_tools,
        profile=profile,
        use_uvx=use_uvx,
    )
    payload_wrapper = build_client_payload(client, spec, server_name=server_name)
    root_key = next(iter(payload_wrapper.keys()))
    entry_value = payload_wrapper[root_key][server_name]

    if client == "codex":
        existing_text = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
        if existing_text.strip() and tomllib is not None:
            # Validate TOML before mutating it so malformed user files fail loudly.
            tomllib.loads(existing_text)
        rendered = _upsert_codex_toml(existing_text, server_name, spec)
    else:
        existing: dict[str, Any] = {}
        if config_path.is_file():
            raw_text = config_path.read_text(encoding="utf-8").strip()
            if raw_text:
                try:
                    existing = _read_config_dict(config_path, client)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Existing config at {config_path} is not valid JSON: {exc}") from exc

        updated = dict(existing)
        section = updated.get(root_key)
        if section is None:
            section = {}
        elif not isinstance(section, dict):
            raise ValueError(f"Expected {root_key!r} to be a JSON object in {config_path}")
        else:
            section = dict(section)

        section[server_name] = entry_value
        updated[root_key] = section
        rendered = json.dumps(updated, indent=2) + "\n"

    backup_path: Optional[Path] = None
    if not dry_run:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if config_path.is_file():
            backup_path = config_path.with_suffix(config_path.suffix + ".bak")
            shutil.copy2(config_path, backup_path)
        config_path.write_text(rendered, encoding="utf-8")

    return {
        "client": client,
        "scope": resolved_scope,
        "config_path": str(config_path),
        "backup_path": str(backup_path) if backup_path else None,
        "dry_run": dry_run,
        "entry": payload_wrapper,
    }


def _extract_server_fields(client: str, section_entry: dict[str, Any]) -> tuple[str, list[str], dict[str, str]]:
    """Normalize command, args, and env mapping from any supported client's MCP entry."""
    if client == "opencode":
        raw_cmd = section_entry.get("command")
        if isinstance(raw_cmd, list):
            cmd = str(raw_cmd[0]) if raw_cmd else ""
            args = [str(x) for x in raw_cmd[1:]]
        else:
            cmd = str(raw_cmd or "")
            args = []
        raw_env = section_entry.get("environment") or {}
    else:
        cmd = str(section_entry.get("command") or "")
        raw_args = section_entry.get("args") or []
        args = [str(x) for x in raw_args] if isinstance(raw_args, list) else []
        raw_env = section_entry.get("env") or {}
    env = {str(k): str(v) for k, v in raw_env.items()} if isinstance(raw_env, dict) else {}
    return cmd, args, env


def _command_is_runnable(cmd: str) -> bool:
    """Return True if *cmd* resolves on PATH or points to an existing executable file."""
    cleaned = cmd.strip()
    if not cleaned:
        return False
    p = Path(cleaned).expanduser()
    if p.is_absolute() or os.sep in cleaned or (os.altsep and os.altsep in cleaned):
        return p.is_file()
    return shutil.which(cleaned) is not None


def inspect_configured_mcp_entries(
    *,
    project_dir: Optional[Path] = None,
    expected_workspace: Optional[Path] = None,
    server_name: str = "cineforge",
) -> list[dict[str, Any]]:
    """Inspect all configured CineForge MCP client entries and flag broken paths/workspaces."""
    proj = (project_dir or Path.cwd()).resolve()
    resolved_ws = expected_workspace.expanduser().resolve() if expected_workspace else None
    findings: list[dict[str, Any]] = []

    for client in SUPPORTED_CLIENTS:
        meta = _CLIENT_META[client]
        candidates: list[tuple[str, Path]] = [
            ("global", client_config_path(client, project_dir=proj, scope="global")),
        ]
        if meta["supports_project_scope"]:
            proj_path = client_config_path(client, project_dir=proj, scope="project")
            if proj_path != candidates[0][1]:
                candidates.append(("project", proj_path))

        root_key = next(iter(build_client_payload(client, {"command": "x", "args": []}).keys()))
        for scope_name, cfg_path in candidates:
            if not cfg_path.is_file():
                continue
            try:
                data = _read_config_dict(cfg_path, client)
            except Exception as exc:
                findings.append(
                    {
                        "client": client,
                        "display_name": meta["display_name"],
                        "scope": scope_name,
                        "config_path": str(cfg_path),
                        "command": None,
                        "workspace": None,
                        "needs_repair": True,
                        "reasons": [f"Malformed config file: {exc}"],
                        "skill_target": meta["skill_target"],
                    }
                )
                continue

            section = data.get(root_key)
            if not isinstance(section, dict) or server_name not in section:
                continue
            entry = section.get(server_name)
            if not isinstance(entry, dict):
                findings.append(
                    {
                        "client": client,
                        "display_name": meta["display_name"],
                        "scope": scope_name,
                        "config_path": str(cfg_path),
                        "command": None,
                        "workspace": None,
                        "needs_repair": True,
                        "reasons": [f"Entry {server_name!r} is not a mapping"],
                        "skill_target": meta["skill_target"],
                    }
                )
                continue

            cmd, _args, env = _extract_server_fields(client, entry)
            ws_val = env.get("CINEFORGE_HOME", "")
            reasons: list[str] = []
            if not _command_is_runnable(cmd):
                reasons.append(f"Executable missing or not on PATH: {cmd or '<empty>'}")
            if ws_val:
                ws_path = Path(ws_val).expanduser()
                if not ws_path.is_dir():
                    reasons.append(f"Workspace path does not exist: {ws_val}")
                elif resolved_ws is not None and ws_path.resolve() != resolved_ws:
                    reasons.append(f"Workspace mismatch ({ws_val} != {resolved_ws})")
            elif resolved_ws is not None:
                reasons.append(f"CINEFORGE_HOME unset (expected {resolved_ws})")

            findings.append(
                {
                    "client": client,
                    "display_name": meta["display_name"],
                    "scope": scope_name,
                    "config_path": str(cfg_path),
                    "command": cmd,
                    "workspace": ws_val or None,
                    "needs_repair": bool(reasons),
                    "reasons": reasons,
                    "skill_target": meta["skill_target"],
                }
            )
    return findings
