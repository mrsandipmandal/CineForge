"""Shared runtime, workspace, doctor, and demo helpers for CineForge CLI and MCP."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional
from urllib import request as _urllib_request
from urllib.error import URLError

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
    ("GEMINI_API_KEY", "Google Gemini / Imagen / Veo / Lyria", "Free tier via Google AI Studio (also accepts GOOGLE_API_KEY)"),
    ("PEXELS_API_KEY", "Pexels Stock Video & Images", "Free HD stock media API"),
    ("PIXABAY_API_KEY", "Pixabay Stock Media & Music", "Free stock media API"),
    ("OPENROUTER_API_KEY", "OpenRouter (Free LLMs + Speech Gateways)", "Free & paid multi-model API"),
    ("GROQ_API_KEY", "Groq (Fast Free LLM & Whisper STT)", "Free-tier LPU inference"),
    ("FAL_KEY", "fal.ai (FLUX, Kling, Seedance, Wan, 3D)", "Unified multi-model media API"),
    ("ELEVENLABS_API_KEY", "ElevenLabs (TTS, SFX, Music, Voice Clone)", "Studio voice & audio API"),
    ("SARVAM_API_KEY", "Sarvam AI (Bengali bn-IN, Hindi, Indic TTS)", "Native Indian language voices"),
    ("OPENAI_API_KEY", "OpenAI (GPT Image, TTS, Sora)", "OpenAI media APIs"),
)

_POPULAR_KEY_GROUPS: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("GEMINI_API_KEY", "GOOGLE_API_KEY"), "Google Imagen / Veo / Lyria / Gemini TTS", "Set GEMINI_API_KEY (or GOOGLE_API_KEY) -> https://aistudio.google.com/apikey"),
    (("PEXELS_API_KEY",), "Pexels Stock Video & Images", "Set PEXELS_API_KEY (free HD stock) -> https://www.pexels.com/api/"),
    (("PIXABAY_API_KEY",), "Pixabay Stock Video & Images", "Set PIXABAY_API_KEY (free stock) -> https://pixabay.com/api/docs/"),
    (("OPENROUTER_API_KEY",), "OpenRouter LLMs & Free TTS Gateways", "Set OPENROUTER_API_KEY (free tier) -> https://openrouter.ai/keys"),
    (("GROQ_API_KEY",), "Groq Fast LLM & Whisper Transcription", "Set GROQ_API_KEY (free tier) -> https://console.groq.com/keys"),
    (("FAL_KEY", "FAL_AI_API_KEY"), "fal.ai Multi-Model Image / Video / 3D", "Set FAL_KEY -> https://fal.ai/dashboard/keys"),
    (("ELEVENLABS_API_KEY",), "ElevenLabs Voice, SFX & Music", "Set ELEVENLABS_API_KEY -> https://elevenlabs.io/"),
    (("SARVAM_API_KEY",), "Sarvam AI Indic TTS & STT (bn-IN / hi-IN)", "Set SARVAM_API_KEY -> https://dashboard.sarvam.ai/"),
    (("OPENAI_API_KEY",), "OpenAI GPT Image, TTS & Sora", "Set OPENAI_API_KEY -> https://platform.openai.com/api-keys"),
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


def _pip_install_packages(packages: list[str]) -> tuple[bool, str]:
    """Install packages into the active Python interpreter via pip or uv pip."""
    import importlib.util

    if importlib.util.find_spec("pip") is not None:
        cmd = [sys.executable, "-m", "pip", "install", *packages]
    else:
        uv_cmd = find_executable("uv")
        if not uv_cmd:
            return False, f"Neither `pip` nor `uv` is available to install {' '.join(packages)}"
        cmd = [uv_cmd, "pip", "install", "--python", sys.executable, *packages]

    try:
        subprocess.run(cmd, check=True)
        return True, f"Installed {' '.join(packages)}"
    except subprocess.CalledProcessError as exc:
        return False, f"Package install failed ({' '.join(packages)}): {exc}"


def install_piper_tts() -> tuple[bool, str]:
    """Install optional offline piper-tts package into the active Python environment."""
    return _pip_install_packages(["piper-tts"])


def install_media_extras() -> tuple[bool, str]:
    """Install optional zero-key local media tools (yt-dlp, transcripts, faster-whisper)."""
    return _pip_install_packages(["yt-dlp", "youtube-transcript-api", "faster-whisper"])


def _count_dotenv_nonempty_keys(env_path: Path) -> int:
    """Count non-empty active variables declared in a .env file without exposing values."""
    if not env_path.is_file():
        return 0
    count = 0
    try:
        for raw in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and val and not val.startswith("your_") and val not in ("...", "xxx"):
                count += 1
    except OSError:
        return 0
    return count


def _detect_env_warnings(env_files: list[Path]) -> list[str]:
    """Check for duplicate keys in .env files and conflicting offline/cloud flags."""
    warnings: list[str] = []
    for env_path in env_files:
        if not env_path.is_file():
            continue
        seen: dict[str, int] = {}
        try:
            for raw in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key = line.partition("=")[0].strip()
                if key:
                    seen[key] = seen.get(key, 0) + 1
        except OSError:
            continue
        dups = sorted(k for k, cnt in seen.items() if cnt > 1)
        if dups:
            warnings.append(
                f"Duplicate key(s) in {env_path}: {', '.join(dups)} (first or last may win depending on loader)"
            )

    if os.environ.get("TTS_OFFLINE", "").strip().lower() in ("1", "true", "yes"):
        cloud_tts_keys = [
            k for k in ("ELEVENLABS_API_KEY", "AZURE_SPEECH_KEY", "GOOGLE_TTS_API_KEY", "SARVAM_API_KEY")
            if os.environ.get(k, "").strip()
        ]
        if cloud_tts_keys:
            warnings.append(
                f"TTS_OFFLINE=true is active while cloud TTS key(s) are set ({', '.join(cloud_tts_keys)}); "
                "cloud TTS providers will be bypassed."
            )

    return warnings


def build_doctor_report() -> dict[str, Any]:
    """Collect a structured diagnostic report of CineForge paths, runtimes, and tools."""
    from tools.tool_registry import registry

    registry.ensure_discovered()
    summary = registry.provider_menu_summary()

    status_counts = {"available": 0, "degraded": 0, "unavailable": 0}
    category_counts: dict[str, int] = {}
    optional_pkg_tools: list[dict[str, str]] = []

    for name in sorted(registry.list_all()):
        tool = registry.get(name)
        if tool is None:
            continue
        avail = registry.describe_tool_availability(tool)
        st = avail["status"]
        status_counts[st] = status_counts.get(st, 0) + 1
        cat = avail["category"]
        if st != "available":
            category_counts[cat] = category_counts.get(cat, 0) + 1
        if cat in ("missing_pkg", "missing_cmd"):
            optional_pkg_tools.append(
                {
                    "tool": name,
                    "capability": tool.capability,
                    "reason": avail["reason"],
                }
            )

    popular_unlocks: list[dict[str, str]] = []
    for env_names, capability_label, hint in _POPULAR_KEY_GROUPS:
        if any(os.environ.get(k, "").strip() for k in env_names):
            continue
        popular_unlocks.append(
            {
                "env_var": env_names[0],
                "label": capability_label,
                "hint": hint,
            }
        )

    env_files_found = [p for p in get_env_search_paths() if p.is_file()]
    env_summary = [
        {"path": str(p), "nonempty_keys": _count_dotenv_nonempty_keys(p)}
        for p in env_files_found
    ]
    env_warnings = _detect_env_warnings(env_files_found)

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
            "env_files_found": [str(p) for p in env_files_found],
        },
        "env_summary": env_summary,
        "env_warnings": env_warnings,
        "status_counts": status_counts,
        "unavailable_breakdown": category_counts,
        "optional_package_tools": optional_pkg_tools,
        "popular_unlocks": popular_unlocks,
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


# ---------------------------------------------------------------------------
# API key live validation
# ---------------------------------------------------------------------------

#: Lightweight probe specs: (env_var_names, label, test_url, auth_header_template)
#: ``auth_header_template`` uses ``{key}`` as placeholder for the API key value.
_KEY_PROBES: tuple[tuple[tuple[str, ...], str, str, str], ...] = (
    (
        ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        "Google / Gemini",
        "https://generativelanguage.googleapis.com/v1/models?key={key}",
        "",  # key in URL
    ),
    (
        ("GROQ_API_KEY",),
        "Groq",
        "https://api.groq.com/openai/v1/models",
        "Bearer {key}",
    ),
    (
        ("OPENROUTER_API_KEY",),
        "OpenRouter",
        "https://openrouter.ai/api/v1/models",
        "Bearer {key}",
    ),
    (
        ("ELEVENLABS_API_KEY",),
        "ElevenLabs",
        "https://api.elevenlabs.io/v1/voices",
        "xi-api-key {key}",
    ),
    (
        ("SARVAM_API_KEY",),
        "Sarvam AI",
        "https://api.sarvam.ai/status",
        "Bearer {key}",
    ),
    (
        ("PIXABAY_API_KEY",),
        "Pixabay",
        "https://pixabay.com/api/?key={key}&q=test&per_page=1",
        "",
    ),
    (
        ("FAL_KEY", "FAL_AI_API_KEY"),
        "fal.ai",
        "https://fal.run/health",
        "Key {key}",
    ),
    (
        ("ATLASCLOUD_API_KEY", "ATLAS_CLOUD_API_KEY", "ATLAS_API_KEY"),
        "Atlas Cloud",
        "https://api.atlascloud.ai/api/v1/health",
        "Bearer {key}",
    ),
    (
        ("PEXELS_API_KEY",),
        "Pexels",
        "https://api.pexels.com/v1/curated?per_page=1",
        "Authorization {key}",
    ),
)


def check_api_keys(timeout: float = 5.0) -> dict[str, dict[str, Any]]:
    """Probe each known API key with a lightweight HTTP request.

    Returns a mapping of ``label`` → result dict::

        {
            "present": True,       # key is set in env
            "valid": True | False, # HTTP probe returned a non-401/403 response
            "status_code": 200,
            "env_var": "GOOGLE_API_KEY",  # which var was actually used
            "error": None | "timeout" | "network" | str,
        }

    When a key is not present in the environment the probe is skipped
    (``"present": False, "valid": None``). Network failures are caught
    and reported as ``"error": "..."`` rather than raising.
    """
    from urllib import request as _req
    from urllib.error import URLError, HTTPError

    results: dict[str, dict[str, Any]] = {}

    for env_vars, label, url_tmpl, auth_tmpl in _KEY_PROBES:
        # Find the first set env var among the aliases.
        key: str | None = None
        used_var: str | None = None
        for var in env_vars:
            val = os.environ.get(var, "").strip()
            if val:
                key = val
                used_var = var
                break

        if not key:
            results[label] = {
                "present": False,
                "valid": None,
                "status_code": None,
                "env_var": env_vars[0],
                "error": None,
            }
            continue

        # Build the request.
        url = url_tmpl.replace("{key}", key)
        req = _req.Request(url)
        if auth_tmpl and "{key}" in auth_tmpl:
            req.add_header("Authorization", auth_tmpl.replace("{key}", key))
        elif auth_tmpl and not url_tmpl.endswith("{key}") and "{key}" not in url_tmpl:
            # Template doesn't go in URL and no placeholder — skip auth header.
            pass
        # ElevenLabs uses xi-api-key header with non-standard prefix.
        if auth_tmpl.startswith("xi-api-key"):
            req.headers.pop("Authorization", None)
            req.add_header("xi-api-key", key)

        try:
            with _req.urlopen(req, timeout=timeout) as resp:
                sc = resp.getcode()
                results[label] = {
                    "present": True,
                    "valid": sc < 400,
                    "status_code": sc,
                    "env_var": used_var,
                    "error": None,
                }
        except HTTPError as exc:
            invalid = exc.code in (401, 403)
            results[label] = {
                "present": True,
                "valid": not invalid,
                "status_code": exc.code,
                "env_var": used_var,
                "error": f"HTTP {exc.code}" if invalid else None,
            }
        except URLError as exc:
            results[label] = {
                "present": True,
                "valid": None,  # Can't determine — network issue
                "status_code": None,
                "env_var": used_var,
                "error": f"network: {exc.reason}",
            }
        except TimeoutError:
            results[label] = {
                "present": True,
                "valid": None,
                "status_code": None,
                "env_var": used_var,
                "error": "timeout",
            }
        except Exception as exc:  # pragma: no cover
            results[label] = {
                "present": True,
                "valid": None,
                "status_code": None,
                "env_var": used_var,
                "error": str(exc),
            }

    return results
