"""Shared runtime, workspace, doctor, and demo helpers for CineForge CLI and MCP."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from lib.paths import (
    ensure_workspace_initialized,
    get_env_search_paths,
    get_package_root,
    get_projects_dir,
    get_remotion_composer_dir,
    get_remotion_template_dir,
    get_workspace_root,
)

POPULAR_API_KEYS: tuple[tuple[str, str, str], ...] = (
    ("GEMINI_API_KEY", "Google Gemini / Imagen / Veo / Lyria", "Free tier available via Google AI Studio"),
    ("PEXELS_API_KEY", "Pexels Stock Video & Images", "Free HD stock media API"),
    ("PIXABAY_API_KEY", "Pixabay Stock Media & Music", "Free stock media API"),
    ("FAL_KEY", "fal.ai (FLUX, Kling, Seedance, Wan, 3D)", "Unified multi-model media API"),
    ("ELEVENLABS_API_KEY", "ElevenLabs (TTS, SFX, Music, Voice Clone)", "Studio voice & audio API"),
    ("SARVAM_API_KEY", "Sarvam AI (Bengali bn-IN, Hindi, Indic TTS)", "Native Indian language voices"),
    ("OPENAI_API_KEY", "OpenAI (GPT Image, TTS, Sora)", "OpenAI media APIs"),
)

DEMO_DESCRIPTIONS = {
    "world-in-numbers": "Global scale story with titles, stats, and charts",
    "code-to-screen": "Developer workflow explainer with comparison and KPI cards",
    "focusflow-pitch": "Startup-style pitch built only from Remotion components",
}


def apply_workspace_override(workspace: Optional[str | Path]) -> Optional[Path]:
    """Pin CINEFORGE_HOME (and CINEFORGE_PROJECTS_DIR) before loading registry/backlot."""
    if not workspace:
        return None
    resolved = Path(workspace).expanduser().resolve()
    os.environ["CINEFORGE_HOME"] = str(resolved)
    os.environ.setdefault("CINEFORGE_PROJECTS_DIR", str(resolved / "projects"))
    return resolved


def find_executable(*names: str) -> Optional[str]:
    """Return the first matching executable path on PATH."""
    for name in names:
        hit = shutil.which(name)
        if hit:
            return hit
    return None


def _command_version(cmd: list[str]) -> Optional[str]:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        out = (proc.stdout or proc.stderr or "").strip().splitlines()
        return out[0].strip() if out else None
    except Exception:
        return None


def write_env_keys(env_path: Path, updates: dict[str, str]) -> Path:
    """Safely insert or update non-empty KEY=VALUE entries in a .env file."""
    clean_updates = {k.strip(): v.strip() for k, v in updates.items() if k.strip() and v.strip()}
    env_path.parent.mkdir(parents=True, exist_ok=True)
    if not env_path.exists():
        example = get_package_root() / ".env.example"
        if example.is_file():
            shutil.copy2(example, env_path)
        else:
            env_path.write_text("", encoding="utf-8")

    lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
    remaining = dict(clean_updates)
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.partition("=")[0].strip()
            if key in remaining:
                val = remaining.pop(key)
                new_lines.append(f"{key}={val}")
                continue
        new_lines.append(line)

    if remaining:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append("# Added by cineforge setup")
        for key, val in remaining.items():
            new_lines.append(f"{key}={val}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    for key, val in clean_updates.items():
        os.environ[key] = val
    return env_path


def setup_remotion_workspace(workspace: Optional[Path] = None, *, install_deps: bool = True) -> tuple[bool, str]:
    """Copy remotion-composer template into workspace and optionally run npm install."""
    template_dir = get_remotion_template_dir()
    if not template_dir.is_dir() or not (template_dir / "package.json").is_file():
        return False, f"Remotion template directory not found at {template_dir}"

    existing = get_remotion_composer_dir()
    if (existing / "package.json").is_file() and (existing / "node_modules").is_dir():
        return True, f"Remotion already ready at {existing}"

    ws = ensure_workspace_initialized(workspace)
    target = ws / "remotion-composer"
    if target.resolve() != template_dir.resolve():
        target.mkdir(parents=True, exist_ok=True)
        for fname in ("package.json", "package-lock.json", "tsconfig.json", "SCENE_TYPES.md"):
            src = template_dir / fname
            if src.is_file():
                shutil.copy2(src, target / fname)
        for sub in ("src", "public"):
            src_sub = template_dir / sub
            if src_sub.is_dir():
                shutil.copytree(src_sub, target / sub, dirs_exist_ok=True)

    if not install_deps:
        return True, f"Remotion template staged at {target} (npm install skipped)"

    npm_cmd = find_executable("npm.cmd", "npm", "npm.exe")
    if not npm_cmd:
        return False, "npm not found on PATH. Install Node.js 20+ from https://nodejs.org/"

    try:
        subprocess.run([npm_cmd, "install"], cwd=target, check=True)
        return True, f"Remotion dependencies installed at {target}"
    except subprocess.CalledProcessError as exc:
        return False, f"npm install failed in {target}: {exc}"


def warm_hyperframes_cache() -> tuple[bool, str]:
    """Pre-warm the npx hyperframes package cache."""
    npx_cmd = find_executable("npx.cmd", "npx", "npx.exe")
    if not npx_cmd:
        return False, "npx not found on PATH (requires Node.js 22+)."
    try:
        proc = subprocess.run(
            [npx_cmd, "--yes", "hyperframes", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=True,
        )
        ver = (proc.stdout or "").strip() or "cached"
        return True, f"HyperFrames CLI ready ({ver})"
    except Exception as exc:
        return False, f"HyperFrames warm failed: {exc}"


def install_piper_tts() -> tuple[bool, str]:
    """Install optional offline piper-tts package into the active Python environment."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "piper-tts"],
            check=True,
        )
        return True, "piper-tts installed"
    except subprocess.CalledProcessError as exc:
        return False, f"pip install piper-tts failed: {exc}"


def build_doctor_report() -> dict[str, Any]:
    """Collect a structured diagnostic report of CineForge paths, runtimes, and tools."""
    from tools.tool_registry import registry

    registry.ensure_discovered()
    summary = registry.provider_menu_summary()

    ffmpeg_path = find_executable("ffmpeg")
    ffprobe_path = find_executable("ffprobe")
    node_path = find_executable("node", "node.exe")
    npx_path = find_executable("npx.cmd", "npx", "npx.exe")
    uv_path = find_executable("uv")

    remotion_dir = get_remotion_composer_dir()
    remotion_ready = (remotion_dir / "package.json").is_file() and (remotion_dir / "node_modules").is_dir()

    hyperframes_info: dict[str, Any] = {}
    hf_tool = registry.get("hyperframes_compose")
    if hf_tool is not None and hasattr(hf_tool, "_runtime_check"):
        try:
            hyperframes_info = hf_tool._runtime_check()
        except Exception as exc:
            hyperframes_info = {"runtime_available": False, "reasons": [str(exc)]}

    return {
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
        },
        "paths": {
            "package_root": str(get_package_root()),
            "workspace_root": str(get_workspace_root()),
            "projects_dir": str(get_projects_dir()),
            "remotion_dir": str(remotion_dir),
            "remotion_ready": remotion_ready,
            "env_files_found": [str(p) for p in get_env_search_paths() if p.is_file()],
        },
        "binaries": {
            "ffmpeg": {
                "installed": bool(ffmpeg_path),
                "path": ffmpeg_path,
                "version": _command_version([ffmpeg_path, "-version"]) if ffmpeg_path else None,
            },
            "ffprobe": {"installed": bool(ffprobe_path), "path": ffprobe_path},
            "node": {
                "installed": bool(node_path),
                "path": node_path,
                "version": _command_version([node_path, "--version"]) if node_path else None,
            },
            "npx": {"installed": bool(npx_path), "path": npx_path},
            "uv": {"installed": bool(uv_path), "path": uv_path},
        },
        "total_tools_discovered": len(registry.list_all()),
        "provider_summary": summary,
        "hyperframes": hyperframes_info,
    }


def discover_demos() -> dict[str, Path]:
    """Return available zero-key Remotion demo prop files mapped by stem name."""
    for base in (get_remotion_composer_dir(), get_remotion_template_dir()):
        props_dir = base / "public" / "demo-props"
        if props_dir.is_dir():
            found = {p.stem: p for p in sorted(props_dir.glob("*.json"))}
            if found:
                return found
    return {}


def render_demo_video(demo_name: Optional[str] = None) -> list[Path]:
    """Render one or all zero-key Remotion demos into projects/demos/renders/."""
    demos = discover_demos()
    if not demos:
        raise FileNotFoundError("No demo prop files found in remotion-composer/public/demo-props/")

    if demo_name and demo_name not in demos:
        available = ", ".join(demos)
        raise ValueError(f"Unknown demo {demo_name!r}. Available demos: {available}")

    if not find_executable("node", "node.exe"):
        raise RuntimeError("Node.js is required to render Remotion demos (https://nodejs.org/).")
    npx_cmd = find_executable("npx.cmd", "npx", "npx.exe")
    if not npx_cmd:
        raise RuntimeError("npx is required to render Remotion demos.")

    composer_dir = get_remotion_composer_dir()
    if not (composer_dir / "node_modules").is_dir():
        ok, msg = setup_remotion_workspace(install_deps=True)
        if not ok:
            raise RuntimeError(msg)
        composer_dir = get_remotion_composer_dir()

    output_dir = get_projects_dir() / "demos" / "renders"
    output_dir.mkdir(parents=True, exist_ok=True)
    selected = {demo_name: demos[demo_name]} if demo_name else demos
    rendered: list[Path] = []

    for name, props_path in selected.items():
        payload = json.loads(props_path.read_text(encoding="utf-8"))
        if not isinstance(payload.get("cuts"), list) or not payload["cuts"]:
            raise ValueError(f"Demo props {props_path} must define at least one cut.")
        out_path = output_dir / f"{name}.mp4"
        subprocess.run(
            [
                npx_cmd,
                "remotion",
                "render",
                "src/index.tsx",
                "Explainer",
                str(out_path),
                "--props",
                str(props_path),
                "--codec",
                "h264",
            ],
            cwd=composer_dir,
            check=True,
        )
        rendered.append(out_path)
    return rendered
