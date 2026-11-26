"""CineForge Smart Hybrid Model Context Protocol (MCP) server.

Exposes CineForge's instruction-driven video production pipelines, dynamic tool
registry (186+ tools), Backlot studio board, and Layer 2/3 skills to any MCP
client (Claude Desktop, Cursor, Antigravity, Claude Code, Windsurf, VS Code).

By default runs in Smart Hybrid mode (~20 curated workflow + selector +
universal dispatcher tools) to avoid overwhelming LLM tool contexts. Pass
``--all-tools`` or ``--profile <capabilities>`` to expose individual tools
directly.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from mcp.server.mcpserver import MCPServer

from cineforge_cli.core import apply_workspace_override, build_doctor_report
from cineforge_mcp import __version__
from lib.paths import (
    ensure_workspace_initialized,
    get_agent_skills_dir,
    get_package_root,
    get_pipeline_defs_dir,
    get_projects_dir,
    get_skills_dir,
    get_styles_dir,
    get_workspace_root,
)

_SERVER_INSTRUCTIONS = (
    "You are driving CineForge, an instruction-driven AI video production studio. "
    "Follow Rule Zero from cineforge://guide (AGENT_GUIDE.md): "
    "1) Always call `cineforge_preflight` before any creative production work. "
    "2) Initialize a workspace with `cineforge_init_project` so all assets/artifacts live under projects/<project_id>/. "
    "3) Before executing any pipeline stage, call `cineforge_get_stage_guide(pipeline, stage)` and follow its director skill. "
    "4) Before calling a generation tool, inspect its `agent_skills` with `cineforge_get_tool_details` (or read cineforge://skills/layer3/<name>) and check cost via `cineforge_estimate_cost`. "
    "5) Persist checkpoints via `cineforge_save_checkpoint` and respect `human_approval_default` gates."
)


def _safe_child(root: Path, *parts: str) -> Path:
    """Resolve a path strictly inside *root*, rejecting traversal attempts."""
    clean_parts: list[str] = []
    for part in parts:
        if not part or "\x00" in part or "/" in part or "\\" in part or part in {".", ".."}:
            raise ValueError(f"Invalid path component: {part!r}")
        clean_parts.append(part)
    candidate = (root / Path(*clean_parts)).resolve()
    resolved_root = root.resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise ValueError("Path escapes allowed root")
    return candidate


def _tool_result_to_dict(tool_name: str, result: Any) -> dict[str, Any]:
    """Normalize a CineForge ToolResult object into a JSON-serializable dict."""
    return {
        "tool": tool_name,
        "success": bool(getattr(result, "success", False)),
        "data": getattr(result, "data", {}) or {},
        "artifacts": list(getattr(result, "artifacts", []) or []),
        "error": getattr(result, "error", None),
        "cost_usd": getattr(result, "cost_usd", 0.0),
        "duration_seconds": getattr(result, "duration_seconds", 0.0),
        "model": getattr(result, "model", None),
        "seed": getattr(result, "seed", None),
        "from_cache": bool(getattr(result, "from_cache", False)),
    }


def _execute_registry_tool(
    tool_name: str,
    inputs: Optional[dict[str, Any]] = None,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Look up a tool in ToolRegistry and either dry-run or execute it."""
    from tools.tool_registry import registry

    registry.ensure_discovered()
    tool = registry.get(tool_name)
    if tool is None:
        return {
            "tool": tool_name,
            "success": False,
            "error": f"Unknown tool {tool_name!r}. Use `cineforge_search_tools` to find valid tool names.",
        }

    payload = dict(inputs or {})
    if dry_run:
        return {
            "tool": tool_name,
            "success": True,
            "dry_run": tool.dry_run(payload),
        }

    result = tool.execute(payload)
    return _tool_result_to_dict(tool_name, result)


def _register_core_tools(mcp: MCPServer) -> None:
    """Register the curated Smart Hybrid workflow, discovery, and selector tools."""

    @mcp.tool()
    def cineforge_preflight() -> dict[str, Any]:
        """Run mandatory CineForge preflight discovery.

        Returns available composition runtimes (ffmpeg, remotion, hyperframes),
        capability readiness counts (configured/total), 1-minute env-var setup
        offers, runtime warnings, and active workspace paths.
        """
        from tools.tool_registry import registry

        registry.ensure_discovered()
        return {
            "workspace": {
                "package_root": str(get_package_root()),
                "workspace_root": str(get_workspace_root()),
                "projects_dir": str(get_projects_dir()),
            },
            "total_tools_discovered": len(registry.list_all()),
            "menu": registry.provider_menu_summary(),
        }

    @mcp.tool()
    def cineforge_doctor() -> dict[str, Any]:
        """Run full environment diagnostics (Python, FFmpeg, Node, Remotion, HyperFrames, and providers)."""
        return build_doctor_report()

    @mcp.tool()
    def cineforge_search_tools(
        capability: str = "",
        provider: str = "",
        available_only: bool = False,
        query: str = "",
        limit: int = 40,
    ) -> dict[str, Any]:
        """Search all discovered CineForge tools by capability, provider, availability, or keyword."""
        from tools.tool_registry import registry

        registry.ensure_discovered()
        q = query.strip().lower()
        matches: list[dict[str, Any]] = []

        for name in sorted(registry.list_all()):
            tool = registry.get(name)
            if tool is None:
                continue
            info = tool.get_info()
            if capability and info.get("capability") != capability:
                continue
            if provider and info.get("provider") != provider:
                continue
            if available_only and info.get("status") != "available":
                continue
            if q:
                haystack = " ".join(
                    [
                        name,
                        str(info.get("capability", "")),
                        str(info.get("provider", "")),
                        " ".join(str(x) for x in (info.get("best_for") or [])),
                    ]
                ).lower()
                if q not in haystack:
                    continue
            matches.append(
                {
                    "name": name,
                    "capability": info.get("capability"),
                    "provider": info.get("provider"),
                    "runtime": info.get("runtime"),
                    "status": info.get("status"),
                    "best_for": info.get("best_for", []),
                    "agent_skills": info.get("agent_skills", []),
                }
            )

        capped = matches[: max(1, min(limit, 200))]
        return {
            "total_matches": len(matches),
            "returned": len(capped),
            "tools": capped,
        }

    @mcp.tool()
    def cineforge_get_tool_details(tool_name: str) -> dict[str, Any]:
        """Inspect a tool's full contract: input_schema, output_schema, dependencies, and Layer 3 agent_skills."""
        from tools.tool_registry import registry

        registry.ensure_discovered()
        tool = registry.get(tool_name)
        if tool is None:
            return {"found": False, "error": f"Unknown tool: {tool_name!r}"}
        return {"found": True, "info": tool.get_info()}

    @mcp.tool()
    def cineforge_list_pipelines() -> dict[str, Any]:
        """List all available CineForge production pipelines from pipeline_defs/."""
        from lib.pipeline_loader import list_pipelines, load_pipeline_readonly

        items: list[dict[str, Any]] = []
        for name in sorted(list_pipelines()):
            try:
                manifest = load_pipeline_readonly(name)
                items.append(
                    {
                        "name": name,
                        "description": manifest.get("description", ""),
                        "stability": manifest.get("stability", "unknown"),
                        "stages": [s["name"] for s in manifest.get("stages", [])],
                    }
                )
            except Exception as exc:
                items.append({"name": name, "error": str(exc)})
        return {"pipelines": items}

    @mcp.tool()
    def cineforge_get_stage_guide(pipeline: str, stage: str) -> dict[str, Any]:
        """Load the pipeline manifest stage contract AND its Layer 2 director skill instructions."""
        from lib.pipeline_loader import load_pipeline_readonly

        manifest = load_pipeline_readonly(pipeline)
        stage_def = next((s for s in manifest.get("stages", []) if s.get("name") == stage), None)
        if stage_def is None:
            valid = [s.get("name") for s in manifest.get("stages", [])]
            return {
                "found": False,
                "error": f"Stage {stage!r} not in pipeline {pipeline!r}. Valid stages: {valid}",
            }

        skill_rel = stage_def.get("skill", "")
        skill_text = ""
        resolved_skill_rel = skill_rel
        if skill_rel:
            skills_root = get_skills_dir().resolve()
            pkg_root = get_package_root().resolve()
            candidates = [
                (skills_root, skills_root / (skill_rel if skill_rel.endswith(".md") else f"{skill_rel}.md")),
                (pkg_root, pkg_root / (skill_rel if skill_rel.endswith(".md") else f"{skill_rel}.md")),
            ]
            for base_root, cand in candidates:
                resolved = cand.resolve()
                if base_root in resolved.parents and resolved.is_file():
                    skill_text = resolved.read_text(encoding="utf-8", errors="replace")
                    resolved_skill_rel = resolved.relative_to(pkg_root).as_posix()
                    break

        return {
            "found": True,
            "pipeline": pipeline,
            "stage": stage,
            "stage_manifest": stage_def,
            "director_skill_path": resolved_skill_rel,
            "director_skill_markdown": skill_text,
        }

    @mcp.tool()
    def cineforge_init_project(
        project_id: str,
        title: str,
        pipeline_type: str,
        style_playbook: Optional[str] = None,
        open_board: bool = False,
    ) -> dict[str, Any]:
        """Initialize a canonical project workspace under projects/<project_id>/ and optionally launch Backlot."""
        from lib.checkpoint import init_project

        ensure_workspace_initialized()
        projects_root = get_projects_dir()
        project_dir = init_project(
            project_id,
            title=title,
            pipeline_type=pipeline_type,
            pipeline_dir=projects_root,
            style_playbook=style_playbook,
        )
        board_info: dict[str, Any] = {}
        if open_board:
            board_info = cineforge_open_backlot(project_id=project_id)

        return {
            "project_id": project_id,
            "project_dir": str(project_dir),
            "pipeline_type": pipeline_type,
            "backlot": board_info,
        }

    @mcp.tool()
    def cineforge_project_status(project_id: str) -> dict[str, Any]:
        """Inspect project progress, completed stages, next stage, and Backlot state summary."""
        from lib.checkpoint import (
            PROJECT_MARKER_FILENAME,
            get_completed_stages,
            get_latest_checkpoint,
            get_next_stage,
        )

        projects_root = get_projects_dir()
        project_dir = _safe_child(projects_root, project_id)
        if not project_dir.is_dir():
            return {"exists": False, "error": f"Project not found: {project_id!r}"}

        marker_path = project_dir / PROJECT_MARKER_FILENAME
        marker: dict[str, Any] = {}
        if marker_path.is_file():
            marker = json.loads(marker_path.read_text(encoding="utf-8"))

        pipeline_type = marker.get("pipeline_type")
        completed = get_completed_stages(projects_root, project_id, pipeline_type)
        next_stage = get_next_stage(projects_root, project_id, pipeline_type)
        latest = get_latest_checkpoint(projects_root, project_id)

        return {
            "exists": True,
            "project_id": project_id,
            "project_dir": str(project_dir),
            "marker": marker,
            "completed_stages": completed,
            "next_stage": next_stage,
            "latest_stage": latest.get("stage") if latest else None,
            "latest_status": latest.get("status") if latest else None,
        }

    @mcp.tool()
    def cineforge_save_checkpoint(
        project_id: str,
        stage: str,
        status: str,
        artifacts: dict[str, Any],
        pipeline_type: Optional[str] = None,
        style_playbook: Optional[str] = None,
        checkpoint_policy: str = "guided",
        human_approval_required: bool = False,
        human_approved: bool = False,
        review: Optional[dict[str, Any]] = None,
        cost_snapshot: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Write and schema-validate a CineForge stage checkpoint (enforcing human approval gates)."""
        from lib.checkpoint import write_checkpoint

        projects_root = get_projects_dir()
        path = write_checkpoint(
            projects_root,
            project_id,
            stage,
            status,
            artifacts,
            pipeline_type=pipeline_type,
            style_playbook=style_playbook,
            checkpoint_policy=checkpoint_policy,
            human_approval_required=human_approval_required,
            human_approved=human_approved,
            review=review,
            cost_snapshot=cost_snapshot,
            error=error,
            metadata=metadata,
        )
        return {"saved": True, "checkpoint_path": str(path), "stage": stage, "status": status}

    @mcp.tool()
    def cineforge_estimate_cost(tool_name: str, inputs: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Estimate cost (USD), runtime, and availability of a tool via dry_run without side effects."""
        return _execute_registry_tool(tool_name, inputs, dry_run=True)

    @mcp.tool()
    def cineforge_open_backlot(project_id: Optional[str] = None) -> dict[str, Any]:
        """Start the Backlot Matrix Studio local server (if needed) and open it in the browser."""
        from backlot.__main__ import _port, cmd_open

        rc = cmd_open(project_id)
        port = _port()
        url = f"http://127.0.0.1:{port}/p/{project_id}" if project_id else f"http://127.0.0.1:{port}/"
        return {"opened": rc == 0, "url": url, "exit_code": rc}

    @mcp.tool()
    def cineforge_generate_tts(
        text: str,
        output_path: str,
        language: str = "en",
        voice: Optional[str] = None,
        provider: Optional[str] = None,
        extra_inputs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Generate narration speech audio via `tts_selector` (or an explicit TTS tool)."""
        payload: dict[str, Any] = {
            "text": text,
            "output_path": output_path,
            "language": language,
            **(extra_inputs or {}),
        }
        if voice:
            payload["voice"] = voice
        if provider:
            payload["provider"] = provider
        return _execute_registry_tool("tts_selector", payload)

    @mcp.tool()
    def cineforge_generate_image(
        prompt: str,
        output_path: str,
        aspect_ratio: str = "16:9",
        provider: Optional[str] = None,
        extra_inputs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Generate an image via `image_selector` (or an explicit image tool)."""
        payload: dict[str, Any] = {
            "prompt": prompt,
            "output_path": output_path,
            "aspect_ratio": aspect_ratio,
            **(extra_inputs or {}),
        }
        if provider:
            payload["provider"] = provider
        return _execute_registry_tool("image_selector", payload)

    @mcp.tool()
    def cineforge_generate_video(
        prompt: str,
        output_path: str,
        duration: float = 5.0,
        aspect_ratio: str = "16:9",
        image_path: Optional[str] = None,
        provider: Optional[str] = None,
        extra_inputs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Generate a video clip via `video_selector` (text-to-video or image-to-video)."""
        payload: dict[str, Any] = {
            "prompt": prompt,
            "output_path": output_path,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            **(extra_inputs or {}),
        }
        if image_path:
            payload["image_path"] = image_path
        if provider:
            payload["provider"] = provider
        return _execute_registry_tool("video_selector", payload)

    @mcp.tool()
    def cineforge_generate_music(
        prompt: str,
        output_path: str,
        duration_seconds: float = 30.0,
        tool_name: Optional[str] = None,
        extra_inputs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Generate background music using the first available music generation tool (or explicit tool_name)."""
        from tools.tool_registry import registry

        registry.ensure_discovered()
        chosen = tool_name
        if not chosen:
            for candidate in registry.get_by_capability("music_generation"):
                if candidate.get_status().value == "available":
                    chosen = candidate.name
                    break
        if not chosen:
            return {
                "success": False,
                "error": "No music generation provider is configured. Check `music_library` for local tracks or configure a music API key.",
            }
        payload: dict[str, Any] = {
            "prompt": prompt,
            "output_path": output_path,
            "duration_seconds": duration_seconds,
            **(extra_inputs or {}),
        }
        return _execute_registry_tool(chosen, payload)

    @mcp.tool()
    def cineforge_compose_video(
        edit_decisions: dict[str, Any],
        asset_manifest: dict[str, Any],
        output_path: str,
        render_runtime: Optional[str] = None,
        extra_inputs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Render the final composed video using Remotion, HyperFrames, or FFmpeg via `video_compose`."""
        decisions = dict(edit_decisions)
        if render_runtime:
            decisions["render_runtime"] = render_runtime
        payload: dict[str, Any] = {
            "edit_decisions": decisions,
            "asset_manifest": asset_manifest,
            "output_path": output_path,
            **(extra_inputs or {}),
        }
        return _execute_registry_tool("video_compose", payload)

    @mcp.tool()
    def cineforge_analyze_video(
        video_path: str,
        extra_inputs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Analyze a reference or source video (transcript, scenes, pacing) via `video_analyzer`."""
        payload: dict[str, Any] = {"video_path": video_path, **(extra_inputs or {})}
        return _execute_registry_tool("video_analyzer", payload)

    @mcp.tool()
    def cineforge_transcribe_audio(
        audio_path: str,
        output_path: Optional[str] = None,
        language: Optional[str] = None,
        extra_inputs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Transcribe audio or video with timestamps using local Whisper (`transcriber`)."""
        payload: dict[str, Any] = {"audio_path": audio_path, **(extra_inputs or {})}
        if output_path:
            payload["output_path"] = output_path
        if language:
            payload["language"] = language
        return _execute_registry_tool("transcriber", payload)

    @mcp.tool()
    def cineforge_enhance_video(
        video_path: str,
        output_path: str,
        profile: str = "balanced",
        extra_inputs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Run non-destructive pre-export video quality enhancement (`video_quality_enhancer`)."""
        payload: dict[str, Any] = {
            "video_path": video_path,
            "output_path": output_path,
            "profile": profile,
            **(extra_inputs or {}),
        }
        return _execute_registry_tool("video_quality_enhancer", payload)

    @mcp.tool()
    def cineforge_execute_tool(
        tool_name: str,
        inputs: Optional[dict[str, Any]] = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Universal dispatcher: execute (or dry-run) ANY of CineForge's 186+ BaseTool implementations."""
        return _execute_registry_tool(tool_name, inputs, dry_run=dry_run)


def _register_dynamic_tools(
    mcp: MCPServer,
    *,
    all_tools: bool = False,
    profile: Optional[str] = None,
) -> int:
    """Optionally register individual BaseTools directly as MCP tools."""
    if not all_tools and not profile:
        return 0

    from tools.tool_registry import registry

    registry.ensure_discovered()
    allowed_caps = {c.strip() for c in profile.split(",") if c.strip()} if profile else None
    count = 0

    for name in sorted(registry.list_all()):
        tool = registry.get(name)
        if tool is None:
            continue
        if allowed_caps and tool.capability not in allowed_caps:
            continue

        info = tool.get_info()
        best_for = "; ".join(info.get("best_for") or [])
        props = list((info.get("input_schema") or {}).get("properties", {}).keys())
        desc = (
            f"[{info.get('capability')}/{info.get('provider')}] "
            f"{best_for or 'CineForge tool'}. "
            f"Input keys: {', '.join(props[:15]) or 'see cineforge_get_tool_details'}."
        )

        def _make_handler(bound_name: str):
            def _handler(inputs: Optional[dict[str, Any]] = None, dry_run: bool = False) -> dict[str, Any]:
                return _execute_registry_tool(bound_name, inputs, dry_run=dry_run)

            return _handler

        mcp.add_tool(
            _make_handler(name),
            name=f"tool_{name}",
            description=desc,
        )
        count += 1
    return count


def _register_resources(mcp: MCPServer) -> None:
    """Expose AGENT_GUIDE, pipelines, skills, styles, and Backlot state as MCP Resources."""

    @mcp.resource("cineforge://guide", mime_type="text/markdown")
    def read_agent_guide() -> str:
        """Primary CineForge agent operating contract (AGENT_GUIDE.md)."""
        path = get_package_root() / "AGENT_GUIDE.md"
        return path.read_text(encoding="utf-8", errors="replace")

    @mcp.resource("cineforge://context", mime_type="text/markdown")
    def read_project_context() -> str:
        """Shared project architecture and key file index (PROJECT_CONTEXT.md)."""
        path = get_package_root() / "PROJECT_CONTEXT.md"
        return path.read_text(encoding="utf-8", errors="replace")

    @mcp.resource("cineforge://pipelines/{name}", mime_type="text/yaml")
    def read_pipeline_manifest(name: str) -> str:
        """YAML manifest for a named CineForge pipeline."""
        clean = name[:-5] if name.endswith(".yaml") else name
        path = _safe_child(get_pipeline_defs_dir(), f"{clean}.yaml")
        return path.read_text(encoding="utf-8", errors="replace")

    @mcp.resource("cineforge://styles/{name}", mime_type="text/yaml")
    def read_style_playbook(name: str) -> str:
        """YAML definition for a visual style playbook."""
        clean = name[:-5] if name.endswith(".yaml") else name
        path = _safe_child(get_styles_dir(), f"{clean}.yaml")
        return path.read_text(encoding="utf-8", errors="replace")

    @mcp.resource("cineforge://skills/layer2/{category}/{name}", mime_type="text/markdown")
    def read_layer2_skill(category: str, name: str) -> str:
        """Layer 2 CineForge skill (core, creative, meta)."""
        fname = name if name.endswith(".md") else f"{name}.md"
        path = _safe_child(get_skills_dir(), category, fname)
        return path.read_text(encoding="utf-8", errors="replace")

    @mcp.resource("cineforge://skills/pipeline/{pipeline}/{stage}", mime_type="text/markdown")
    def read_pipeline_director_skill(pipeline: str, stage: str) -> str:
        """Pipeline stage director skill (e.g. animated-explainer / script)."""
        fname = stage if stage.endswith(".md") else f"{stage}-director.md"
        path = _safe_child(get_skills_dir(), "pipelines", pipeline, fname)
        return path.read_text(encoding="utf-8", errors="replace")

    @mcp.resource("cineforge://skills/layer3/{skill_name}", mime_type="text/markdown")
    def read_layer3_skill(skill_name: str) -> str:
        """Layer 3 vendor/technology skill (SKILL.md under .agents/skills/)."""
        base = get_agent_skills_dir()
        dir_cand = _safe_child(base, skill_name) / "SKILL.md"
        if dir_cand.is_file():
            return dir_cand.read_text(encoding="utf-8", errors="replace")
        file_cand = _safe_child(base, f"{skill_name}.md")
        return file_cand.read_text(encoding="utf-8", errors="replace")

    @mcp.resource("cineforge://projects/{project_id}/state", mime_type="application/json")
    def read_project_board_state(project_id: str) -> str:
        """Live Backlot board state JSON for a project."""
        from backlot.state import load_board_state

        project_dir = _safe_child(get_projects_dir(), project_id)
        return json.dumps(load_board_state(project_dir), indent=2)


def _register_prompts(mcp: MCPServer) -> None:
    """Expose high-value CineForge workflows as one-click MCP Prompts."""

    @mcp.prompt()
    def onboarding() -> str:
        """Check your CineForge capabilities and suggest ready-to-run video ideas."""
        return (
            "Call `cineforge_preflight` and read `cineforge://skills/layer2/meta/onboarding`. "
            "Summarize what capabilities and composition runtimes are ready right now (leading with what works), "
            "mention at most 2 quick unlocks if any, and offer 3 tailored starter prompts."
        )

    @mcp.prompt()
    def make_video(
        topic: str,
        platform: str = "youtube-shorts",
        duration: str = "60 seconds",
        language: str = "English",
    ) -> str:
        """Start a full pipeline-governed CineForge video production."""
        return (
            f"Produce a {duration} video about {topic!r} for {platform} in {language}. "
            "First call `cineforge_preflight` and `cineforge_list_pipelines` to pick the best pipeline. "
            "Present both Remotion and HyperFrames if available, present the music plan, initialize the workspace "
            "with `cineforge_init_project(..., open_board=True)`, and follow `cineforge_get_stage_guide` stage by stage."
        )

    @mcp.prompt()
    def science_explainer(language: str = "English", topic: str = "") -> str:
        """Launch the autonomous Science Explainer Shorts workflow."""
        topic_hint = f" around {topic!r}" if topic else ""
        return (
            f"Read `cineforge://skills/layer3/bengali-science-explainer` and `cineforge_preflight`. "
            f"Run the Science Explainer Shorts workflow in {language}{topic_hint}: research trending high-retention "
            "topics, propose the top 6 concepts, present the compact feature menu, and get single-gate approval before asset generation."
        )

    @mcp.prompt()
    def reference_video(reference_url_or_path: str, new_topic: str = "") -> str:
        """Analyze a reference video/Short/Reel and propose original concepts."""
        topic_clause = f" adapted for {new_topic!r}" if new_topic else ""
        return (
            f"Read `cineforge://skills/layer2/meta/video-reference-analyst` and `cineforge_preflight`. "
            f"Analyze `{reference_url_or_path}` using `cineforge_analyze_video`, summarize its hook, pacing, "
            f"structure, and style, then propose 3 differentiated original concepts{topic_clause}."
        )

    @mcp.prompt()
    def clip_stream(source_video_path: str, game_or_topic: str = "") -> str:
        """Extract viral 9:16 clips from a long stream, VOD, or podcast."""
        topic_clause = f" ({game_or_topic})" if game_or_topic else ""
        return (
            f"Read `cineforge://skills/layer3/stream-clips` and `cineforge_preflight`. "
            f"Process `{source_video_path}`{topic_clause} to detect high-energy moments, "
            "crop/stack into 9:16 vertical clips, and add synced word-level subtitles."
        )


def create_mcp_server(
    *,
    all_tools: bool = False,
    profile: Optional[str] = None,
) -> MCPServer:
    """Create and configure the CineForge MCPServer instance."""
    mcp = MCPServer(
        name="CineForge",
        instructions=_SERVER_INSTRUCTIONS,
        version=__version__,
    )
    _register_core_tools(mcp)
    _register_dynamic_tools(mcp, all_tools=all_tools, profile=profile)
    _register_resources(mcp)
    _register_prompts(mcp)
    return mcp


def serve_mcp(
    *,
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8766,
    all_tools: bool = False,
    profile: Optional[str] = None,
) -> None:
    """Run the CineForge MCP server over stdio or streamable-http."""
    server = create_mcp_server(all_tools=all_tools, profile=profile)
    if transport in ("http", "streamable-http"):
        server.run(transport="streamable-http", host=host, port=port)
        return
    if transport == "sse":
        server.run(transport="sse", host=host, port=port)
        return
    server.run(transport="stdio")


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for `cineforge-mcp` and `python -m cineforge_mcp`."""
    parser = argparse.ArgumentParser(
        prog="cineforge-mcp",
        description="Run the CineForge Model Context Protocol (MCP) server.",
    )
    parser.add_argument(
        "--workspace",
        "-w",
        default=None,
        help="Override CineForge workspace directory (sets CINEFORGE_HOME).",
    )
    parser.add_argument(
        "--transport",
        "-t",
        choices=("stdio", "streamable-http", "http", "sse"),
        default="stdio",
        help="MCP transport protocol (default: stdio).",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host (default: 127.0.0.1).")
    parser.add_argument("--port", "-p", type=int, default=8766, help="HTTP port (default: 8766).")
    parser.add_argument(
        "--all-tools",
        action="store_true",
        help="Expose every BaseTool directly in addition to Smart Hybrid tools.",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Comma-separated capability filter to expose directly (e.g. tts,image_generation).",
    )
    args = parser.parse_args(argv)
    apply_workspace_override(args.workspace)
    serve_mcp(
        transport=args.transport,
        host=args.host,
        port=args.port,
        all_tools=args.all_tools,
        profile=args.profile,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
