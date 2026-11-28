"""Self-update and workspace/environment repair helpers for the CineForge CLI."""

from __future__ import annotations

import importlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional
from urllib import request as _urllib_request

from cineforge_cli import __version__
from cineforge_cli.core import (
    _pip_install_packages,
    find_executable,
    setup_remotion_workspace,
    warm_hyperframes_cache,
)
from lib.env_loader import load_env
from lib.paths import (
    ensure_workspace_initialized,
    get_backlot_state_dir,
    get_package_root,
    get_projects_dir,
    get_remotion_composer_dir,
    get_remotion_template_dir,
    get_workspace_root,
)

try:  # Python 3.11+ stdlib
    import tomllib  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - Python 3.10 fallback
    tomllib = None  # type: ignore[assignment]

PYPI_PACKAGE_JSON_URL = "https://pypi.org/pypi/cineforge/json"
_ANSI_ESC_RE = re.compile(r"\x1b\[20[01]~|\x1b\[[0-9;?]*[ -/]*[@-~]")
_CORE_IMPORT_MODULES = (
    ("yaml", "pyyaml"),
    ("pydantic", "pydantic"),
    ("jsonschema", "jsonschema"),
    ("dotenv", "python-dotenv"),
    ("PIL", "Pillow"),
    ("numpy", "numpy"),
    ("requests", "requests"),
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("typer", "typer"),
    ("rich", "rich"),
    ("mcp", "mcp"),
)


def _version_key(raw: str) -> tuple[int, ...]:
    """Convert dotted/prerelease version strings cleanly for comparison."""
    nums = [int(part) for part in re.findall(r"\d+", raw or "")]
    return tuple(nums) if nums else (0,)


def _parse_uv_receipt(prefix: Path) -> dict[str, Any]:
    """Read uv tool metadata (`uv-receipt.toml`) if running inside a uv tool environment."""
    receipt_path = prefix / "uv-receipt.toml"
    if not receipt_path.is_file():
        return {}
    raw = receipt_path.read_text(encoding="utf-8", errors="replace")
    if tomllib is not None:
        try:
            loaded = tomllib.loads(raw)
        except Exception:
            return {}
        reqs = ((loaded.get("tool") or {}).get("requirements") or [])
        for req in reqs:
            if isinstance(req, dict) and req.get("name", "").lower() == "cineforge":
                return dict(req)
        return dict(reqs[0]) if reqs and isinstance(reqs[0], dict) else {}

    # Python 3.10 fallback parser for simple uv-receipt lines
    info: dict[str, Any] = {}
    dir_m = re.search(r'directory\s*=\s*"([^"]+)"', raw)
    if dir_m:
        info["directory"] = dir_m.group(1)
    if re.search(r"editable\s*=\s*true", raw, re.IGNORECASE):
        info["editable"] = True
    return info


def detect_install_info() -> dict[str, Any]:
    """Detect how CineForge is currently installed (uv-tool, git-editable, or pip-venv)."""
    prefix = Path(sys.prefix).resolve()
    pkg_root = get_package_root().resolve()
    uv_exe = find_executable("uv")
    receipt = _parse_uv_receipt(prefix)

    direct_url_data: dict[str, Any] = {}
    try:
        dist = importlib.metadata.distribution("cineforge")
        du = dist.read_text("direct_url.json")
        if du:
            parsed = json.loads(du)
            if isinstance(parsed, dict):
                direct_url_data = parsed
    except Exception:
        pass

    is_uv_tool = (prefix / "uv-receipt.toml").is_file() or ("uv" in prefix.parts and "tools" in prefix.parts)
    source_dir: Optional[Path] = None
    if receipt.get("directory"):
        source_dir = Path(str(receipt["directory"])).expanduser().resolve()
    elif direct_url_data.get("url", "").startswith("file://"):
        from urllib.parse import unquote, urlsplit

        source_dir = Path(unquote(urlsplit(direct_url_data["url"]).path)).resolve()
    elif (pkg_root / ".git").exists() and (pkg_root / "pyproject.toml").is_file():
        source_dir = pkg_root

    is_git = bool(source_dir and (source_dir / ".git").exists())
    if is_uv_tool:
        mode = "uv-tool-local" if source_dir else "uv-tool-pypi"
    elif is_git:
        mode = "git-editable"
    else:
        mode = "pip-venv"

    return {
        "mode": mode,
        "current_version": __version__,
        "python_executable": sys.executable,
        "prefix": str(prefix),
        "package_root": str(pkg_root),
        "source_dir": str(source_dir) if source_dir else None,
        "is_git_repo": is_git,
        "uv_available": bool(uv_exe),
        "uv_path": uv_exe,
        "editable": bool(
            receipt.get("editable")
            or (direct_url_data.get("dir_info") or {}).get("editable")
            or mode == "git-editable"
        ),
    }


def fetch_latest_pypi_version(timeout: float = 5.0) -> dict[str, Any]:
    """Fetch the latest published CineForge release metadata from PyPI safely."""
    try:
        req = _urllib_request.Request(
            PYPI_PACKAGE_JSON_URL,
            headers={"Accept": "application/json", "User-Agent": f"cineforge/{__version__}"},
        )
        with _urllib_request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
        latest = str((payload.get("info") or {}).get("version") or "").strip() or None
        update_available = bool(latest and _version_key(latest) > _version_key(__version__))
        return {
            "ok": True,
            "current_version": __version__,
            "latest_version": latest,
            "update_available": update_available,
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "current_version": __version__,
            "latest_version": None,
            "update_available": None,
            "error": str(exc),
        }


def _git_is_dirty(repo_dir: Path) -> Optional[bool]:
    git_cmd = find_executable("git")
    if not git_cmd:
        return None
    proc = subprocess.run(
        [git_cmd, "status", "--porcelain"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if proc.returncode != 0:
        return None
    return bool(proc.stdout.strip())


def _run_step_cmd(cmd: list[str], *, cwd: Optional[Path] = None, timeout: int = 300) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    return {
        "command": cmd,
        "cwd": str(cwd) if cwd else None,
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout": out[-1000:] if out else "",
        "stderr": err[-1000:] if err else "",
    }


def _build_package_upgrade_commands(
    install_info: dict[str, Any],
    *,
    from_pypi: bool = False,
    extras: Optional[str] = None,
) -> tuple[list[tuple[list[str], Optional[Path], str]], list[str]]:
    """Return ``(commands_to_run, warnings)`` for upgrading CineForge cleanly."""
    mode = install_info["mode"]
    uv_path = install_info.get("uv_path") or find_executable("uv")
    source_dir = Path(install_info["source_dir"]) if install_info.get("source_dir") else None
    warnings: list[str] = []
    cmds: list[tuple[list[str], Optional[Path], str]] = []

    clean_extras = extras.strip() if extras and extras.strip() else None
    pypi_spec = f"cineforge[{clean_extras}]" if clean_extras else "cineforge"

    if mode in ("uv-tool-local", "git-editable") and not from_pypi and source_dir and source_dir.is_dir():
        if (source_dir / ".git").exists():
            dirty = _git_is_dirty(source_dir)
            git_cmd = find_executable("git")
            if dirty is True:
                warnings.append(
                    f"Repository at {source_dir} has uncommitted changes; skipping `git pull --ff-only`."
                )
            elif git_cmd:
                cmds.append(([git_cmd, "pull", "--ff-only"], source_dir, f"Pull latest changes in {source_dir}"))

        local_spec = f"{source_dir}[{clean_extras}]" if clean_extras else str(source_dir)
        if mode == "uv-tool-local" and uv_path:
            tool_cmd = [uv_path, "tool", "install", "--force"]
            if install_info.get("editable"):
                tool_cmd.append("--editable")
            tool_cmd.append(local_spec)
            cmds.append((tool_cmd, None, "Reinstall CineForge uv tool from local checkout"))
        else:
            if importlib.util.find_spec("pip") is not None:
                cmds.append(
                    ([sys.executable, "-m", "pip", "install", "--upgrade", "--editable", local_spec], None, "Refresh editable install via pip")
                )
            elif uv_path:
                cmds.append(
                    ([uv_path, "pip", "install", "--python", sys.executable, "--upgrade", "--editable", local_spec], None, "Refresh editable install via uv pip")
                )
        return cmds, warnings

    # PyPI / wheel / fallback installs
    if (mode.startswith("uv-tool") or from_pypi and mode == "uv-tool-local") and uv_path:
        if clean_extras or from_pypi:
            cmds.append(([uv_path, "tool", "install", "--force", "--upgrade", pypi_spec], None, f"Upgrade {pypi_spec} via uv tool"))
        else:
            cmds.append(([uv_path, "tool", "upgrade", "cineforge"], None, "Upgrade cineforge via uv tool"))
        return cmds, warnings

    if importlib.util.find_spec("pip") is not None:
        cmds.append(([sys.executable, "-m", "pip", "install", "--upgrade", pypi_spec], None, f"Upgrade {pypi_spec} via pip"))
    elif uv_path:
        cmds.append(([uv_path, "pip", "install", "--python", sys.executable, "--upgrade", pypi_spec], None, f"Upgrade {pypi_spec} via uv pip"))
    else:
        warnings.append("Neither `pip` nor `uv` is available to upgrade packages automatically.")
    return cmds, warnings


def _sync_installed_skills(*, project_dir: Optional[Path] = None, dry_run: bool = False) -> list[dict[str, Any]]:
    """Refresh agent skills in target folders where CineForge skills are already installed."""
    from cineforge_cli.skills_installer import install_skills

    home = Path.home()
    proj = (project_dir or Path.cwd()).resolve()
    candidates = [
        ("agents", True, home / ".agents" / "skills" / "cineforge"),
        ("claude", True, home / ".claude" / "skills" / "cineforge"),
        ("cursor", True, home / ".cursor" / "skills" / "cineforge"),
        ("codex", True, home / ".codex" / "skills" / "cineforge"),
        ("antigravity", True, home / ".gemini" / "antigravity" / "skills" / "cineforge"),
        ("agents", False, proj / ".agents" / "skills" / "cineforge"),
        ("claude", False, proj / ".claude" / "skills" / "cineforge"),
        ("cursor", False, proj / ".cursor" / "skills" / "cineforge"),
        ("codex", False, proj / ".codex" / "skills" / "cineforge"),
        ("antigravity", False, proj / ".gemini" / "antigravity" / "skills" / "cineforge"),
    ]
    synced: list[dict[str, Any]] = []
    for target, is_global, marker in candidates:
        if not marker.is_dir():
            continue
        if dry_run:
            synced.append({"target": target, "scope": "global" if is_global else "project", "status": "would_sync", "files": 0})
            continue
        written = install_skills(target, project_dir=proj, global_install=is_global)
        total = sum(len(v) for v in written.values())
        synced.append({"target": target, "scope": "global" if is_global else "project", "status": "synced", "files": total})
    return synced


def run_update(
    *,
    workspace: Optional[Path] = None,
    project_dir: Optional[Path] = None,
    check_only: bool = False,
    from_pypi: bool = False,
    extras: Optional[str] = None,
    sync_mcp: bool = False,
    sync_skills: bool = False,
    with_remotion: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Check and apply CineForge package, workspace template, MCP, and skill updates."""
    ws = ensure_workspace_initialized(workspace)
    install_info = detect_install_info()
    pypi = fetch_latest_pypi_version()
    planned_cmds, warnings = _build_package_upgrade_commands(
        install_info,
        from_pypi=from_pypi,
        extras=extras,
    )

    executed: list[dict[str, Any]] = []
    success = True

    if check_only or dry_run:
        for cmd, cwd, desc in planned_cmds:
            executed.append({"description": desc, "command": cmd, "cwd": str(cwd) if cwd else None, "status": "planned"})
    else:
        for cmd, cwd, desc in planned_cmds:
            res = _run_step_cmd(cmd, cwd=cwd)
            res["description"] = desc
            res["status"] = "ok" if res["ok"] else "failed"
            executed.append(res)
            if not res["ok"]:
                success = False
                break

    mcp_sync_results: list[dict[str, Any]] = []
    if sync_mcp and success:
        mcp_rep = repair_mcp_configs(ws, project_dir=project_dir, dry_run=(check_only or dry_run), force_sync=True)
        mcp_sync_results = mcp_rep.get("actions", [])

    skills_sync_results: list[dict[str, Any]] = []
    if sync_skills and success:
        skills_sync_results = _sync_installed_skills(project_dir=project_dir, dry_run=(check_only or dry_run))

    remotion_result: Optional[dict[str, Any]] = None
    if with_remotion and success:
        if check_only or dry_run:
            remotion_result = {"status": "planned", "message": f"Would update/install Remotion deps in {ws / 'remotion-composer'}"}
        else:
            ok_rem, msg_rem = setup_remotion_workspace(ws, install_deps=True)
            remotion_result = {"status": "ok" if ok_rem else "failed", "message": msg_rem}
            if not ok_rem:
                success = False

    return {
        "success": success,
        "mode": "check" if check_only else ("dry-run" if dry_run else "apply"),
        "workspace": str(ws),
        "install": install_info,
        "pypi": pypi,
        "warnings": warnings,
        "steps": executed,
        "mcp_sync": mcp_sync_results,
        "skills_sync": skills_sync_results,
        "remotion": remotion_result,
    }


# ---------------------------------------------------------------------------
# Workspace & environment repair
# ---------------------------------------------------------------------------


def repair_workspace_layout(ws: Path, *, dry_run: bool = False) -> list[dict[str, Any]]:
    """Verify workspace directories, config.yaml validity, and remove stale lock/temp files."""
    actions: list[dict[str, Any]] = []
    required_dirs = (
        ws / ".cineforge",
        ws / "projects",
        ws / "music_library",
        ws / ".backlot",
    )
    missing_dirs = [d for d in required_dirs if not d.is_dir()]
    if missing_dirs:
        if dry_run:
            actions.append(
                {
                    "component": "workspace_dirs",
                    "status": "needs_repair",
                    "action": f"Would create {len(missing_dirs)} missing workspace dir(s)",
                    "backup": None,
                }
            )
        else:
            ensure_workspace_initialized(ws)
            actions.append(
                {
                    "component": "workspace_dirs",
                    "status": "repaired",
                    "action": f"Created {len(missing_dirs)} missing workspace dir(s)",
                    "backup": None,
                }
            )
    else:
        actions.append({"component": "workspace_dirs", "status": "ok", "action": "All workspace directories present", "backup": None})

    # Validate config.yaml
    cfg_path = ws / "config.yaml"
    pkg_cfg = get_package_root() / "config.yaml"
    if not cfg_path.is_file():
        if pkg_cfg.is_file():
            if dry_run:
                actions.append({"component": "config.yaml", "status": "needs_repair", "action": "Would restore missing config.yaml", "backup": None})
            else:
                shutil.copy2(pkg_cfg, cfg_path)
                actions.append({"component": "config.yaml", "status": "repaired", "action": "Restored missing config.yaml from defaults", "backup": None})
    else:
        import yaml

        cfg_ok = True
        try:
            loaded = yaml.safe_load(cfg_path.read_text(encoding="utf-8", errors="replace"))
            if loaded is None or not isinstance(loaded, dict):
                cfg_ok = False
        except Exception:
            cfg_ok = False
        if not cfg_ok and pkg_cfg.is_file():
            bak_path = cfg_path.with_suffix(".yaml.bak")
            if dry_run:
                actions.append({"component": "config.yaml", "status": "needs_repair", "action": f"Would back up malformed config.yaml -> {bak_path.name} and restore defaults", "backup": str(bak_path)})
            else:
                shutil.copy2(cfg_path, bak_path)
                shutil.copy2(pkg_cfg, cfg_path)
                actions.append({"component": "config.yaml", "status": "repaired", "action": "Restored valid config.yaml defaults", "backup": str(bak_path)})
        else:
            actions.append({"component": "config.yaml", "status": "ok", "action": "Valid YAML mapping", "backup": None})

    # Clean stale .backlot locks and crashed partial mux temp files inside projects/
    stale_files: list[Path] = []
    backlot_dir = ws / ".backlot"
    if backlot_dir.is_dir():
        stale_files.extend(p for p in backlot_dir.glob("*.lock") if p.is_file())
    projects_dir = ws / "projects"
    if projects_dir.is_dir():
        stale_files.extend(p for p in projects_dir.rglob(".*.audio-mux-*.mp4") if p.is_file())
        stale_files.extend(p for p in projects_dir.rglob("*.tmp") if p.is_file())

    if stale_files:
        if dry_run:
            actions.append({"component": "stale_temp_files", "status": "needs_repair", "action": f"Would remove {len(stale_files)} stale lock/temp file(s)", "backup": None})
        else:
            removed = 0
            for sf in stale_files:
                try:
                    sf.unlink()
                    removed += 1
                except OSError:
                    pass
            actions.append({"component": "stale_temp_files", "status": "repaired", "action": f"Removed {removed} stale lock/temp file(s)", "backup": None})
    else:
        actions.append({"component": "stale_temp_files", "status": "ok", "action": "No stale locks or temp files found", "backup": None})

    return actions


def repair_env_file(ws: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Deduplicate active keys and clean CRLF/ANSI artifacts in ``<ws>/.env`` safely."""
    env_path = ws / ".env"
    if not env_path.is_file():
        pkg_env_ex = get_package_root() / ".env.example"
        if pkg_env_ex.is_file():
            if dry_run:
                return {"component": "env_file", "status": "needs_repair", "action": "Would initialize missing .env from .env.example", "backup": None}
            shutil.copy2(pkg_env_ex, env_path)
            return {"component": "env_file", "status": "repaired", "action": "Created missing .env from .env.example", "backup": None}
        return {"component": "env_file", "status": "ok", "action": "No .env present", "backup": None}

    raw_bytes = env_path.read_bytes()
    has_crlf = b"\r\n" in raw_bytes
    raw_text = raw_bytes.decode("utf-8", errors="replace").replace("\r\n", "\n")
    has_ansi = bool(_ANSI_ESC_RE.search(raw_text))

    lines = raw_text.splitlines()
    # First pass: locate the last index of every active key so duplicates keep latest non-empty value.
    last_value_for_key: dict[str, str] = {}
    key_counts: dict[str, int] = {}
    parsed_entries: list[tuple[Optional[str], str]] = []

    for line in lines:
        cleaned_line = _ANSI_ESC_RE.sub("", line)
        stripped = cleaned_line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k, _, v = stripped.partition("=")
            key = k.strip()
            val = v.strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                val = val[1:-1]
            if key:
                key_counts[key] = key_counts.get(key, 0) + 1
                if val or key not in last_value_for_key:
                    last_value_for_key[key] = val
                parsed_entries.append((key, f"{key}={val}"))
                continue
        parsed_entries.append((None, cleaned_line))

    dup_keys = sorted(k for k, cnt in key_counts.items() if cnt > 1)
    if not dup_keys and not has_crlf and not has_ansi:
        return {"component": "env_file", "status": "ok", "action": ".env is clean (no duplicates or encoding issues)", "backup": None}

    # Rebuild keeping comments and placing each key once at its latest position with normalized value.
    last_idx_for_key: dict[str, int] = {}
    for idx, (k, _txt) in enumerate(parsed_entries):
        if k:
            last_idx_for_key[k] = idx

    out_lines: list[str] = []
    for idx, (k, txt) in enumerate(parsed_entries):
        if k is None:
            out_lines.append(txt)
        elif idx == last_idx_for_key[k]:
            out_lines.append(f"{k}={last_value_for_key[k]}")

    details = []
    if dup_keys:
        details.append(f"deduplicated {', '.join(dup_keys)}")
    if has_crlf:
        details.append("normalized CRLF")
    if has_ansi:
        details.append("stripped ANSI escapes")

    bak_path = env_path.with_name(".env.bak")
    if dry_run:
        return {
            "component": "env_file",
            "status": "needs_repair",
            "action": f"Would clean .env ({'; '.join(details)})",
            "backup": str(bak_path),
        }

    shutil.copy2(env_path, bak_path)
    env_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    load_env(ws)
    return {
        "component": "env_file",
        "status": "repaired",
        "action": f"Cleaned .env ({'; '.join(details)})",
        "backup": str(bak_path),
    }


def repair_remotion_runtime(ws: Path, *, force_reinstall: bool = False, dry_run: bool = False) -> dict[str, Any]:
    """Repair missing Remotion template files or incomplete ``node_modules``."""
    composer_dir = get_remotion_composer_dir()
    template_dir = get_remotion_template_dir()
    has_npm = bool(find_executable("npm.cmd", "npm", "npm.exe"))
    has_pkg = (composer_dir / "package.json").is_file() and (composer_dir / "src").is_dir()
    has_modules = (composer_dir / "node_modules" / "@remotion").is_dir() or (composer_dir / "node_modules" / "remotion").is_dir()

    if has_pkg and has_modules and not force_reinstall:
        return {"component": "remotion", "status": "ok", "action": f"Ready at {composer_dir}", "backup": None}

    if not template_dir.is_dir():
        return {"component": "remotion", "status": "skipped", "action": f"Template missing at {template_dir}", "backup": None}

    if dry_run:
        need_npm = force_reinstall or not has_modules
        action_msg = (
            f"Would restore Remotion files in {composer_dir}"
            + (" and run `npm install`" if need_npm and has_npm else "")
        )
        return {"component": "remotion", "status": "needs_repair", "action": action_msg, "backup": None}

    need_install = force_reinstall or ((composer_dir / "node_modules").is_dir() and not has_modules)
    if not has_pkg or need_install or force_reinstall:
        ok, msg = setup_remotion_workspace(ws, install_deps=(need_install and has_npm))
        return {"component": "remotion", "status": "repaired" if ok else "failed", "action": msg, "backup": None}

    return {
        "component": "remotion",
        "status": "ok",
        "action": "Remotion template present (optional ~700MB npm install not forced; pass --remotion or run `cineforge setup --with-remotion`)",
        "backup": None,
    }


def repair_hyperframes_runtime(*, dry_run: bool = False) -> dict[str, Any]:
    """Verify HyperFrames runtime and warm its npx cache if needed."""
    from tools.tool_registry import registry

    registry.ensure_discovered()
    hf = registry.get("hyperframes_compose")
    if hf is None or not hasattr(hf, "_runtime_check"):
        return {"component": "hyperframes", "status": "skipped", "action": "hyperframes_compose tool unavailable", "backup": None}

    check = hf._runtime_check()
    if check.get("runtime_available"):
        return {"component": "hyperframes", "status": "ok", "action": "HyperFrames CLI & dependencies ready", "backup": None}

    if not (find_executable("npx.cmd", "npx", "npx.exe") and find_executable("ffmpeg")):
        reasons = "; ".join(str(r) for r in (check.get("reasons") or ["Missing Node >= 22 or FFmpeg"]))
        return {"component": "hyperframes", "status": "skipped", "action": reasons, "backup": None}

    if dry_run:
        return {"component": "hyperframes", "status": "needs_repair", "action": "Would warm npx hyperframes cache", "backup": None}

    ok, msg = warm_hyperframes_cache()
    return {"component": "hyperframes", "status": "repaired" if ok else "failed", "action": msg, "backup": None}


def repair_mcp_configs(
    ws: Path,
    *,
    project_dir: Optional[Path] = None,
    dry_run: bool = False,
    force_sync: bool = False,
) -> dict[str, Any]:
    """Repair broken or workspace-mismatched CineForge MCP entries across configured IDEs."""
    from cineforge_mcp.installer import inspect_configured_mcp_entries, install_mcp_config

    entries = inspect_configured_mcp_entries(
        project_dir=project_dir,
        expected_workspace=(ws if force_sync else None),
    )
    if not entries:
        return {
            "component": "mcp_configs",
            "actions": [{"component": "mcp_configs", "status": "ok", "action": "No existing CineForge MCP entries configured", "backup": None}],
        }

    targets = [e for e in entries if e["needs_repair"] or force_sync]
    if not targets:
        return {
            "component": "mcp_configs",
            "actions": [
                {
                    "component": f"mcp:{e['client']}({e['scope']})",
                    "status": "ok",
                    "action": f"Healthy ({e['config_path']})",
                    "backup": None,
                }
                for e in entries
            ],
        }

    actions: list[dict[str, Any]] = []
    for entry in entries:
        comp = f"mcp:{entry['client']}({entry['scope']})"
        if entry not in targets:
            actions.append({"component": comp, "status": "ok", "action": "Healthy", "backup": None})
            continue
        reason_text = "; ".join(entry["reasons"]) if entry["reasons"] else "Refresh sync"
        if dry_run:
            actions.append(
                {
                    "component": comp,
                    "status": "needs_repair",
                    "action": f"Would rewrite {entry['config_path']} ({reason_text})",
                    "backup": entry["config_path"] + ".bak",
                }
            )
            continue
        res = install_mcp_config(
            entry["client"],
            workspace=ws,
            project_dir=project_dir,
            scope=entry["scope"],
        )
        actions.append(
            {
                "component": comp,
                "status": "repaired",
                "action": f"Repaired {res['config_path']} ({reason_text})",
                "backup": res.get("backup_path"),
            }
        )
    return {"component": "mcp_configs", "actions": actions}


def repair_python_core(*, reinstall_deps: bool = False, dry_run: bool = False) -> dict[str, Any]:
    """Check core Python imports and optionally reinstall missing/requested packages."""
    missing: list[str] = []
    for mod_name, pkg_name in _CORE_IMPORT_MODULES:
        try:
            importlib.import_module(mod_name)
        except Exception:
            missing.append(pkg_name)

    if not missing and not reinstall_deps:
        return {"component": "python_deps", "status": "ok", "action": "All core Python dependencies import cleanly", "backup": None}

    pkgs = missing if missing else [pkg for _, pkg in _CORE_IMPORT_MODULES]
    if dry_run:
        return {"component": "python_deps", "status": "needs_repair", "action": f"Would install/reinstall {', '.join(pkgs)}", "backup": None}

    ok, msg = _pip_install_packages(pkgs)
    return {"component": "python_deps", "status": "repaired" if ok else "failed", "action": msg, "backup": None}


def run_repair(
    *,
    workspace: Optional[Path] = None,
    project_dir: Optional[Path] = None,
    workspace_only: bool = False,
    fix_env: bool = False,
    fix_remotion: bool = False,
    fix_hyperframes: bool = False,
    fix_mcp: bool = False,
    reinstall_deps: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run targeted or comprehensive non-destructive repairs across CineForge workspace and IDEs."""
    ws = (workspace.expanduser().resolve() if workspace else get_workspace_root())
    selective = any((workspace_only, fix_env, fix_remotion, fix_hyperframes, fix_mcp, reinstall_deps))

    actions: list[dict[str, Any]] = []
    if not selective or workspace_only:
        if ws.exists() or not dry_run:
            actions.extend(repair_workspace_layout(ws, dry_run=dry_run))
        else:
            actions.append({"component": "workspace_dirs", "status": "needs_repair", "action": f"Would initialize workspace {ws}", "backup": None})

    if not selective or fix_env or workspace_only:
        actions.append(repair_env_file(ws, dry_run=dry_run))

    if not selective or fix_remotion:
        actions.append(repair_remotion_runtime(ws, force_reinstall=fix_remotion, dry_run=dry_run))

    if not selective or fix_hyperframes:
        actions.append(repair_hyperframes_runtime(dry_run=dry_run))

    if not selective or fix_mcp:
        mcp_rep = repair_mcp_configs(ws, project_dir=project_dir, dry_run=dry_run, force_sync=False)
        actions.extend(mcp_rep["actions"])

    if not selective or reinstall_deps:
        actions.append(repair_python_core(reinstall_deps=reinstall_deps, dry_run=dry_run))

    has_failure = any(a["status"] == "failed" for a in actions)
    return {
        "success": not has_failure,
        "dry_run": dry_run,
        "workspace": str(ws),
        "actions": actions,
    }
