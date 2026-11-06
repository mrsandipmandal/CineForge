# CineForge Matrix — End-to-End Execution Flow

**Date:** 2026-11-06  
**Status:** Comprehensive Pipeline Lifecycle Reference  

---

## 1. Lifecycle Overview

```
User Idea
   │
   ▼
[Stage 0: Preflight & Discovery]
   │  - Discovers 155 tools from ToolRegistry
   │  - Evaluates hardware (GPU/VRAM) and configured env keys
   │  - Surfaces Provider Menu summary to user
   ▼
[Stage 1: Proposal / Idea]
   │  - Selects pipeline manifest (YAML)
   │  - Establishes narrative hook, duration, style playbook
   │  - Locks render_runtime (FFmpeg, Remotion, HyperFrames)
   │  - Artifact: brief.json or proposal_packet.json
   │  - Checkpoint: awaiting_human -> User approves
   ▼
[Stage 2: Script]
   │  - Reads script-director.md
   │  - Generates narration, scene beats, and word timing estimates
   │  - Artifact: script.json (validates against script.schema.json)
   │  - Checkpoint: awaiting_human -> User approves
   ▼
[Stage 3: Scene Plan & Identity Association]
   │  - Reads scene_plan-director.md
   │  - Maps script sections to visual shots
   │  - Binds Voice Profile and Character Identity references
   │  - Artifact: scene_plan.json (validates against scene_plan.schema.json)
   │  - Checkpoint: awaiting_human -> User approves
   ▼
[Stage 4: Asset Generation]
   │  - Reads asset-director.md + Layer 3 vendor skills
   │  - Estimates budget with CostTracker
   │  - Calls TTS with voice profile (cloning or matched voice)
   │  - Generates shots with character face references
   │  - Updates partial_progress in checkpoint after each shot
   │  - Reconciles cost in CostTracker
   │  - Artifact: asset_manifest.json
   │  - Checkpoint: awaiting_human (Filmstrip review) -> User approves
   ▼
[Stage 5: Edit Decisions]
   │  - Reads edit-director.md
   │  - Aligns audio timestamps, cuts, overlays, and color grading
   │  - Artifact: edit_decisions.json
   ▼
[Stage 6: Video Composition]
   │  - Reads compose-director.md
   │  - Dispatches to locked render_runtime:
   │      * FFmpeg (direct stream mux / concat / Ken Burns)
   │      * Remotion (React component rendering via remotion-composer)
   │      * HyperFrames (HTML/GSAP kinetic canvas rendering)
   │  - Generates renders/final.mp4
   │  - Artifact: render_report.json
   ▼
[Stage 7: Final Review & Publishing]
   │  - Self-review against brief delivery promise
   │  - Checkpoint: completed -> Final delivery
```

---

## 2. Preflight & Capability Discovery Deep Dive

Before generating any creative output, the agent runs discovery:

```python
from tools.tool_registry import registry
registry.discover()
summary = registry.provider_menu_summary()
```

The summary computes:
1. `composition_runtimes`: Availability of `ffmpeg`, `remotion`, `hyperframes`.
2. `capabilities`: Ratio of `configured` to `total` providers for each capability family.
3. `setup_offers`: Quick 1-minute configuration items (missing `.env` variables).
4. `runtime_warnings`: Hardware or dependency constraints (e.g. VRAM requirements).

---

## 3. Cost Governance Protocol

```
1. PRE-CHECK:
   estimated_cost = tool.estimate_cost(inputs)
   cost_tracker.reserve(tool.name, estimated_cost)

2. EXECUTION:
   result = tool.execute(inputs)

3. POST-CHECK:
   actual_cost = result.cost_usd
   cost_tracker.reconcile(tool.name, estimated_cost, actual_cost)
   events.log_tool_call(tool.name, actual_cost, result.duration_seconds)
```

If `budget.mode == "cap"` and the reserve exceeds remaining funds, `BudgetExceededError` halts execution until the human adjusts the budget or approves an override.

---

## 4. Checkpoint State Transition Rules

Every stage transition adheres to the state machine in `lib/checkpoint.py`:

```
          [pending]
             │
             ▼
       [in_progress] ──(partial progress updates)
             │
             ├───► [failed]
             │
      (gated stage?)
        /          \
     YES            NO
      │              │
      ▼              │
[awaiting_human]     │
      │ (approval)   │
      ▼              ▼
       [completed] ◄─┘
```

- Any attempt to mark a gated stage `completed` without `human_approved=True` raises `CheckpointValidationError` (Gate Violation).
- Checkpoints write directly to `projects/<project-id>/checkpoint_<stage>.json`.
- Superseded versions are archived into `projects/<project-id>/history/checkpoint_<stage>_<timestamp>.json`.
