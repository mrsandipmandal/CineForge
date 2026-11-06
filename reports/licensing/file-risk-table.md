# CineForge File-by-File Copyright & Risk Audit Table

**Total Files Inspected:** 2240  
**Audit Date:** 2026-11-06  
**Upstream Reference:** `https://github.com/calesthio/OpenMontage` (Base commit: `d21f5d4`)  

## Classification Summary

| Code | Meaning | File Count | Percentage |
|---|---|---|---|
| **A** | Upstream Original (Copied verbatim from OpenMontage) | 1698 | 75.80% |
| **B** | Upstream Modified (Modified by CineForge / Renamed) | 215 | 9.60% |
| **C** | Derived Implementation (Architecturally based on upstream) | 0 | 0.00% |
| **D** | Independent Original (Authored independently in CineForge) | 43 | 1.92% |
| **E** | Third Party (External vendor/library asset) | 284 | 12.68% |
| **F** | Uncertain (Requires manual legal inquiry) | 0 | 0.00% |

## Risk Distribution

| Risk Level | Count | Description |
|---|---|---|
| **CRITICAL** | 1 | Immediate severe copyright/license violation (e.g. LICENSE replacement) |
| **HIGH** | 1911 | Direct copyleft exposure, missing attribution, unnotified modifications |
| **MEDIUM** | 21 | Independent module bound by copyleft when combined; CI/CD rule conflicts |
| **LOW** | 264 | Third-party skill notice or documentation attribution improvements needed |
| **NONE IDENTIFIED** | 43 | Properly documented third-party font/mocap or standalone sample assets |

---

## Detailed File-by-File Risk Table (Representative Critical, High & Architectural Modules)

Below is the file-by-file audit table detailing root configuration, core infrastructure, tools, backlot, and newly added modules. Complete 2,240-row provenance data is maintained in `file-provenance.csv`.

| No. | File Path | Source Classification | Copyright Owner | AGPL Status | Risk | Problem | Required Change |
|---|---|---|---|---|---|---|---|
| 1 | `LICENSE` | **B** | Original: Free Software Foundation / Calesthio; Replaced: Sandip Mandal | Apache-2.0 (Invalidly Replaced) | **CRITICAL** | Unauthorized license substitution; violates AGPL-3.0 Sec 4, 5, 7 | CRITICAL: Immediately restore GNU AGPL-3.0 text |
| 2 | `README.md` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Modified upstream code missing Section 5(a) prominent modification notices | Add AGPL-3.0 Sec 5(a) modification notice with date and changes; preserve upstream copyright |
| 3 | `README_zh-CN.md` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Modified upstream code missing Section 5(a) prominent modification notices | Add AGPL-3.0 Sec 5(a) modification notice with date and changes; preserve upstream copyright |
| 4 | `setup.py` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 5 | `requirements.txt` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 6 | `config.yaml` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 7 | `CONTRIBUTING.md` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 8 | `PROJECT_CONTEXT.md` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Modified upstream code missing Section 5(a) prominent modification notices | Add AGPL-3.0 Sec 5(a) modification notice with date and changes; preserve upstream copyright |
| 9 | `AGENT_GUIDE.md` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 10 | `AGENTS.md` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 11 | `lib/checkpoint.py` | **A** | Calesthio & OpenMontage Contributors | GNU AGPL-3.0 | **HIGH** | Root LICENSE was changed to Apache-2.0, creating severe licensing mismatch | Preserve upstream AGPL-3.0 license and attribution |
| 12 | `lib/pipeline_loader.py` | **A** | Calesthio & OpenMontage Contributors | GNU AGPL-3.0 | **HIGH** | Root LICENSE was changed to Apache-2.0, creating severe licensing mismatch | Preserve upstream AGPL-3.0 license and attribution |
| 13 | `lib/config_model.py` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 14 | `lib/scoring.py` | **A** | Calesthio & OpenMontage Contributors | GNU AGPL-3.0 | **HIGH** | Root LICENSE was changed to Apache-2.0, creating severe licensing mismatch | Preserve upstream AGPL-3.0 license and attribution |
| 15 | `lib/asset_cache.py` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 16 | `lib/identity_library.py` | **D** | Sandip Mandal | TBD (Tied to repo AGPL-3.0 copyleft when bundled) | **MEDIUM** | Bound by AGPL-3.0 copyleft when combined with OpenMontage core | Can be dual-licensed or licensed under AGPL-3.0 |
| 17 | `lib/media_profiles.py` | **A** | Calesthio & OpenMontage Contributors | GNU AGPL-3.0 | **HIGH** | Root LICENSE was changed to Apache-2.0, creating severe licensing mismatch | Preserve upstream AGPL-3.0 license and attribution |
| 18 | `tools/base_tool.py` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 19 | `tools/tool_registry.py` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 20 | `tools/cost_tracker.py` | **A** | Calesthio & OpenMontage Contributors | GNU AGPL-3.0 | **HIGH** | Root LICENSE was changed to Apache-2.0, creating severe licensing mismatch | Preserve upstream AGPL-3.0 license and attribution |
| 21 | `tools/audio/tts_selector.py` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Modified upstream code missing Section 5(a) prominent modification notices | Add AGPL-3.0 Sec 5(a) modification notice with date and changes; preserve upstream copyright |
| 22 | `tools/audio/voice_identity.py` | **D** | Sandip Mandal | TBD (Tied to repo AGPL-3.0 copyleft when bundled) | **MEDIUM** | Bound by AGPL-3.0 copyleft when combined with OpenMontage core | Can be dual-licensed or licensed under AGPL-3.0 |
| 23 | `tools/avatar/character_identity.py` | **D** | Sandip Mandal | TBD (Tied to repo AGPL-3.0 copyleft when bundled) | **MEDIUM** | Bound by AGPL-3.0 copyleft when combined with OpenMontage core | Can be dual-licensed or licensed under AGPL-3.0 |
| 24 | `tools/video/video_compose.py` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 25 | `tools/video/video_stitch.py` | **A** | Calesthio & OpenMontage Contributors | GNU AGPL-3.0 | **HIGH** | Root LICENSE was changed to Apache-2.0, creating severe licensing mismatch | Preserve upstream AGPL-3.0 license and attribution |
| 26 | `tools/video/hyperframes_compose.py` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 27 | `tools/graphics/image_selector.py` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 28 | `tools/video/video_selector.py` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 29 | `backlot/server.py` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Modified upstream code missing Section 5(a) prominent modification notices | Add AGPL-3.0 Sec 5(a) modification notice with date and changes; preserve upstream copyright |
| 30 | `backlot/state.py` | **A** | Calesthio & OpenMontage Contributors | GNU AGPL-3.0 | **HIGH** | Root LICENSE was changed to Apache-2.0, creating severe licensing mismatch | Preserve upstream AGPL-3.0 license and attribution |
| 31 | `backlot/ui/board.html` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Modified upstream code missing Section 5(a) prominent modification notices | Add AGPL-3.0 Sec 5(a) modification notice with date and changes; preserve upstream copyright |
| 32 | `backlot/ui/board.js` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Modified upstream code missing Section 5(a) prominent modification notices | Add AGPL-3.0 Sec 5(a) modification notice with date and changes; preserve upstream copyright |
| 33 | `backlot/ui/board.css` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Modified upstream code missing Section 5(a) prominent modification notices | Add AGPL-3.0 Sec 5(a) modification notice with date and changes; preserve upstream copyright |
| 34 | `remotion-composer/package.json` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 35 | `remotion-composer/src/index.tsx` | **A** | Calesthio & OpenMontage Contributors | GNU AGPL-3.0 | **HIGH** | Root LICENSE was changed to Apache-2.0, creating severe licensing mismatch | Preserve upstream AGPL-3.0 license and attribution |
| 36 | `ink-theater/THIRD_PARTY_NOTICES.md` | **A** | Calesthio & OpenMontage Contributors | GNU AGPL-3.0 | **HIGH** | Root LICENSE was changed to Apache-2.0, creating severe licensing mismatch | Preserve upstream AGPL-3.0 license and attribution |
| 37 | `ink-theater/assets/patrickhand.ttf` | **E** | Patrick Wagesreiter / Google Fonts | SIL OFL 1.1 | **NONE IDENTIFIED** | None (Properly documented in OFL notice) | Preserve OFL notices and font copyright |
| 38 | `ink-theater/mocap/catalog.json` | **E** | CMU Graphics Lab Motion Capture Database | CMU Free for all uses | **NONE IDENTIFIED** | None (Properly documented in THIRD_PARTY_NOTICES.md) | Retain CMU attribution notice |
| 39 | `schemas/artifacts/scene_plan.schema.json` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Modified upstream code missing Section 5(a) prominent modification notices | Add AGPL-3.0 Sec 5(a) modification notice with date and changes; preserve upstream copyright |
| 40 | `schemas/artifacts/asset_manifest.schema.json` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Modified upstream code missing Section 5(a) prominent modification notices | Add AGPL-3.0 Sec 5(a) modification notice with date and changes; preserve upstream copyright |
| 41 | `schemas/checkpoints/checkpoint.schema.json` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |
| 42 | `pipeline_defs/animated-explainer.yaml` | **A** | Calesthio & OpenMontage Contributors | GNU AGPL-3.0 | **HIGH** | Root LICENSE was changed to Apache-2.0, creating severe licensing mismatch | Preserve upstream AGPL-3.0 license and attribution |
| 43 | `pipeline_defs/cinematic.yaml` | **A** | Calesthio & OpenMontage Contributors | GNU AGPL-3.0 | **HIGH** | Root LICENSE was changed to Apache-2.0, creating severe licensing mismatch | Preserve upstream AGPL-3.0 license and attribution |
| 44 | `pipeline_defs/character-animation.yaml` | **A** | Calesthio & OpenMontage Contributors | GNU AGPL-3.0 | **HIGH** | Root LICENSE was changed to Apache-2.0, creating severe licensing mismatch | Preserve upstream AGPL-3.0 license and attribution |
| 45 | `.github/workflows/ci.yml` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Modified upstream code missing Section 5(a) prominent modification notices | Add AGPL-3.0 Sec 5(a) modification notice with date and changes; preserve upstream copyright |
| 46 | `.github/workflows/security.yml` | **D** | Sandip Mandal | Permissive / AGPL-3.0 | **MEDIUM** | security.yml erroneously denies AGPL-3.0 | Update dependency-review deny-list to avoid AGPL conflict |
| 47 | `.github/workflows/build.yml` | **D** | Sandip Mandal | Permissive / AGPL-3.0 | **MEDIUM** | security.yml erroneously denies AGPL-3.0 | Update dependency-review deny-list to avoid AGPL conflict |
| 48 | `.cursor/rules/cineforge.mdc` | **B** | Calesthio & OpenMontage Contributors | AGPL-3.0 | **LOW** | Renamed without modification notice | Add modification notice |
| 49 | `sample-files/manifests/identity-index.json` | **D** | Sandip Mandal | TBD (Tied to repo AGPL-3.0 copyleft when bundled) | **MEDIUM** | Bound by AGPL-3.0 copyleft when combined with OpenMontage core | Can be dual-licensed or licensed under AGPL-3.0 |
| 50 | `tests/lib/test_identity_library.py` | **D** | Sandip Mandal | AGPL-3.0 | **NONE IDENTIFIED** | None | Preserve test suite under AGPL-3.0 |
| 51 | `tests/tools/test_voice_identity.py` | **D** | Sandip Mandal | AGPL-3.0 | **NONE IDENTIFIED** | None | Preserve test suite under AGPL-3.0 |
| 52 | `tests/contracts/test_phase0_contracts.py` | **B** | Calesthio & OpenMontage Contributors (Modified by Sandip Mandal) | AGPL-3.0 (Upstream) / Apache-2.0 (Repo Claim) | **HIGH** | Wholesale renaming without preserving upstream copyright notices; lacks Section 5(a) change notice | Add AGPL-3.0 Sec 5(a) modification notice; retain upstream copyright |

---

### Additional Breakdown by Repository Subsystems

1. **`lib/` Infrastructure (7 files):**
   - 6 files (`checkpoint.py`, `pipeline_loader.py`, `config_model.py`, `scoring.py`, `asset_cache.py`, `media_profiles.py`) are Upstream Original (Class A) or Upstream Modified (Class B, rename only).
   - 1 file (`identity_library.py`) is Independent Original (Class D).
2. **`tools/` Tool Suites (157 files):**
   - 155 files are Upstream Original (Class A) or Upstream Modified (Class B, e.g. `tts_selector.py` with added identity hook).
   - 2 files (`tools/audio/voice_identity.py`, `tools/avatar/character_identity.py`) are Independent Original (Class D).
3. **`backlot/` Studio Server & UI (7 files):**
   - Python server (`server.py`) and UI (`board.js`, `board.css`, `index.html`) are Upstream Modified (Class B) with Matrix UI and Identity endpoints.
4. **`pipeline_defs/` & `schemas/` (33 files):**
   - 31 files are Upstream Original (Class A).
   - 2 schemas (`scene_plan.schema.json`, `asset_manifest.schema.json`) are Upstream Modified (Class B) to support identity fields.
5. **`sample-files/` (21 files):**
   - All 21 files are Independent Original (Class D).
6. **`tests/` (112 test modules):**
   - 107 test modules are Upstream Original (Class A).
   - 5 test modules are Independent Original (Class D).
