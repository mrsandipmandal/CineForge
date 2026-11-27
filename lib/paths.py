"""Canonical repository and workspace paths — single source of truth.

Separates read-only bundled package assets (``PACKAGE_ROOT``: pipeline
definitions, schemas, skills, styles, Backlot UI, templates) from the mutable
user workspace (``WORKSPACE_ROOT``: projects, ``.env``, ``config.yaml``,
``music_library``, ``sample-files``, ``.backlot`` state, and local
``remotion-composer`` runtime).

When running inside a CineForge repository checkout, both roots point to the
repository root (unless ``CINEFORGE_HOME`` / ``CINEFORGE_WORKSPACE`` overrides
the workspace). When installed via ``pip``/``uv`` into ``site-packages``,
``PACKAGE_ROOT`` resolves to the bundled package assets while
``WORKSPACE_ROOT`` resolves to an initialized workspace in ``cwd`` or
``~/.cineforge``.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional

_SOURCE_ROOT = Path(__file__).resolve().parent.parent


def _is_repo_root(path: Path) -> bool:
    """Return True if *path* looks like a CineForge source checkout."""
    return (
        (path / "pipeline_defs").is_dir()
        and (path / "tools").is_dir()
        and (path / "lib").is_dir()
    )


def _is_workspace_root(path: Path) -> bool:
    """Return True if *path* is an initialized CineForge workspace or checkout."""
    if _is_repo_root(path):
        return True
    # Do not treat $HOME itself as a workspace root merely because ~/.cineforge
    # exists inside it; ~/.cineforge is the default child workspace.
    try:
        is_home = path.resolve() == Path.home().resolve()
    except OSError:
        is_home = False
    if not is_home and (path / ".cineforge").is_dir():
        return True
    return (path / "projects").is_dir() and (path / "config.yaml").is_file()


def get_package_root() -> Path:
    """Return the root containing read-only bundled assets (pipelines, skills, etc.)."""
    if _is_repo_root(_SOURCE_ROOT):
        return _SOURCE_ROOT
    try:
        import cineforge_assets  # type: ignore

        assets_dir = Path(cineforge_assets.__file__).resolve().parent
        if (assets_dir / "pipeline_defs").is_dir():
            return assets_dir
    except ImportError:
        pass
    return _SOURCE_ROOT


def get_workspace_root() -> Path:
    """Return the writable user workspace root for projects, .env, and runtime state."""
    env_home = os.environ.get("CINEFORGE_HOME") or os.environ.get("CINEFORGE_WORKSPACE")
    if env_home:
        return Path(env_home).expanduser().resolve()

    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if _is_workspace_root(candidate):
            return candidate

    return (Path.home() / ".cineforge").resolve()


def get_projects_dir() -> Path:
    """Return the canonical directory holding CineForge production projects."""
    override = os.environ.get("CINEFORGE_PROJECTS_DIR")
    if override:
        return Path(override).expanduser()
    return get_workspace_root() / "projects"


def get_schemas_dir() -> Path:
    """Return the directory containing JSON schemas."""
    try:
        import schemas

        pkg_dir = Path(schemas.__file__).resolve().parent
        if (pkg_dir / "artifacts").is_dir():
            return pkg_dir
    except Exception:
        pass
    return get_package_root() / "schemas"


def get_styles_dir() -> Path:
    """Return the directory containing built-in style playbooks."""
    try:
        import styles

        pkg_dir = Path(styles.__file__).resolve().parent
        if any(pkg_dir.glob("*.yaml")):
            return pkg_dir
    except Exception:
        pass
    return get_package_root() / "styles"


def get_custom_styles_dir() -> Path:
    """Return the writable directory for generated custom style playbooks."""
    return get_workspace_root() / "styles" / "custom"


def get_pipeline_defs_dir() -> Path:
    """Return the directory containing pipeline YAML manifests."""
    return get_package_root() / "pipeline_defs"


def get_skills_dir() -> Path:
    """Return the directory containing Layer 2 CineForge skills."""
    return get_package_root() / "skills"


def get_agent_skills_dir() -> Path:
    """Return the directory containing Layer 3 vendor/technology skills."""
    return get_package_root() / ".agents" / "skills"


def get_backlot_state_dir() -> Path:
    """Return the writable .backlot state directory inside the active workspace."""
    return get_workspace_root() / ".backlot"


def get_config_path() -> Path:
    """Return the active config.yaml path (workspace first, package default fallback)."""
    ws_cfg = get_workspace_root() / "config.yaml"
    if ws_cfg.is_file():
        return ws_cfg
    pkg_cfg = get_package_root() / "config.yaml"
    if pkg_cfg.is_file():
        return pkg_cfg
    return ws_cfg


def get_env_search_paths() -> list[Path]:
    """Return candidate .env paths in priority order (cwd -> workspace -> package)."""
    candidates = [
        Path.cwd() / ".env",
        get_workspace_root() / ".env",
        get_package_root() / ".env",
    ]
    seen: set[Path] = set()
    ordered: list[Path] = []
    for cand in candidates:
        try:
            resolved = cand.resolve()
        except OSError:
            resolved = cand
        if resolved not in seen:
            seen.add(resolved)
            ordered.append(cand)
    return ordered


_MUSIC_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
    ".opus",
    ".aiff",
    ".aif",
}


def _has_audio_files(directory: Path) -> bool:
    """Return True if *directory* exists and contains at least one audio track."""
    try:
        return directory.is_dir() and any(
            p.is_file() and p.suffix.lower() in _MUSIC_EXTENSIONS
            for p in directory.rglob("*")
        )
    except OSError:
        return False


def get_music_library_dir() -> Path:
    """Return the user's royalty-free music library directory."""
    ws_dir = get_workspace_root() / "music_library"
    pkg_dir = get_package_root() / "music_library"
    if _has_audio_files(ws_dir):
        return ws_dir
    if _has_audio_files(pkg_dir):
        return pkg_dir
    if ws_dir.exists():
        return ws_dir
    return pkg_dir if pkg_dir.exists() else ws_dir


def get_sample_files_dir() -> Path:
    """Return the identity sample-files directory (workspace first, package fallback)."""
    ws_dir = get_workspace_root() / "sample-files"
    if ws_dir.exists():
        return ws_dir
    pkg_dir = get_package_root() / "sample-files"
    return pkg_dir if pkg_dir.exists() else ws_dir


def get_runtime_dir() -> Path:
    """Return the local .runtime directory for optional portable binaries."""
    ws_dir = get_workspace_root() / ".runtime"
    if ws_dir.exists():
        return ws_dir
    pkg_dir = get_package_root() / ".runtime"
    return pkg_dir if pkg_dir.exists() else ws_dir


def get_remotion_template_dir() -> Path:
    """Return the bundled remotion-composer template directory."""
    return get_package_root() / "remotion-composer"


def get_remotion_composer_dir() -> Path:
    """Return the active remotion-composer directory (preferring one with node_modules)."""
    override = os.environ.get("CINEFORGE_REMOTION_DIR")
    if override:
        return Path(override).expanduser().resolve()

    candidates = [
        Path.cwd() / "remotion-composer",
        get_workspace_root() / "remotion-composer",
        get_package_root() / "remotion-composer",
    ]
    unique: list[Path] = []
    seen: set[Path] = set()
    for cand in candidates:
        try:
            res = cand.resolve()
        except OSError:
            res = cand
        if res not in seen:
            seen.add(res)
            unique.append(cand)

    for cand in unique:
        if (cand / "package.json").is_file() and (cand / "node_modules").is_dir():
            return cand
    for cand in unique:
        if (cand / "package.json").is_file():
            return cand
    return get_workspace_root() / "remotion-composer"


def ensure_workspace_initialized(workspace: Optional[Path] = None) -> Path:
    """Initialize a writable CineForge workspace directory idempotently."""
    root = workspace.expanduser().resolve() if workspace else get_workspace_root()
    pkg = get_package_root()

    (root / ".cineforge").mkdir(parents=True, exist_ok=True)
    (root / "projects").mkdir(parents=True, exist_ok=True)
    (root / "music_library").mkdir(parents=True, exist_ok=True)
    (root / ".backlot").mkdir(parents=True, exist_ok=True)

    pkg_config = pkg / "config.yaml"
    ws_config = root / "config.yaml"
    if pkg_config.is_file() and not ws_config.exists():
        shutil.copy2(pkg_config, ws_config)

    pkg_env_example = pkg / ".env.example"
    ws_env_example = root / ".env.example"
    if pkg_env_example.is_file() and not ws_env_example.exists():
        shutil.copy2(pkg_env_example, ws_env_example)

    ws_env = root / ".env"
    if pkg_env_example.is_file() and not ws_env.exists():
        shutil.copy2(pkg_env_example, ws_env)

    return root


PACKAGE_ROOT = get_package_root()
WORKSPACE_ROOT = get_workspace_root()
# Backward-compatible constant used across tools, tests, and Backlot.
REPO_ROOT = PACKAGE_ROOT
# Overridable for staging/screenshots/tests. Everything — checkpoint writes,
# event attribution, the Backlot board — follows the same root.
PROJECTS_DIR = get_projects_dir()
