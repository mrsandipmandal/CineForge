"""Auto-configurator and config snippet generator for MCP clients."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Optional

from lib.paths import get_workspace_root


SUPPORTED_CLIENTS = (
    "claude",
    "claude-code",
    "cursor",
    "antigravity",
    "windsurf",
    "vscode",
)


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
            # a virtualenv bin directory is not on Claude Desktop's GUI PATH.
            command = sys.executable
            args = ["-m", "cineforge_mcp", *extra_args]

    return {
        "command": command,
        "args": args,
        "env": {
            "CINEFORGE_HOME": str(ws),
        },
    }


def client_config_path(client: str, *, project_dir: Optional[Path] = None) -> Path:
    """Return the standard MCP configuration file path for a given client."""
    system = platform.system()
    home = Path.home()
    proj = (project_dir or Path.cwd()).resolve()

    if client == "claude":
        if system == "Darwin":
            return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        if system == "Windows":
            appdata = Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
            return appdata / "Claude" / "claude_desktop_config.json"
        return home / ".config" / "Claude" / "claude_desktop_config.json"

    if client == "claude-code":
        return proj / ".mcp.json"

    if client == "cursor":
        return home / ".cursor" / "mcp.json"

    if client == "antigravity":
        return home / ".gemini" / "antigravity" / "mcp_config.json"

    if client == "windsurf":
        return home / ".codeium" / "windsurf" / "mcp_config.json"

    if client == "vscode":
        return proj / ".vscode" / "mcp.json"

    raise ValueError(f"Unsupported client {client!r}. Choose from: {', '.join(SUPPORTED_CLIENTS)}")


def build_client_payload(client: str, server_spec: dict[str, Any], server_name: str = "cineforge") -> dict[str, Any]:
    """Wrap server_spec in the JSON structure expected by the target MCP client."""
    if client == "vscode":
        return {
            "servers": {
                server_name: {
                    "type": "stdio",
                    **server_spec,
                }
            }
        }
    return {
        "mcpServers": {
            server_name: server_spec,
        }
    }


def install_mcp_config(
    client: str,
    *,
    workspace: Optional[Path] = None,
    project_dir: Optional[Path] = None,
    server_name: str = "cineforge",
    all_tools: bool = False,
    profile: Optional[str] = None,
    use_uvx: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Merge the CineForge MCP entry into a client's config file with a backup."""
    config_path = client_config_path(client, project_dir=project_dir)
    spec = resolve_mcp_launch_spec(
        workspace=workspace,
        all_tools=all_tools,
        profile=profile,
        use_uvx=use_uvx,
    )
    root_key = "servers" if client == "vscode" else "mcpServers"
    entry_value = {"type": "stdio", **spec} if client == "vscode" else spec

    existing: dict[str, Any] = {}
    if config_path.is_file():
        raw_text = config_path.read_text(encoding="utf-8").strip()
        if raw_text:
            try:
                loaded = json.loads(raw_text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Existing config at {config_path} is not valid JSON: {exc}") from exc
            if not isinstance(loaded, dict):
                raise ValueError(f"Existing config at {config_path} must be a JSON object.")
            existing = loaded

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

    backup_path: Optional[Path] = None
    if not dry_run:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if config_path.is_file():
            backup_path = config_path.with_suffix(config_path.suffix + ".bak")
            shutil.copy2(config_path, backup_path)
        config_path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")

    return {
        "client": client,
        "config_path": str(config_path),
        "backup_path": str(backup_path) if backup_path else None,
        "dry_run": dry_run,
        "entry": {root_key: {server_name: entry_value}},
    }
