# CineForge Matrix — Architecture Map

**Date:** 2026-11-06  
**Status:** Validated against Codebase  

---

## 1. The 3-Layer Knowledge Architecture

CineForge Matrix follows an **agent-first, instruction-driven architecture**. The AI agent is the orchestration engine and creative director. Python code provides execution capabilities (tools) and state persistence (checkpoints).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        LAYER 2: CINEFORGE AGENTS                       │
│  Pipeline Manifests (YAML) + Stage Director Skills (Markdown)          │
│  - idea-director.md         - script-director.md   - asset-director.md │
│  - scene_plan-director.md   - edit-director.md     - compose-director  │
│  Meta Skills: reviewer.md, checkpoint-protocol.md                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
           Directs execution and    │ Uses tool registry
           orchestrates decisions   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        LAYER 1: PYTHON RUNTIME                         │
│  - Tool Registry (singleton auto-discovery of 155 BaseTool classes)    │
│  - Checkpoint Engine (lib/checkpoint.py, history archiving)           │
│  - Cost Tracker (tools/cost_tracker.py: estimate, reserve, reconcile)  │
│  - Config & Profiles (lib/config_model.py, lib/media_profiles.py)      │
│  - Capability Selectors (tts_selector, video_selector, image_selector) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
           Bridges tools to         │ References vendor rules
           external capabilities    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        LAYER 3: VENDOR KNOWLEDGE                       │
│  External Domain Skills (.agents/skills/):                             │
│  - flux-best-practices, bfl-api, seedance-2-0, kling-official          │
│  - elevenlabs, azure-text-to-speech, fish-audio-tts, doubao-tts        │
│  - remotion, hyperframes, gsap-core, threejs-world-generation          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Production State Machine & Checkpoint Lifecycle

All productions execute along a strict state machine:

```
[research] ──► [proposal] ──► [script] ──► [scene_plan] ──► [assets] ──► [edit] ──► [compose] ──► [publish]
     │              │             │              │             │           │           │            │
     ▼              ▼             ▼              ▼             ▼           ▼           ▼            ▼
research_brief  proposal_packet  script      scene_plan   asset_manifest edit_decisions render_report publish_log
```

### Stage Execution Protocol

1. **State Discovery:** Agent invokes `lib.checkpoint.get_next_stage(root, project_id, pipeline_type)`.
2. **Instruction Load:** Agent reads `skills/pipelines/<pipeline>/<stage>-director.md`.
3. **Execution:** Agent invokes Python tools registered in `ToolRegistry` (`execute(inputs)`).
4. **Self-Review:** Agent runs `skills/meta/reviewer.md` (maximum 2 passes).
5. **Gating & Checkpointing:**
   - If `human_approval_default: true` in manifest: writes checkpoint with `status: "awaiting_human"`, outputs summary and costs to user, and ends turn.
   - Upon explicit user approval: writes checkpoint with `status: "completed"` and `human_approved: true`.
   - If non-gated: writes `status: "completed"`.
   - Prior checkpoint version is preserved in `projects/<project-id>/history/checkpoint_<stage>_<timestamp>.json`.

---

## 3. Project Workspace Isolation (`projects/<project-id>/`)

Every video production is confined to an isolated directory structure:

```
projects/<project-id>/
├── project.json                # Project metadata marker (id, title, pipeline, created_at)
├── checkpoint_<stage>.json     # Active checkpoint per completed/current stage
├── events.jsonl                # Telemetry event stream (tool starts, completions, costs)
├── decision_log.json           # Canonical append-only log of human/agent decisions
├── artifacts/                  # Canonical JSON artifacts
│   ├── brief.json
│   ├── proposal_packet.json
│   ├── script.json
│   ├── scene_plan.json
│   ├── asset_manifest.json
│   ├── edit_decisions.json
│   └── render_report.json
├── assets/                     # Concrete binary media generated for this project
│   ├── images/                 # Generated keyframes and stills (PNG/JPEG)
│   ├── video/                  # Generated video shots (MP4)
│   ├── audio/                  # Narration clips, voiceover, stem tracks (WAV/MP3)
│   ├── music/                  # BGM track
│   └── subtitles.srt           # Time-aligned subtitles
├── history/                    # Archived checkpoint versions for rollback & replay
└── renders/
    └── final.mp4               # Final assembled composite deliverable
```

---

## 4. Backlot Real-Time Observer Architecture

The Backlot UI acts strictly as a **passive observer**:

```
[Agent writes file to disk]
           │
           ▼
[watchfiles in lib/events.py / backlot/server.py]
           │
           ▼ (debounced SSE event)
[SSE: /api/project/{id}/events]
           │
           ▼
[Backlot Browser UI (ui/board.js)]
           │
           ▼ (HTTP GET /api/project/{id}/state)
[Derives state from checkpoints, artifacts, events, assets]
           │
           ▼
[Updates Filmstrip, Screenplay, Gate Modals, Meter, and History]
```

### Architectural Guarantees Preserved:
1. **Never block, never break:** A corrupted or in-flight JSON file never crashes the server; fallback representation is rendered.
2. **DNS-rebinding protection:** Server binds to `127.0.0.1` and enforces `TrustedHostMiddleware` (`localhost`, `127.0.0.1`).
3. **Path traversal immunity:** All media and thumbnail requests are resolved against canonical project bounds using `Path.resolve().relative_to(project_dir.resolve())`.
