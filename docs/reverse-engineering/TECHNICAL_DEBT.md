# OpenMontage Matrix — Technical Debt & Codebase Health Audit

**Date:** 2026-11-06  
**Auditor:** Principal Software Architect  

---

## 1. Technical Debt Inventory

| Category | Finding | File(s) Impacted | Severity | Remediation Strategy |
|---|---|---|---|---|
| **Environment Dependency** | `google-genai` library was missing in the baseline environment, causing 18 contract tests to fail until installed via pip. | `tools/video/veo_video.py`, `tools/audio/google_music.py`, `tools/graphics/google_imagen.py` | Medium | Package installed cleanly in `~/.local/lib/python3.14/site-packages`; tests now pass 100%. Add explicit pin to `requirements.txt`. |
| **Deprecated Tool Names** | Legacy aliases `image_gen` (deprecated in favor of `image_selector`), `tts_cloud`, `tts_engine`, `video_gen` exist in historical notes. | `tools/graphics/image_gen.py`, `tools/audio/` | Low | Kept as backward-compatible wrappers or soft aliases; registry marks them deprecated. |
| **Duplicated Video Trimming Logic** | `video_trimmer.py` and `silence_cutter.py` both invoke FFmpeg subprocesses directly without sharing a common FFmpeg runner abstraction. | `tools/video/video_trimmer.py`, `tools/video/silence_cutter.py` | Low | Share common FFmpeg command execution in `tools/video/_shared.py`. |
| **Hardcoded Language Lookups** | Some TTS adapters hardcoded language strings rather than using a centralized BCP-47 language tag resolver (e.g. `bn-IN`, `hi-IN`, `en-US`). | `tools/audio/azure_tts.py`, `tools/audio/google_tts.py` | Medium | Create shared `lib/locale_utils.py` with standard BCP-47 mapping and pronunciation hints. |
| **Backlot UI Extensibility** | UI was a single monolithic `board.js` file (48KB). Adding tabs or panels requires clean modularization. | `backlot/ui/board.js`, `backlot/ui/board.css` | Medium | Modularize Matrix UI panels cleanly into distinct view components while preserving single-file load compatibility. |
| **Unanchored Face Reference Inputs** | Video tools lacked a standardized schema property for passing multi-image character reference dictionaries (`front_ref`, `side_ref`, `expression_refs`). | `tools/video/seedance_video.py`, `tools/video/kling_video.py` | High | Introduce standardized `character_references` schema field in `tools/avatar/` and `tools/video/`. |

---

## 2. Backward Compatibility Guardrails

1. Existing pipeline manifests (`animated-explainer`, `cinematic`, `talking-head`, etc.) must not have required fields altered in a breaking manner.
2. Projects created before the identity system must continue to load and render cleanly in Backlot without crashing on missing identity fields.
3. Checkpoint schema version remains `1.0` with optional metadata extensions.
