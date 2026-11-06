# CineForge Matrix — Face & Character Identity Studio

The **Face & Character Identity Studio** provides unified visual character management, multi-angle reference libraries, and cross-scene character consistency across all generative image and video pipelines.

---

## 1. Six Distinct Visual Identity Operations

CineForge Matrix explicitly distinguishes between six distinct facial processing operations to maintain architectural clarity and honest reporting:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   VISUAL IDENTITY TAXONOMY                            │
├──────────────────────────┬─────────────────────────────────────────────┤
│ 1. Reference Management  │ Storage, probing, hashing, and thumbnails   │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 2. Character Consistency │ Multi-view image conditioning for diffusion │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 3. Talking-Head Anim     │ Still portrait animated by driving audio    │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 4. Video Lip Sync        │ Re-syncing mouth movements in moving video  │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 5. Face Replacement      │ Authorized identity swap onto source body   │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 6. Face Restoration      │ GFPGAN / CodeFormer upscaling & sharpening  │
└──────────────────────────┴─────────────────────────────────────────────┘
```

> **Important**: No generative model guarantees 100% mathematical face consistency across dynamic video cuts. CineForge Matrix maximizes consistency by delivering structured multi-angle conditioning bundles, consistent character visual descriptors, and fixed reference seeds to providers supporting image conditioning (such as Kling, Seedance 2.5, and Wan2.1).

---

## 2. Face Library Organization

Face profiles are stored in `sample-files/faces/<character_id>/`:

```
sample-files/faces/elena_vance/
├── metadata.json              # Physical attributes, consent, view registry
├── references/                # High-resolution original portraits
│   ├── front.png              # Direct frontal view (essential)
│   ├── left_quarter.png       # Left three-quarter profile
│   ├── right_quarter.png      # Right three-quarter profile
│   └── expression_smile.png   # Specific facial expression
└── thumbnails/                # Automatically generated 256x256 UI previews
    ├── front.png
    ├── left_quarter.png
    └── right_quarter.png
```

### Profile Metadata Example (`metadata.json`)

```json
{
  "character_id": "elena_vance",
  "name": "Dr. Elena Vance",
  "views": {
    "front": "sample-files/faces/elena_vance/references/front.png",
    "left_quarter": "sample-files/faces/elena_vance/references/left_quarter.png",
    "right_quarter": "sample-files/faces/elena_vance/references/right_quarter.png",
    "expression_smile": "sample-files/faces/elena_vance/references/expression_smile.png"
  },
  "attributes": {
    "age": 34,
    "hair": "Dark brown, shoulder-length, tied in a low bun",
    "eyes": "Hazel",
    "features": "Square jawline, light freckles over nose bridge",
    "attire": "Charcoal blazer over white minimalist lab coat"
  },
  "default_prompt": "Dr. Elena Vance, 34-year-old female lead astrophysicist, hazel eyes, dark brown hair in a low bun, charcoal blazer, cinematic lighting, photorealistic 8k",
  "consent": {
    "verified": true,
    "consent_type": "model_release",
    "notes": "Verified photo release on file for cinematic character reference"
  }
}
```

---

## 3. Character Consistency Conditioning

When creating scenes featuring a character, the `CharacterIdentity` tool (`tools/avatar/character_identity.py`) exports tailored conditioning bundles via:

```python
bundle = character_tool.generate_conditioning_bundle(
    character_id="elena_vance",
    target_provider="seedance"  # or "kling", "wan", "talking_head"
)
```

### Provider-Specific Conditioning Adaptations:
- **Seedance 2.5 / 2.0 (Atlas Cloud)**: Transmits primary frontal reference and prompt augmentation incorporating character visual attributes.
- **Kling Video (Direct API)**: Prepares multi-reference image list (`image_url` / base64 payload) for Kling image-to-video reference conditioning.
- **Wan2.1 (ComfyUI)**: Prepares IP-Adapter conditioning image paths and weight settings (recommended strength: `0.75 - 0.85`).
- **Talking Head (SadTalker / MuseTalk)**: Supplies the frontal portrait as `source_image` alongside driver audio from `sample-files/voices/`.

---

## 4. Cross-Modal Characters (`sample-files/characters/`)

Characters unify visual appearance and vocal identity into a single entity:

```json
{
  "character_id": "elena_vance",
  "name": "Dr. Elena Vance",
  "face_profile_id": "elena_vance",
  "voice_profile_id": "dr_elena_vance",
  "role": "Lead Astrophysicist and Principal Investigator",
  "description": "Brilliant quantum astrophysicist investigating anomalies at the edge of the solar system.",
  "metadata": {
    "created_at": "2026-11-06T00:00:00Z",
    "verified": true
  }
}
```

When a scene plan specifies `character_id: "elena_vance"`, both the narration TTS (`dr_elena_vance`) and the scene image generation (`elena_vance` reference photos) are locked automatically.
