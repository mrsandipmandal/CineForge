# CineForge Clean-Room Rewrite Roadmap

**Target:** Achieve 100% Proprietary, Closed-Source, or Personal-Use-Only / Non-Commercial Legal Status  
**Prerequisite:** All code originating from `calesthio/OpenMontage` (2,197 files, ~450,000 lines of code) must be completely eliminated.

---

## 1. Clean-Room Engineering Architecture & Methodology

To legally replace AGPL-3.0 code with a proprietary or Non-Commercial license without risking copyright contamination:

1. **Separation of Teams:**
   - **Specification Team (Dirty Room):** Reviews the existing CineForge/OpenMontage codebase, extracts functional requirements, API contracts, JSON schemas, tool interfaces, and pipeline execution flows, and writes a formal **Functional & Contract Specification Document**. The Specification Team does NOT write code.
   - **Implementation Team (Clean Room):** Engineers who have NEVER read, inspected, or contributed to OpenMontage or CineForge. They are given only the Functional Specification and implement the entire system from scratch.
2. **Preservation of Public APIs & Interfaces:**
   - Under US copyright law (*Google LLC v. Oracle America, Inc.*), declaring code, JSON schema property names, and method signatures necessary for interoperability are non-protectable elements or covered by fair use.
   - The Clean-Room implementation can preserve identical pipeline manifests, JSON schemas, and BaseTool method signatures (`execute(inputs) -> ToolResult`).

---

## 2. Subsystem Rewrite Matrix

| Priority | Module / Subsystem | Why It Must Be Replaced | New Implementation Needed | Dependencies | Complexity | Estimated Effort |
|---|---|---|---|---|---|---|
| **P1** | **Core Runtime Engine (`lib/`)** | `checkpoint.py`, `pipeline_loader.py`, `scoring.py`, `asset_cache.py`, `config_model.py` are 100% OpenMontage code. | Re-architect state persistence, YAML manifest loader, provider scoring algorithm, and filesystem asset cache from scratch. | Python standard library, Pydantic, PyYAML | **HIGH** | 4-6 weeks |
| **P1** | **Tool Framework (`tools/base_tool.py`, `tool_registry.py`)** | Abstract `BaseTool` class, dynamic auto-discovery registry, and `cost_tracker.py` originate from OpenMontage. | Implement independent plugin/tool discovery framework using standard Python entry points or custom decorators. | Python `pkgutil`, `importlib` | **MEDIUM** | 2-3 weeks |
| **P2** | **Composition & Rendering Core (`tools/video/video_compose.py`, `video_stitch.py`)** | `video_compose.py` contains ~2,954 lines of complex FFmpeg filtergraph orchestration, Ken Burns motion, and timing math. | Build a clean-room FFmpeg filtergraph builder and composition dispatch engine. | FFmpeg binary | **CRITICAL** | 6-8 weeks |
| **P2** | **Pipeline Manifests & Schemas (`pipeline_defs/`, `schemas/`)** | 13 pipelines and 19 JSON schemas define the operational contract. | Write original pipeline manifests and schemas preserving functional inputs/outputs. | jsonschema | **LOW** | 1-2 weeks |
| **P3** | **Living Storyboard Server & UI (`backlot/`)** | FastAPI backend (`server.py`, `state.py`) and SPA UI (`board.html`, `board.js`, `board.css`) are derived from OpenMontage. | Rebuild the live project dashboard, media thumbnail service, and SSE event streaming using a modern frontend framework (e.g. Svelte/Vue) or clean vanilla JS. | FastAPI, SSE | **HIGH** | 4-6 weeks |
| **P3** | **Remotion Composer (`remotion-composer/`)** | React composition components (`Explainer`, `CinematicRenderer`, `CaptionOverlay`, text cards, stat charts) are OpenMontage code. | Implement clean-room Remotion or Web Canvas animated components matching the visual spec. | Remotion, React | **HIGH** | 4-6 weeks |
| **P4** | **150+ Tool Provider Adapters (`tools/audio/`, `tools/video/`, `tools/graphics/`, `tools/avatar/`)** | All third-party adapters (Kling, Sora, ElevenLabs, Azure, FLUX, Wan2.1, etc.) originate from OpenMontage. | Implement clean-room REST/WebSocket API wrappers for each external vendor. | requests, websockets, SDKs | **HIGH** (Due to volume) | 8-12 weeks |
| **P4** | **Ink Theater Engine (`ink-theater/`)** | Vector doodle renderer and CMU mocap player originate from OpenMontage. | Rewrite procedural vector drawing engine or replace with standard SVG animation library. | Canvas / SVG API | **MEDIUM** | 3-4 weeks |
| **P5** | **Agent Skills & Stage Directors (`skills/`)** | All stage director prompt skills and reviewer instructions originate from OpenMontage. | Re-author all agent director skills with bespoke artistic directions and prompting strategies. | Markdown prompt templates | **MEDIUM** | 3-4 weeks |
| **P5** | **Comprehensive Test Suites (`tests/`)** | 2,240+ unit, contract, and QA tests originate from OpenMontage. | Author independent test suites verifying compliance with the functional specification. | pytest | **HIGH** | 4-6 weeks |

---

## 3. Total Rewrite Summary

- **Total Scope:** ~2,197 files (~450,000 lines of Python, TypeScript, JSON, YAML, and Markdown).
- **Estimated Engineering Resources:** 2 to 4 Senior Software Engineers for 6 to 9 months.
- **Estimated Cost:** $200,000 – $400,000 USD.
- **Conclusion:** A clean-room rewrite is technically possible, but it represents an immense engineering undertaking. Retaining GNU AGPL-3.0 compliance is vastly more practical, legally sound, and collaborative.
