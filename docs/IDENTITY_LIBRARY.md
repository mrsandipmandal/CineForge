# CineForge Matrix — Identity Library Architecture & Guide

The **Identity Library** (`lib/identity_library.py`) provides a persistent, reusable, privacy-first repository for voice and facial identities across all CineForge Matrix pipelines.

It ensures that characters, narrators, and actors remain visually and acoustically consistent across different scenes, projects, and production pipelines without duplicate uploads or hardcoded file paths.

---

## 1. Directory Structure

The identity repository is rooted at `sample-files/`:

```
sample-files/
├── README.md                           # Documentation and usage guide
├── voices/                             # Voice identity profiles
│   ├── dr_elena_vance/
│   │   ├── metadata.json               # Voice metadata, language, consent status
│   │   └── samples/                    # WAV/MP3/FLAC reference audio files
│   ├── aarti_patel/
│   │   ├── metadata.json
│   │   └── samples/
│   └── anirban_roy/
│       ├── metadata.json
│       └── samples/
├── faces/                              # Face & visual character profiles
│   ├── elena_vance/
│   │   ├── metadata.json               # Appearance tags, traits, consent
│   │   ├── references/                 # PNG/JPEG/WEBP multi-angle reference photos
│   │   │   ├── front.png
│   │   │   ├── left_quarter.png
│   │   │   └── expression_smile.png
│   │   └── thumbnails/                 # Auto-generated 256x256 preview thumbnails
│   └── aarti_patel/
│       ├── metadata.json
│       ├── references/
│       └── thumbnails/
├── characters/                         # Cross-modal linked profiles
│   ├── elena_vance.json                # Links face `elena_vance` + voice `dr_elena_vance`
│   └── aarti_patel.json
└── manifests/
    └── identity-index.json             # Fast-lookup cached index with SHA-256 hashes
```

---

## 2. Technical Capabilities

### Media Probing & Inspection
- **Audio Probing (`probe_audio`)**: Extracts duration, sample rate (Hz), channel count, format, and calculates a SHA-256 fingerprint. Supported formats: `.wav`, `.mp3`, `.ogg`, `.flac`, `.m4a`, `.aac`.
- **Image Probing (`probe_image`)**: Uses PIL (or native binary parsing fallback) to extract width, height, aspect ratio, color mode, format, and SHA-256 hash. Supported formats: `.png`, `.jpg`, `.jpeg`, `.webp`.
- **Thumbnail Generation (`generate_thumbnail`)**: Automatically downscales reference portraits to maximum 256×256 pixels with preserved aspect ratio, saving directly to `thumbnails/` for fast Backlot UI rendering.

### Integrity & Deduplication
- Every reference file is hashed with SHA-256 during indexing.
- Duplicate files across different names or folders are detected to prevent redundant storage and unnecessary remote API uploads.

### Path Traversal & Sandbox Protection
- All path lookups are passed through `_safe_resolve(target_path, root_dir)`.
- If an input path contains relative sequences (e.g. `../../etc/passwd` or absolute path escapes), `_safe_resolve` raises a `ValueError` which the Backlot server converts to HTTP 403 Forbidden.
- Production projects can link identities safely via `link_to_project(profile_id, project_assets_dir)` which copies or symlinks verified references into `projects/<project_id>/assets/references/`.

---

## 3. Privacy, Consent & Git Hygiene

1. **Zero Unintended Cloud Exposure**: No identity asset is ever sent to a third-party AI provider (ElevenLabs, Kling, HeyGen, Fal) without explicit user configuration and consent check (`consent_verified: true`).
2. **Explicit Consent Flag**: Each profile's `metadata.json` requires:
   ```json
   "consent": {
     "verified": true,
     "consent_type": "actor_release",
     "notes": "Authorized for documentary narration"
   }
   ```
3. **Strict `.gitignore` Boundaries**:
   The repository `.gitignore` explicitly ignores private audio recordings (`*.wav`, `*.mp3`, etc.) and photos (`*.jpg`, `*.png`) inside `sample-files/voices/` and `sample-files/faces/references/`, while keeping `.gitkeep` anchors and `metadata.json` / `identity-index.json` manifests tracked.

---

## 4. Programmatic API (`lib/identity_library.py`)

```python
from lib.identity_library import IdentityLibrary

lib = IdentityLibrary()

# 1. List available profiles
voices = lib.list_voice_profiles()
faces = lib.list_face_profiles()
characters = lib.list_characters()

# 2. Inspect a profile
voice = lib.get_voice_profile("dr_elena_vance")
print(voice.name, voice.language, voice.samples)

# 3. Create or update a voice profile
lib.register_voice_profile(
    profile_id="sourav_ganguly",
    name="Sourav",
    language="bn-IN",
    description="Bengali sports commentary voice",
    sample_files=["/path/to/sample1.wav"],
    consent_verified=True,
    consent_notes="Authorized voice talent release"
)

# 4. Link to active production project
lib.link_to_project("voices", "dr_elena_vance", project_assets_dir)
```

---

## 5. Tool Integration

- **Voice Identity Tool**: `tools.audio.voice_identity.VoiceIdentity` — command-line and agent tool for listing, inspecting, validating, verifying consent, and preparing reference files.
- **Character Identity Tool**: `tools.avatar.character_identity.CharacterIdentity` — manages character views (`front`, `left_quarter`, `right_quarter`, `expression`), view completeness, and generates multi-provider conditioning bundles.
- **TTS Selector**: `tools.audio.tts_selector.TTSSelector` — accepts `voice_profile_id` and automatically routes to the best provider supporting that language and cloning requirement.
