# OpenMontage Matrix — Upgrade & Migration Guide

This guide details the process for migrating existing CineForge / OpenMontage installations to **OpenMontage Matrix**, outlining architectural guarantees, backward compatibility, and the setup of reusable identity profiles.

---

## 1. Compatibility Guarantees

OpenMontage Matrix was engineered under strict non-destructive upgrade principles:

| System Component | Compatibility Status | Notes |
| :--- | :---: | :--- |
| **Stage Checkpoints** (`checkpoint_<stage>.json`) | **100% Compatible** | The state machine, gate validation, prerequisite rules, and history archiving in `lib/checkpoint.py` are preserved intact. |
| **Pipeline Manifests** (`pipeline_defs/*.yaml`) | **100% Compatible** | Existing YAML manifests continue to execute without changes. |
| **Artifact Schemas** | **Additive & Optional** | `scene_plan.schema.json` and `asset_manifest.schema.json` have added optional fields (`voice_profile_id`, `character_id`, `identity`, `reference_media_used`, `consent_verified`). Existing artifacts without these fields remain 100% valid. |
| **Tools & Registries** (`tools/`) | **100% Compatible** | All existing tools continue to inherit `BaseTool` and discover through `ToolRegistry`. New tools (`voice_identity`, `character_identity`) operate cleanly alongside existing providers. |
| **Backlot UI & Server** (`backlot/`) | **100% Compatible** | Existing endpoints (`/api/project/*`, `/api/events`, etc.) are unchanged. New endpoints (`/api/identity/*`, `/identity-media/*`) provide additive functionality. |

---

## 2. Upgrading an Existing Installation

### Step 1: Pull the Latest Upgrade Branch
```bash
git checkout feature/openmontage-matrix-upgrade
```

### Step 2: Verify Dependencies
Ensure the recommended runtime dependencies are installed:
```bash
# Python dependencies
pip install -r requirements.txt

# If using Google GenAI or Azure TTS capabilities:
pip install google-genai azure-cognitiveservices-speech pillow

# Node.js check (HyperFrames requires Node.js >= 22)
node -v
```

### Step 3: Configure Environment Variables
Copy and update your `.env` file from `.env.example`:
```bash
# Multilingual TTS and Voice Cloning keys (optional, depending on chosen provider)
ELEVENLABS_API_KEY=your_key_here
FISH_AUDIO_API_KEY=your_key_here
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=eastus

# Image and Video reference generation keys (optional)
ATLASCLOUD_API_KEY=your_atlas_key
FAL_KEY=your_fal_key
KLING_API_KEY=your_kling_key
```

---

## 3. Initializing the Identity Library

1. **Verify Default Structure**:
   The identity library is rooted at `sample-files/`:
   ```bash
   sample-files/
   ├── voices/
   ├── faces/
   ├── characters/
   └── manifests/
   ```

2. **Index Existing Sample Files**:
   Run the Python indexing script to scan files, extract media metadata, and generate thumbnails:
   ```bash
   python -c "from lib.identity_library import IdentityLibrary; lib = IdentityLibrary(); idx = lib.update_index(); print(f'Indexed {len(idx[\"voices\"])} voices, {len(idx[\"faces\"])} faces')"
   ```

3. **Launch the Matrix Backlot Studio**:
   ```bash
   python -m backlot open <project-id>
   ```
   Open your browser to `http://localhost:8000/board.html?project=<project-id>` to access the Matrix Control Room, Voice Lab, and Face Lab.

---

## 4. Using Identities in Production Pipelines

### Specifying Voice in `scene_plan.json`
To lock a specific voice identity to scene narration, include `voice_profile_id` in the scene definition:

```json
{
  "scene_id": "scene_01",
  "name": "Introduction",
  "duration_sec": 8.0,
  "voice_profile_id": "anirban_roy",
  "narration": "ওপেনমন্টেজ ম্যাট্রিক্সের জগতে স্বাগতম।",
  "visual_description": "Futuristic server room bathed in phosphor green matrix luminescence."
}
```

### Specifying Character in `scene_plan.json`
To maintain visual face consistency across generative image and video cuts, specify `character_id`:

```json
{
  "scene_id": "scene_02",
  "name": "Dr. Vance in Lab",
  "duration_sec": 6.0,
  "character_id": "elena_vance",
  "voice_profile_id": "dr_elena_vance",
  "narration": "The atmospheric data confirms our hypothesis.",
  "visual_description": "Close-up portrait of Dr. Elena Vance observing holographic stellar charts."
}
```

The asset director and generation tools will automatically extract the multi-angle references from `sample-files/faces/elena_vance/references/` and pass them to supported providers.
