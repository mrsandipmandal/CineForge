# CineForge Matrix — Upgrade Roadmap & Implementation Plan

**Date:** 2026-11-06  
**Status:** In Execution (Milestone A Complete)  

---

## Milestone Breakdown

### Milestone A: Repository Audit & Baseline Verification (PHASE 0 & 1) ✅
- [x] Inspect git status, branch, and runtime versions (Python 3.14.4, Node v24.22.1).
- [x] Read `AGENT_GUIDE.md`, `PROJECT_CONTEXT.md`, `README.md`, `CODEX.md`, `config.yaml`, `.env.example`.
- [x] Run full baseline test suite (2,254 tests, resolved missing `google-genai` library, 100% test health: 2,241 passed).
- [x] Generate comprehensive audit documentation under `docs/reverse-engineering/`:
  - `PROJECT_INVENTORY.md`
  - `ARCHITECTURE_MAP.md`
  - `EXECUTION_FLOW.md`
  - `TOOL_PROVIDER_MATRIX.md`
  - `PIPELINE_DEPENDENCY_MAP.md`
  - `UI_ARCHITECTURE.md`
  - `SECURITY_AUDIT.md`
  - `TECHNICAL_DEBT.md`
  - `UPGRADE_ROADMAP.md`

### Milestone B: Identity Library & File Discovery (PHASE 2 & PHASE 8) 🚀
- [ ] Create `sample-files/` structure:
  - `sample-files/README.md`
  - `sample-files/voices/` (profile directories with audio samples + metadata)
  - `sample-files/faces/` (character directories with reference images + metadata)
  - `sample-files/characters/` (unified character definitions linking voice and face)
  - `sample-files/manifests/identity-index.json`
- [ ] Create `lib/identity_library.py`:
  - Scan audio (WAV, MP3, M4A, FLAC, OGG) and images (PNG, JPG, WEBP).
  - Extract metadata: duration, sample rate, channels, resolution, aspect ratio, SHA-256 hash.
  - Safe path validation and duplicate detection.
  - Audio waveform and image thumbnail generator.
  - Ownership, permissions, and external cloud consent flags.
- [ ] Update `.gitignore` to prevent leaking personal media files while keeping directory scaffolds and sample READMEs intact.
- [ ] Write unit tests in `tests/lib/test_identity_library.py`.

### Milestone C: Voice Identity Studio (PHASE 3 & PHASE 7)
- [ ] Implement `tools/audio/voice_identity.py` (BaseTool) for discovering, validating, and managing voice profiles.
- [ ] Extend `tools/audio/tts_selector.py` with first-class `voice_profile` support.
- [ ] Verify Bengali (`bn-IN`), Hindi (`hi-IN`), and English (`en-US`) language handling:
  - ElevenLabs (multilingual voice cloning with audio sample references).
  - Fish Audio (zero-shot reference audio cloning).
  - Azure Speech Neural (`bn-IN-BashkarNeural`, `hi-IN-MadhurNeural`, `en-US-JennyNeural`).
  - Google Cloud TTS (`bn-IN-Standard-A`, `hi-IN-Neural2-A`).
  - Piper TTS (local offline fallback).
- [ ] Implement explicit consent verification workflow for voice cloning.
- [ ] Write comprehensive unit and contract tests in `tests/tools/test_voice_identity.py`.

### Milestone D: Face & Character Identity Studio (PHASE 4)
- [ ] Implement `tools/avatar/character_identity.py` (BaseTool) for character face references and profile management.
- [ ] Connect character references to generation tools (`talking_head`, `lip_sync`, `seedance_video`, `kling_video`, `wan_video`).
- [ ] Support front, left, right, and expression reference image roles.
- [ ] Differentiate clearly between:
  1. Face reference management
  2. Character consistency across scene generation
  3. Photo-to-talking-head animation
  4. Video lip-sync
  5. Authorized face replacement (consent-gated)
  6. Face restoration & enhancement (`face_restore`, `face_enhance`)
- [ ] Write tests in `tests/tools/test_character_identity.py`.

### Milestone E: Identity-Aware Video Pipeline Integration (PHASE 5)
- [ ] Extend canonical schemas (`schemas/artifacts/scene_plan.schema.json`, `schemas/artifacts/asset_manifest.schema.json`, `schemas/artifacts/brief.schema.json`) to carry `voice_profile` and `character_profile` references without breaking existing pipelines.
- [ ] Update pipeline director skills to prompt for and resolve identity selection.
- [ ] Verify checkpoint backward compatibility with legacy and identity-equipped projects.
- [ ] Write end-to-end contract tests in `tests/contracts/test_identity_pipeline.py`.

### Milestone F: Backlot Matrix Redesign (PHASE 6)
- [ ] Redesign `backlot/ui/board.css` with the Matrix Green-on-Black theme:
  - Deep black background (`#050805`, `#0A100C`, `#0D1510`).
  - Thin green glowing borders (`#193523`, `#00FF66`).
  - JetBrains Mono / IBM Plex Mono typography.
  - Subtle matrix digital rain canvas & terminal cursor animation (respecting `prefers-reduced-motion`).
- [ ] Add new views & panels in `backlot/ui/board.js` and `backlot/ui/library.js`:
  - `CONTROL ROOM` (Overview, active stage, pipeline tracker, live stats)
  - `VOICE LAB` (Interactive voice profiles, audio preview, waveform, language selection)
  - `FACE LAB` (Character identities, photo angles, thumbnails, consistency anchors)
  - `STORYBOARD` (Filmstrip, scene cards, audio scrubber)
  - `ASSETS`, `DECISIONS`, `PROVIDERS`, `SETTINGS`
- [ ] Extend `backlot/server.py` with identity endpoints:
  - `GET /api/identity/voices`
  - `GET /api/identity/faces`
  - `GET /api/identity/characters`
  - `GET /thumb/identity/{path:path}`
  - `GET /media/identity/{path:path}`
- [ ] Validate with browser tests and Playwright regressions.

### Milestone G: Full Integration Testing, Security Verification & Documentation (PHASE 9 & 10)
- [ ] Run full pytest suite across all contracts, tools, lib, and backlot tests.
- [ ] Verify zero API key exposure, no git leaks, complete path traversal immunity.
- [ ] Produce final documentation:
  - `docs/IDENTITY_LIBRARY.md`
  - `docs/VOICE_IDENTITY.md`
  - `docs/FACE_IDENTITY.md`
  - `docs/MATRIX_UI.md`
  - `docs/UPGRADE_MIGRATION.md`
  - Updated `README.md`, `PROJECT_CONTEXT.md`, `.env.example`.
