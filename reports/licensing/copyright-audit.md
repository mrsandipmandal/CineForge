# Comprehensive Copyright & Provenance Audit Report — CineForge

**Product:** CineForge AI Film Production Studio  
**Audit Date:** 2026-11-06  
**Auditor:** Senior Software Licensing Auditor & Software Architect  
**Upstream Repository:** `https://github.com/calesthio/OpenMontage.git`  
**Upstream Base Commit:** `d21f5d4eaa08422b09c7091757a05affcbabb35b`  
**Current Git Branch:** `feature/openmontage-matrix-upgrade` (`541dbbd`)  

---

## 1. Executive Provenance Overview

CineForge is **not** an independently developed application. Forensic git history and tree hash comparisons prove conclusively that CineForge is an immediate, direct downstream fork of `calesthio/OpenMontage` (authored under GNU AGPL-3.0).

### Key Historical Milestones:
1. **Commit `470cdd5` ("first commit" — Fri Nov 6 10:37:24 2026):**
   - The entire working tree of `calesthio/OpenMontage` at HEAD (`d21f5d4`) was committed into a brand new Git repository, severing all 900+ upstream git commits.
   - 2,196 files were imported verbatim.
   - The upstream `LICENSE` (AGPL-3.0, 864 lines) was deleted and replaced with Apache License 2.0 claiming "Copyright 2026 Sandip Mandal".
2. **Commit `94fdad2` ("refactor: rename project from OpenMontage to CineForge across codebase"):**
   - A global text replacement was executed across 210 files, replacing all occurrences of `OpenMontage`, `openmontage`, and `OPENMONTAGE` with `CineForge`, `cineforge`, and `CINEFORGE`.
3. **Commit `cca1d94` ("feat(matrix): OpenMontage Matrix studio upgrade..."):**
   - Added an identity subsystem (`lib/identity_library.py`, `tools/audio/voice_identity.py`, `tools/avatar/character_identity.py`), sample files (`sample-files/`), unit tests, and Matrix UI CSS/JS styling for Backlot.

---

## 2. Quantitative Provenance Breakdown

Across all **2,240 files** currently tracked in CineForge:

| Category | Description | Count | Percentage |
|---|---|---|---|
| **Class A — Upstream Original** | Verbatim copy of OpenMontage code (100% SHA match) | **1,698** | **75.80%** |
| **Class B — Upstream Modified** | Upstream code modified by CineForge (195 nominal renames + 20 functional changes + 1 LICENSE) | **216** | **9.64%** |
| **Class E — Third Party** | Vendored assets (SIL OFL fonts, CMU mocap, HeyGen & GSAP skills) | **284** | **12.68%** |
| **Class D — Independent Original** | Independently written by Sandip Mandal (Identity library, sample files, CI workflows, docs) | **43** | **1.92%** |
| **Total** | | **2,240** | **100.00%** |

> [!IMPORTANT]
> **98.08%** of the files in CineForge (2,197 files) represent code and intellectual property originating from `calesthio/OpenMontage` or upstream-vendored assets. Only **1.92%** of the codebase consists of net-new independent code.

---

## 3. Subsystem-by-Subsystem Provenance & Copyright Ownership

### 3.1 Core Architecture & Runtime (`lib/`)
- **Files:** `checkpoint.py`, `pipeline_loader.py`, `config_model.py`, `scoring.py`, `asset_cache.py`, `media_profiles.py`, `events.py`.
- **Provenance:** 100% authored by Calesthio and OpenMontage contributors.
- **Copyright Owner:** Calesthio & contributors.
- **Status:** Upstream Original (Class A) / Nominal Rename (Class B).
- **New Addition:** `lib/identity_library.py` (authored by Sandip Mandal; Class D).

### 3.2 Tool Suites (`tools/` — 157 tools)
- **Files:** `base_tool.py`, `tool_registry.py`, `cost_tracker.py`, and 154 specific tool adapters (`video_compose.py`, `video_stitch.py`, `audio_mixer.py`, `flux2_image.py`, `kling_video.py`, etc.).
- **Provenance:** 155 tools originate entirely from OpenMontage.
- **Modifications:** `tools/audio/tts_selector.py` modified to support voice identity profiles and language fallbacks.
- **New Additions:** `tools/audio/voice_identity.py` and `tools/avatar/character_identity.py` (Class D).

### 3.3 Living Storyboard (`backlot/`)
- **Files:** `server.py`, `state.py`, `ui/board.html`, `ui/board.js`, `ui/board.css`, `ui/library.js`.
- **Provenance:** Base architecture, API routes, SSE streaming, and SPA UI originate from OpenMontage.
- **Modifications:** Added Matrix terminal theme and `/api/identity/*` REST endpoints.
- **Classification:** Upstream Modified (Class B).

### 3.4 Composition Engines
- **Remotion Composer (`remotion-composer/`):** React components, spring physics, canvas rendering, and typography components originate 100% from OpenMontage.
- **Ink Theater (`ink-theater/`):** Hand-drawn doodle animation engine and CMU mocap integration originate 100% from OpenMontage.
- **HyperFrames Adapter (`tools/video/hyperframes_compose.py`):** Originated 100% from OpenMontage.

### 3.5 Declarative Pipelines & Schemas
- **`pipeline_defs/*.yaml` (13 pipelines):** All 13 production pipelines originate from OpenMontage.
- **`schemas/artifacts/*.json` (19 schemas):** 17 schemas are verbatim OpenMontage; 2 schemas (`scene_plan.schema.json`, `asset_manifest.schema.json`) were extended with identity fields.

---

## 4. Legal Copyright Analysis

### 4.1 Copyright Ownership under Berne Convention & 17 U.S.C.
- Copyright arises automatically when an original work of authorship is fixed in a tangible medium of expression (17 U.S.C. § 102).
- The upstream OpenMontage contributors did not sign a Contributor License Agreement (CLA) transferring copyright to a single foundation or company. As stated in upstream `CONTRIBUTING.md`: *"We do not require a Contributor License Agreement (CLA), Developer Certificate of Origin sign-off, or any separate contribution contract."*
- Consequently, each individual upstream contributor holds copyright in their respective contributions, which they licensed to downstream users under the GNU AGPL-3.0.
- **False Copyright Assertion:** The declaration in the root `LICENSE` file ("Copyright 2026 Sandip Mandal") asserting copyright over the entire repository is legally false. Sandip Mandal holds copyright **only** in the newly created contributions (the 43 Class D files and the incremental diffs in Class B files). Claiming copyright over others' work without authorization violates copyright law.

### 4.2 Derivative Work Doctrine
- Under 17 U.S.C. § 103, copyright in a derivative work extends only to the material contributed by the author of such work, as distinguished from the preexisting material employed in the work.
- The author has no independent copyright in the preexisting OpenMontage code.
- Furthermore, under 17 U.S.C. § 103(a), *"copyright in a compilation or derivative work employing preexisting material in which copyright subsists does not extend to any part of the work in which such material has been used unlawfully."* If preexisting code is used in violation of its license (e.g. by stripping AGPL-3.0), the derivative work lacks valid legal protection.

---

## 5. Feasibility of Personal-Use-Only & Non-Commercial Goal

The project owner wishes to enforce the following licensing policy:
- Personal individual use: Allowed.
- Educational & research use: Allowed.
- Commercial use, Paid SaaS, Paid hosting, Resale: Strictly prohibited.

### 5.1 Can this policy apply to Upstream AGPL Files?
**NO.** You do not own the copyright to upstream files. Upstream licensors granted rights under GNU AGPL-3.0, which explicitly guarantees commercial use rights (AGPL-3.0 Preamble: *"When we speak of free software, we are referring to freedom, not price... you have the freedom to distribute copies of free software (and charge for them if you wish)..."*). Adding a non-commercial clause is a violation of Section 7.

### 5.2 Can this policy apply to Modified Upstream Files?
**NO.** Under AGPL-3.0 Section 5(c), modified source versions must be licensed under AGPL-3.0 as a whole. You cannot attach a Non-Commercial rider to modifications of AGPL-3.0 code.

### 5.3 Can this policy apply to the Combined CineForge Application?
**NO.** CineForge as an integrated system combines the core runner, tool registry, pipeline manifests, and web UI. Under AGPL-3.0 copyleft, the combined work as a whole must be conveyed under AGPL-3.0.

### 5.4 Can this policy apply to Independently Authored Modules?
**YES, BUT ONLY IF COMPLETELY SEPARATED.**
- Sandip Mandal is the sole copyright owner of `lib/identity_library.py` and `sample-files/`.
- If `lib/identity_library.py` is extracted into an independent, standalone Python package, hosted in a separate repository, and distributed without any OpenMontage code, Sandip Mandal can license it under a proprietary Non-Commercial EULA.
- However, as soon as it is imported, linked, bundled, and executed inside CineForge, the combined application distribution falls under AGPL-3.0.

---

## 6. How Can CineForge Legally Become Closed-Source / Non-Commercial?

There are only two legal pathways:

### Pathway 1: Dual-Licensing / Commercial Relicensing from Upstream
- **Requirement:** Secure an explicit commercial, proprietary license from every single copyright holder of OpenMontage.
- **Feasibility:** Virtually 0%. OpenMontage has over 900 PRs and dozens of independent open-source contributors around the world with no CLA. Tracking down and getting unanimous agreement from 100% of contributors is practically impossible.

### Pathway 2: Complete Clean-Room Rewrite
- **Requirement:** Completely discard all 2,197 files originating from OpenMontage and rewrite the entire video production platform from scratch using clean-room specifications.
- **Feasibility:** High technical effort (~450,000 lines of code, estimated 6 to 12 person-months of senior engineering effort), but legally sound.
