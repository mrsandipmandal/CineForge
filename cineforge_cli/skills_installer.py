"""Install portable CineForge skills, rules, and slash commands into user IDEs/projects."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from lib.paths import get_agent_skills_dir, get_package_root

SUPPORTED_SKILL_TARGETS = (
    "agents",
    "claude",
    "cursor",
    "codex",
    "antigravity",
)

_CURSOR_RULE_CONTENT = """---
description: CineForge AI Video Studio integration rule
globs: ["**/*"]
alwaysApply: false
---

# CineForge Video Studio

When the user asks to produce, edit, clip, dub, or animate videos with CineForge:
- Read `.agents/skills/cineforge/SKILL.md` first (or use the `cineforge` MCP server if connected).
- Run preflight (`cineforge_preflight` MCP tool or `cineforge doctor --json`) before creative proposals.
- Write all project artifacts and renders under `projects/<project-id>/`.
"""


def _copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def _copy_tree_md(src_dir: Path, dst_dir: Path) -> list[str]:
    copied: list[str] = []
    if not src_dir.is_dir():
        return copied
    for item in sorted(src_dir.glob("*.md")):
        if item.name.lower() == "readme.md":
            continue
        dst = dst_dir / item.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dst)
        copied.append(str(dst))
    return copied


def list_installable_skills() -> list[dict[str, str]]:
    """List portable CineForge entry skills and featured workflow skills."""
    agent_skills = get_agent_skills_dir()
    items: list[dict[str, str]] = []
    if not agent_skills.is_dir():
        return items
    for skill_dir in sorted(agent_skills.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_dir.is_dir() or not skill_md.is_file():
            continue
        first_line = ""
        for raw in skill_md.read_text(encoding="utf-8", errors="replace").splitlines():
            s = raw.strip()
            if s and not s.startswith(("---", "name:", "description:", "#")):
                first_line = s[:100]
                break
        items.append({"name": skill_dir.name, "path": str(skill_md), "summary": first_line})
    return items


def install_skills(
    target: str,
    *,
    project_dir: Optional[Path] = None,
    global_install: bool = False,
    include_workflows: bool = True,
) -> dict[str, list[str]]:
    """Install the portable CineForge skill pack into the specified IDE/agent target."""
    targets = list(SUPPORTED_SKILL_TARGETS) if target == "all" else [target]
    for item in targets:
        if item not in SUPPORTED_SKILL_TARGETS:
            raise ValueError(
                f"Unsupported target {item!r}. Choose from: {', '.join(SUPPORTED_SKILL_TARGETS)}, all"
            )

    base_dir = (project_dir or Path.cwd()).resolve()
    home = Path.home()
    agent_skills_dir = get_agent_skills_dir()
    pkg_root = get_package_root()

    core_skill_src = agent_skills_dir / "cineforge" / "SKILL.md"
    if not core_skill_src.is_file():
        raise FileNotFoundError(f"Bundled CineForge SKILL.md not found at {core_skill_src}")

    workflow_skills = ["bengali-science-explainer", "stream-clips", "faceless-shorts", "ai-video-editor"]
    commands_dir = pkg_root / ".claude" / "commands"
    codex_prompts_dir = pkg_root / ".codex" / "prompts"

    installed: dict[str, list[str]] = {}

    for tgt in targets:
        written: list[str] = []
        if tgt == "agents":
            skill_root = (home / ".agents" / "skills") if global_install else (base_dir / ".agents" / "skills")
            if _copy_if_exists(core_skill_src, skill_root / "cineforge" / "SKILL.md"):
                written.append(str(skill_root / "cineforge" / "SKILL.md"))
            if include_workflows:
                for wf in workflow_skills:
                    wf_src = agent_skills_dir / wf / "SKILL.md"
                    if _copy_if_exists(wf_src, skill_root / wf / "SKILL.md"):
                        written.append(str(skill_root / wf / "SKILL.md"))

        elif tgt == "claude":
            claude_root = (home / ".claude") if global_install else (base_dir / ".claude")
            if _copy_if_exists(core_skill_src, claude_root / "skills" / "cineforge" / "SKILL.md"):
                written.append(str(claude_root / "skills" / "cineforge" / "SKILL.md"))
            if include_workflows:
                for wf in workflow_skills:
                    wf_src = agent_skills_dir / wf / "SKILL.md"
                    if _copy_if_exists(wf_src, claude_root / "skills" / wf / "SKILL.md"):
                        written.append(str(claude_root / "skills" / wf / "SKILL.md"))
            written.extend(_copy_tree_md(commands_dir, claude_root / "commands"))

        elif tgt == "cursor":
            cursor_root = (home / ".cursor") if global_install else (base_dir / ".cursor")
            rule_path = cursor_root / "rules" / "cineforge-mcp.mdc"
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            rule_path.write_text(_CURSOR_RULE_CONTENT, encoding="utf-8")
            written.append(str(rule_path))
            shared_skill_dest = (
                home / ".agents" / "skills" / "cineforge" / "SKILL.md"
                if global_install
                else base_dir / ".agents" / "skills" / "cineforge" / "SKILL.md"
            )
            if _copy_if_exists(core_skill_src, shared_skill_dest):
                written.append(str(shared_skill_dest))
            written.extend(_copy_tree_md(commands_dir, cursor_root / "commands"))

        elif tgt == "codex":
            codex_root = (home / ".codex") if global_install else (base_dir / ".codex")
            prompt_src = codex_prompts_dir if codex_prompts_dir.is_dir() else commands_dir
            written.extend(_copy_tree_md(prompt_src, codex_root / "prompts"))
            skill_dest = (
                home / ".agents" / "skills" / "cineforge" / "SKILL.md"
                if global_install
                else base_dir / ".agents" / "skills" / "cineforge" / "SKILL.md"
            )
            if _copy_if_exists(core_skill_src, skill_dest):
                written.append(str(skill_dest))

        elif tgt == "antigravity":
            ag_root = (home / ".gemini" / "antigravity" / "skills") if global_install else (base_dir / ".agents" / "skills")
            if _copy_if_exists(core_skill_src, ag_root / "cineforge" / "SKILL.md"):
                written.append(str(ag_root / "cineforge" / "SKILL.md"))
            if include_workflows:
                for wf in workflow_skills:
                    wf_src = agent_skills_dir / wf / "SKILL.md"
                    if _copy_if_exists(wf_src, ag_root / wf / "SKILL.md"):
                        written.append(str(ag_root / wf / "SKILL.md"))

        installed[tgt] = written

    return installed
