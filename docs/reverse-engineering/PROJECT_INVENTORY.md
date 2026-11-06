# OpenMontage Matrix — Project Inventory & Codebase Audit

**Date:** 2026-11-06  
**Project Name:** OpenMontage Matrix (CineForge)  
**Repository:** https://github.com/calesthio/OpenMontage.git / https://github.com/mrsandipmandal/CineForge.git  
**Runtime:** Python 3.14.4, Node.js v24.22.1, npm 11.19.1, FFmpeg 7.1  
**Baseline Test Results:** 2,241 passed, 10 skipped, 3 xfailed, 1 warning (100% core test suite health).

---

## 1. Top-Level Directory Structure

| Directory / File | Description | Core Artifacts / Responsibilities |
|---|---|---|
| `lib/` | Core runtime infrastructure (Python) | `checkpoint.py`, `config_model.py`, `pipeline_loader.py`, `media_profiles.py`, `scoring.py`, `asset_cache.py`, `events.py` |
| `tools/` | 155 BaseTool implementations across 26 capabilities | `base_tool.py`, `tool_registry.py`, `cost_tracker.py`, subpackages: `audio/`, `avatar/`, `video/`, `graphics/`, `enhancement/`, `analysis/`, `character/`, `subtitle/`, `capture/`, `publishers/` |
| `pipeline_defs/` | Declarative YAML pipeline definitions (13 pipelines) | `animated-explainer.yaml`, `cinematic.yaml`, `character-animation.yaml`, `talking-head.yaml`, `avatar-spokesperson.yaml`, `localization-dub.yaml`, etc. |
| `schemas/` | JSON Schemas for contract enforcement | `artifacts/` (19 schemas), `checkpoints/`, `pipelines/`, `styles/`, `tools/` |
| `skills/` | Layer 2: Pipeline & stage director instructions | `pipelines/<pipeline>/<stage>-director.md`, `core/`, `creative/`, `meta/` (`reviewer.md`, `checkpoint-protocol.md`) |
| `.agents/skills/` | Layer 3: External technology and model guides | 50+ domain skills (Remotion, HyperFrames, FLUX, Kling, ElevenLabs, Azure, Fish Audio, etc.) |
| `backlot/` | Live production board server & SPA frontend | `server.py` (FastAPI + SSE), `state.py`, `ui/board.html`, `ui/board.js`, `ui/board.css`, `ui/library.js` |
| `styles/` | Visual style playbooks | Playbook YAMLs (`clean-professional`, `flat-motion-graphics`, etc.) + `playbook_loader.py` |
| `remotion-composer/` | React/Remotion video composition package | React scenes, spring physics, canvas rendering, typography, chart components |
| `ink-theater/` | Hand-drawn procedural animation engine | Ink doodle animator, mocap choreography |
| `tests/` | Comprehensive test suite (2,254 collected items) | `tests/contracts/`, `tests/lib/`, `tests/tools/`, `tests/backlot/`, `tests/qa/`, `tests/eval/`, `tests/styles/` |
| `projects/` | Runtime production workspace (gitignored) | Per-project directories with `artifacts/`, `assets/`, `renders/`, `checkpoints`, `events.jsonl` |
| `sample-files/` | Reusable identity reference library (to be built) | Voice profiles (`voices/`), character references (`faces/`), character definitions (`characters/`), index (`manifests/`) |

---

## 2. Core Python Infrastructure Modules (`lib/`)

### `lib/checkpoint.py`
- **Responsibility:** Pipeline state persistence, stage status lifecycle (`in_progress`, `awaiting_human`, `completed`, `failed`), history archiving, prerequisite validation, and gate enforcement.
- **Key Functions:**
  - `init_project(project_id, title, pipeline_type)`: Seeds workspace with `project.json`.
  - `write_checkpoint(root, project_id, stage, status, ...)`: Enforces that gated stages require `human_approved=True` to complete; archives old versions to `history/checkpoint_<stage>_<ts>.json`.
  - `read_checkpoint(root, project_id, stage)`: Loads canonical stage state.
  - `get_next_stage(root, project_id, pipeline_type)`: Determines resume point.
- **Contract Dependencies:** `schemas/checkpoints/checkpoint.schema.json`, `schemas/artifacts/`.
- **Testing:** `tests/lib/test_checkpoint_*.py`, `tests/contracts/test_phase0_contracts.py`.

### `lib/config_model.py`
- **Responsibility:** Pydantic models for `config.yaml` validating LLM settings, budget governance, checkpoint policy, render defaults, and system paths.
- **Public Classes:** `CineForgeConfig`, `LLMConfig`, `BudgetConfig`, `CheckpointConfig`, `OutputConfig`, `PathsConfig`.
- **Testing:** `tests/contracts/test_phase0_contracts.py`.

### `lib/pipeline_loader.py`
- **Responsibility:** YAML loading and validation for manifests under `pipeline_defs/`.
- **Key Functions:** `load_pipeline(name)`, `list_pipelines()`, `get_stage_order()`, `get_required_tools()`, `get_stage_skill()`.
- **Testing:** `tests/contracts/test_pipeline_catalog.py`, `tests/contracts/test_phase0_contracts.py`.

### `lib/media_profiles.py`
- **Responsibility:** Platform delivery specs (YouTube Landscape 16:9 4K/1080p, TikTok/Reels Vertical 9:16 1080x1920, Instagram Square 1:1, Cinema 2.39:1).
- **Key Functions:** `get_profile(name)`, `ffmpeg_output_args(profile)`.
- **Testing:** `tests/contracts/test_phase0_contracts.py`.

### `lib/scoring.py` & `tools/cost_tracker.py`
- **Responsibility:** Scored ranking of providers across capability, quality, latency, reliability, and cost; budget reservation and reconciliation.
- **Key Classes:** `CostTracker`, `BudgetMode`, `ScoredCandidate`.
- **Testing:** `tests/tools/test_cost_tracker_governance.py`, `tests/tools/test_scoring.py`.

---

## 3. Tool Architecture (`tools/`)

### `tools/base_tool.py`
- **Base Class:** `BaseTool` (abstract base class).
- **Public Contract Attributes:**
  - `name`: Unique snake_case string identifier.
  - `version`: SemVer string.
  - `tier`: `ToolTier` enum (`CORE`, `VOICE`, `ENHANCE`, `GENERATE`, `SOURCE`, `ANALYZE`, `PUBLISH`).
  - `capability`: String capability category.
  - `provider`: String service provider identifier.
  - `runtime`: `ToolRuntime` enum (`LOCAL`, `LOCAL_GPU`, `API`, `HYBRID`).
  - `stability`: `ToolStability` enum (`EXPERIMENTAL`, `BETA`, `PRODUCTION`).
  - `dependencies`: List of prefixes: `cmd:<bin>`, `env:<VAR>`, `python:<pkg>`.
  - `input_schema` & `output_schema`: JSON Schemas.
  - `supports`: Dictionary of supported boolean flags.
  - `fallback_tools`: Ordered list of fallback tool names.
  - `agent_skills`: List of Layer 3 skills in `.agents/skills/`.
- **Abstract Method:** `execute(inputs: dict[str, Any]) -> ToolResult`.
- **Return Type:** `ToolResult` dataclass with `success`, `data`, `artifacts`, `error`, `cost_usd`, `duration_seconds`, `seed`, `model`.

### `tools/tool_registry.py`
- **Singleton Registry:** `ToolRegistry` auto-discovers all tools in `tools/` using `pkgutil.walk_packages()`.
- **Discovered Tools:** 155 tools across 26 capabilities.
- **Key Methods:**
  - `discover()` / `ensure_discovered()`
  - `get_by_capability(cap)`
  - `get_by_provider(provider)`
  - `get_available()`
  - `support_envelope()`
  - `provider_menu()` / `provider_menu_summary()`

---

## 4. Backlot Server & UI (`backlot/`)

### Backend (`backlot/server.py` & `backlot/state.py`)
- **Server:** FastAPI application on `127.0.0.1` protected by `TrustedHostMiddleware` and path sanitization.
- **Endpoints:**
  - `GET /api/health`
  - `GET /api/projects`
  - `GET /api/project/{project_id}/state`
  - `GET /api/project/{project_id}/events` (SSE stream for live reactivity)
  - `GET /api/library/events` (SSE stream)
  - `GET /thumb/{project_id}/{file_path}` (on-demand image/video poster frame generation)
  - `GET /media/{project_id}/{file_path}` (streaming media delivery)
  - `GET /p/{project_id}` & `GET /` (SPA pages)
- **State Derivation:** Pure read-only join of `project.json`, `checkpoint_*.json`, `history/`, `artifacts/*.json`, `events.jsonl`, `assets/`, `renders/`.

### Frontend (`backlot/ui/`)
- Vanilla ES Modules (`board.js`, `library.js`, `lib.js`) and CSS (`board.css`).
- Zero external JS frameworks (no React/Vue dependency in UI layer).
- Real-time reactivity via Server-Sent Events (`EventSource`).
- Storyboard filmstrip join of `scene_plan` × `script` × `asset_manifest`.
- Script screenplay rendering, Decision log audit viewer, Cost meter, and Replay scrubber.

---

## 5. Artifact Schemas (`schemas/artifacts/`)

Canonical JSON schemas enforcing stage-to-stage data contracts:
1. `research_brief.schema.json`
2. `brief.schema.json`
3. `proposal_packet.schema.json`
4. `script.schema.json`
5. `scene_plan.schema.json`
6. `asset_manifest.schema.json`
7. `edit_decisions.schema.json`
8. `render_report.schema.json`
9. `final_review.schema.json`
10. `publish_log.schema.json`
11. `decision_log.schema.json`
12. `cost_log.schema.json`
13. `character_design.schema.json`
14. `rig_plan.schema.json`
15. `pose_library.schema.json`
16. `action_timeline.schema.json`
17. `character_qa_report.schema.json`
18. `source_media_review.schema.json`
19. `video_analysis_brief.schema.json`

---

## 6. Current Limitations & Dead/Unfinished Code

1. **Identity System Absence:** No centralized library existed under `sample-files/` for voice recordings and character face references.
2. **Bengali/Hindi Voice Matrix Ambiguity:** Although documentation mentions Indic language support, concrete provider tooling lacks unified reference-audio cloning and explicit Bengali script/dialect validation tools.
3. **Face Consistency Pipeline Hook:** Image/video generators did not receive unified face-reference conditioning parameters from a shared character catalog.
4. **Backlot UI Styling:** Current theme is dark slate/charcoal with neutral clapper-board accents, lacking the requested high-density Matrix terminal command-center aesthetic, Voice Lab, and Face Lab panels.
