"""Setuptools build script that bundles CineForge non-package assets cleanly into wheels."""

from __future__ import annotations

import shutil
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

_REPO_ROOT = Path(__file__).resolve().parent

_ROOT_FILES = (
    "AGENT_GUIDE.md",
    "PROJECT_CONTEXT.md",
    "PROMPT_GALLERY.md",
    "README.md",
    "config.yaml",
    ".env.example",
)

_ROOT_DIRS = (
    "pipeline_defs",
    "skills",
    "ink-theater",
    ".claude/commands",
    ".codex/prompts",
)

_SKIP_DIR_NAMES = {
    "__pycache__",
    ".git",
    "node_modules",
    "out",
    "projects",
    ".remotion",
    ".cache",
}

_HEAVY_SKILL_MEDIA_EXTS = {
    ".mp4",
    ".webm",
    ".mov",
    ".avi",
    ".mkv",
    ".wav",
    ".mp3",
    ".ogg",
    ".flac",
    ".onnx",
}

# Skip binary showcase/preview files > 350 KB inside .agents/skills to keep
# PyPI wheels lean while keeping every SKILL.md, script, and template intact.
_MAX_AGENT_SKILL_BINARY_BYTES = 350 * 1024


def _ignore_common(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in _SKIP_DIR_NAMES or name.endswith((".pyc", ".pyo"))
    }


def _copy_agent_skills(src_root: Path, dst_root: Path) -> None:
    if not src_root.is_dir():
        return
    for src_file in src_root.rglob("*"):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(src_root)
        if any(part in _SKIP_DIR_NAMES for part in rel.parts):
            continue
        suffix = src_file.suffix.lower()
        if suffix in _HEAVY_SKILL_MEDIA_EXTS:
            continue
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ttf", ".otf", ".woff2"}:
            try:
                if src_file.stat().st_size > _MAX_AGENT_SKILL_BINARY_BYTES:
                    continue
            except OSError:
                continue
        dest = dst_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest)


def _copy_remotion_template(src_root: Path, dst_root: Path) -> None:
    if not src_root.is_dir():
        return
    for item_name in ("package.json", "package-lock.json", "tsconfig.json", "SCENE_TYPES.md"):
        src_file = src_root / item_name
        if src_file.is_file():
            dst_root.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_root / item_name)
    for sub in ("src", "public"):
        src_sub = src_root / sub
        if src_sub.is_dir():
            shutil.copytree(src_sub, dst_root / sub, ignore=_ignore_common, dirs_exist_ok=True)


class BuildPyWithAssets(_build_py):
    """Bundle CineForge manifests, skills, and templates into ``cineforge_assets``."""

    def run(self) -> None:
        super().run()
        if not (_REPO_ROOT / "pipeline_defs").is_dir():
            return

        assets_dst = Path(self.build_lib) / "cineforge_assets"
        assets_dst.mkdir(parents=True, exist_ok=True)
        (assets_dst / "__init__.py").write_text(
            '"""Bundled CineForge runtime assets (pipelines, skills, templates)."""\n',
            encoding="utf-8",
        )

        for filename in _ROOT_FILES:
            src = _REPO_ROOT / filename
            if src.is_file():
                shutil.copy2(src, assets_dst / filename)

        for dirname in _ROOT_DIRS:
            src = _REPO_ROOT / dirname
            if src.is_dir():
                shutil.copytree(src, assets_dst / dirname, ignore=_ignore_common, dirs_exist_ok=True)

        _copy_agent_skills(_REPO_ROOT / ".agents" / "skills", assets_dst / ".agents" / "skills")
        _copy_remotion_template(_REPO_ROOT / "remotion-composer", assets_dst / "remotion-composer")


setup(cmdclass={"build_py": BuildPyWithAssets})
