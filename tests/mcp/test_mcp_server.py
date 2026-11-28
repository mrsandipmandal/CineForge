"""Protocol-level integration tests for the CineForge MCP server."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from cineforge_mcp.server import create_mcp_server


@asynccontextmanager
async def _open_session(*, all_tools: bool = False, profile: str | None = None):
    server = create_mcp_server(all_tools=all_tools, profile=profile)
    lowlevel = server._lowlevel_server
    async with create_client_server_memory_streams() as ((c_read, c_write), (s_read, s_write)):
        async with anyio.create_task_group() as tg:
            tg.start_soon(
                lowlevel.run,
                s_read,
                s_write,
                lowlevel.create_initialization_options(),
            )
            async with ClientSession(c_read, c_write) as session:
                await session.initialize()
                yield session
            tg.cancel_scope.cancel()


@pytest.mark.asyncio
async def test_smart_hybrid_tools_resources_and_prompts(tmp_path: Path, monkeypatch) -> None:
    ws = tmp_path / "mcp-ws"
    monkeypatch.setenv("CINEFORGE_HOME", str(ws))
    monkeypatch.setenv("CINEFORGE_PROJECTS_DIR", str(ws / "projects"))
    import lib.paths as paths_mod

    monkeypatch.setattr(paths_mod, "PROJECTS_DIR", ws / "projects")

    async with _open_session() as session:
        tools_res = await session.list_tools()
        tool_names = {t.name for t in tools_res.tools}
        assert "cineforge_preflight" in tool_names
        assert "cineforge_execute_tool" in tool_names
        assert "cineforge_get_stage_guide" in tool_names
        assert len(tool_names) <= 30

        res_list = await session.list_resources()
        assert any(str(r.uri) == "cineforge://guide" for r in res_list.resources)

        guide = await session.read_resource("cineforge://guide")
        assert "Rule Zero" in guide.contents[0].text

        pipe_yaml = await session.read_resource("cineforge://pipelines/animated-explainer")
        assert "animated-explainer" in pipe_yaml.contents[0].text

        l2 = await session.read_resource("cineforge://skills/layer2/meta/onboarding")
        assert "Onboarding" in l2.contents[0].text

        l3 = await session.read_resource("cineforge://skills/layer3/ffmpeg")
        assert "ffmpeg" in l3.contents[0].text.lower()

        stage_guide = await session.call_tool(
            "cineforge_get_stage_guide",
            {"pipeline": "animated-explainer", "stage": "script"},
        )
        sg_payload = json.loads(stage_guide.content[0].text)
        assert sg_payload["found"] is True
        assert sg_payload["director_skill_markdown"]

        init_out = await session.call_tool(
            "cineforge_init_project",
            {
                "project_id": "mcp-demo-proj",
                "title": "MCP Demo Project",
                "pipeline_type": "animated-explainer",
                "open_board": False,
            },
        )
        init_payload = json.loads(init_out.content[0].text)
        assert Path(init_payload["project_dir"]).is_dir()

        status_out = await session.call_tool(
            "cineforge_project_status",
            {"project_id": "mcp-demo-proj"},
        )
        status_payload = json.loads(status_out.content[0].text)
        assert status_payload["exists"] is True
        assert status_payload["next_stage"] == "research"

        dry_out = await session.call_tool(
            "cineforge_execute_tool",
            {"tool_name": "tts_selector", "inputs": {"text": "Hello"}, "dry_run": True},
        )
        dry_payload = json.loads(dry_out.content[0].text)
        assert dry_payload["success"] is True
        assert dry_payload["dry_run"]["tool"] == "tts_selector"

        prompts = await session.list_prompts()
        prompt_names = {p.name for p in prompts.prompts}
        assert {"onboarding", "make_video", "science_explainer"}.issubset(prompt_names)


@pytest.mark.asyncio
async def test_mcp_profile_and_all_tools_modes() -> None:
    async with _open_session(profile="tts") as session:
        tools_res = await session.list_tools()
        names = {t.name for t in tools_res.tools}
        assert "tool_tts_selector" in names
        assert "tool_video_compose" not in names

    async with _open_session(all_tools=True) as session:
        tools_res = await session.list_tools()
        names = {t.name for t in tools_res.tools}
        assert len(names) > 150
        assert "tool_tts_selector" in names
        assert "tool_video_compose" in names


@pytest.mark.asyncio
async def test_mcp_structured_errors_for_invalid_inputs(tmp_path: Path, monkeypatch) -> None:
    ws = tmp_path / "mcp-err-ws"
    monkeypatch.setenv("CINEFORGE_HOME", str(ws))
    monkeypatch.setenv("CINEFORGE_PROJECTS_DIR", str(ws / "projects"))
    import lib.paths as paths_mod

    monkeypatch.setattr(paths_mod, "PROJECTS_DIR", ws / "projects")

    async with _open_session() as session:
        bad_stage = json.loads(
            (await session.call_tool("cineforge_get_stage_guide", {"pipeline": "no-such-pipe", "stage": "script"}))
            .content[0]
            .text
        )
        assert bad_stage["found"] is False
        assert bad_stage["error"]

        bad_proj = json.loads(
            (await session.call_tool("cineforge_project_status", {"project_id": "../escape"})).content[0].text
        )
        assert bad_proj["exists"] is False
        assert bad_proj["error"]

        bad_init = json.loads(
            (
                await session.call_tool(
                    "cineforge_init_project",
                    {"project_id": "../bad", "title": "Bad", "pipeline_type": "animated-explainer"},
                )
            )
            .content[0]
            .text
        )
        assert bad_init["success"] is False
        assert bad_init["error"]

        await session.call_tool(
            "cineforge_init_project",
            {"project_id": "p-gate", "title": "Gate Test", "pipeline_type": "animated-explainer"},
        )
        gate_err = json.loads(
            (
                await session.call_tool(
                    "cineforge_save_checkpoint",
                    {
                        "project_id": "p-gate",
                        "stage": "script",
                        "status": "completed",
                        "artifacts": {},
                    },
                )
            )
            .content[0]
            .text
        )
        assert gate_err["saved"] is False
        assert "GATE VIOLATION" in gate_err["error"]


@pytest.mark.asyncio
async def test_mcp_curated_wrappers_forward_exact_tool_schema_keys(monkeypatch) -> None:
    captured: list[tuple[str, dict, bool]] = []

    def _fake_exec(tool_name: str, inputs=None, *, dry_run: bool = False):
        captured.append((tool_name, dict(inputs or {}), dry_run))
        return {"tool": tool_name, "success": True, "captured": dict(inputs or {})}

    monkeypatch.setattr("cineforge_mcp.server._execute_registry_tool", _fake_exec)

    async with _open_session() as session:
        await session.call_tool(
            "cineforge_generate_tts",
            {"text": "Hello", "output_path": "a.wav", "language": "bn", "provider": "sarvam"},
        )
        await session.call_tool(
            "cineforge_generate_image",
            {"prompt": "Space", "output_path": "i.png", "provider": "bfl"},
        )
        await session.call_tool(
            "cineforge_generate_video",
            {"prompt": "Galaxy", "output_path": "v.mp4", "duration": 6, "image_path": "ref.png", "provider": "kling"},
        )
        await session.call_tool(
            "cineforge_compose_video",
            {"edit_decisions": {"cuts": []}, "asset_manifest": {}, "output_path": "out.mp4", "render_runtime": "ffmpeg"},
        )
        await session.call_tool("cineforge_analyze_video", {"video_path": "clip.mp4"})
        await session.call_tool(
            "cineforge_transcribe_audio",
            {"audio_path": "narration.wav", "output_path": "/tmp/transcript/out.json", "language": "en"},
        )
        await session.call_tool(
            "cineforge_enhance_video",
            {"video_path": "raw.mp4", "output_path": "enh.mp4", "profile": "cinematic"},
        )

    by_tool = {name: payload for name, payload, _ in captured}
    assert by_tool["tts_selector"]["language_code"] == "bn"
    assert by_tool["tts_selector"]["preferred_provider"] == "sarvam"
    assert "provider" not in by_tool["tts_selector"]

    assert by_tool["image_selector"]["preferred_provider"] == "bfl"
    assert by_tool["video_selector"]["duration"] == "6"
    assert by_tool["video_selector"]["reference_image_path"] == "ref.png"
    assert by_tool["video_selector"]["preferred_provider"] == "kling"

    assert by_tool["video_compose"]["operation"] == "render"
    assert by_tool["video_compose"]["edit_decisions"]["render_runtime"] == "ffmpeg"

    assert by_tool["video_analyzer"]["source"] == "clip.mp4"
    assert by_tool["transcriber"]["input_path"] == "narration.wav"
    assert by_tool["transcriber"]["output_dir"] == "/tmp/transcript"
    assert by_tool["video_quality_enhancer"]["input_path"] == "raw.mp4"
