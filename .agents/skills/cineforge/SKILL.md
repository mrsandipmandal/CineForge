---
name: cineforge
description: >
  End-to-end AI video production studio skill for CineForge. Produces explainers,
  YouTube Shorts, Reels, talking-head edits, game stream clips, 2D/3D animations,
  and voice-cloned documentaries via CineForge MCP tools or the `cineforge` CLI.
---

# CineForge — Autonomous AI Video Studio

You are operating **CineForge**, an instruction-driven video production system.
Follow the CineForge pipeline contract whether connected via **MCP**, **CLI**, or a **local repo checkout**.

---

## 1. Detect How CineForge Is Available

Check in this exact order:

1. **CineForge MCP tools connected** (tools named `cineforge_preflight`, `cineforge_get_stage_guide`, `cineforge_execute_tool`, etc.):
   - **Use MCP tools directly** — no repo clone required.
   - Read `cineforge://guide` (or call `cineforge_list_pipelines` and `cineforge_get_stage_guide`) as your operating contract.
2. **`cineforge` CLI installed in terminal** (`which cineforge` or `cineforge --version`):
   - Inspect capabilities with `cineforge doctor --json`.
   - List pipelines with `cineforge pipelines list --json`.
   - Run tools with `cineforge tools run <name> --input '...'`.
   - Open the visual board with `cineforge studio <project_id>`.
3. **Inside a cloned CineForge repository** (`AGENT_GUIDE.md` + `tools/tool_registry.py` present):
   - Follow `AGENT_GUIDE.md` directly.
4. **Not installed yet**:
   - Offer the user a one-command setup:
     - `uv tool install cineforge && cineforge setup` (or `pip install cineforge && cineforge setup`)
     - Connect MCP automatically: `cineforge mcp install --client claude` (supports `claude`, `claude-code`, `cursor`, `antigravity`, `windsurf`, `vscode`).

---

## 2. Mandatory Preflight (Always First)

Before proposing concepts or generating media:

- **MCP:** call `cineforge_preflight()`.
- **CLI:** run `cineforge doctor --json`.

Translate the result for the user:
- Lead with what **works right now** (including `$0.00` offline/local options).
- Report composition runtimes separately (`ffmpeg`, `remotion`, `hyperframes`).
- Mention at most 1–2 easy env-var unlocks from `setup_offers` if relevant; never nag if the user prefers zero-key mode.

---

## 3. Route the Request to the Right Workflow

| User Request | Route |
|---|---|
| Vague / exploratory ("make me a video", "what can you do?") | MCP prompt `onboarding` / resource `cineforge://skills/layer2/meta/onboarding` |
| Science / mystery short ("make a science video", "/science-explainer") | MCP prompt `science_explainer` / resource `cineforge://skills/layer3/bengali-science-explainer` |
| Reference YouTube/Reel/TikTok URL or video ("make something like this") | Call `cineforge_analyze_video` + read `cineforge://skills/layer2/meta/video-reference-analyst` |
| Stream / VOD clipping ("clip this stream", "find best moments") | MCP prompt `clip_stream` / resource `cineforge://skills/layer3/stream-clips` |
| Faceless $0 vertical shorts ("Zack D. Films style", "what happens if") | Read `cineforge://skills/layer3/faceless-shorts` |
| Talking-head edit ("cut silences/mistakes", "add Nafay 3D graphics") | Read `cineforge://skills/layer3/ai-video-editor` |
| Standard explainer, cinematic, animation, avatar, demo, doc | Match a pipeline from `cineforge_list_pipelines()` and run stage by stage |

---

## 4. Non-Negotiable Production Rules

1. **Initialize a project workspace first:** Call `cineforge_init_project(project_id, title, pipeline_type, open_board=True)` (or `init_project` in Python) so all files stay under `projects/<project_id>/`.
2. **Read stage instructions before acting:** Always call `cineforge_get_stage_guide(pipeline, stage)` before running a stage.
3. **Read Layer 3 skill before generation:** Inspect `cineforge_get_tool_details(tool_name)` -> `agent_skills[]` and read `cineforge://skills/layer3/<name>` before crafting prompts for any video, image, TTS, or music tool.
4. **Present both Remotion and HyperFrames (if both available):** Never silently pick a default `render_runtime`. Explain both tradeoffs, recommend one, and wait for approval.
5. **Present the Music Plan at proposal time:** Check `music_library`, free music search, and music generation APIs upfront.
6. **Respect human approval gates & cost transparency:** Call `cineforge_estimate_cost` (`dry_run=True`) before paid batch calls, announce provider/model/cost beforehand, and persist checkpoints via `cineforge_save_checkpoint` pausing when `human_approval_default: true`.
