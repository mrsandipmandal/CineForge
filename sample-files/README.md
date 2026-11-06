# OpenMontage Matrix — Identity Reference Library (`sample-files/`)

This directory serves as the **reusable voice and face identity library** for OpenMontage Matrix productions.

## Directory Layout

```
sample-files/
├── README.md
├── voices/
│   ├── <profile-name>/
│   │   ├── samples/              # Reference audio files (.wav, .mp3, .flac)
│   │   └── metadata.json         # Voice profile attributes (language, speaker, consent)
│   └── ...
├── faces/
│   ├── <character-name>/
│   │   ├── references/           # Reference photos (.png, .jpg, .webp - front, side, expressions)
│   │   ├── thumbnails/           # Auto-generated preview thumbnails
│   │   └── metadata.json         # Character appearance, role, consent, generation prompts
│   └── ...
├── characters/
│   ├── <character-name>.json     # Character profiles binding voice + face identities
│   └── ...
└── manifests/
    └── identity-index.json       # Auto-generated catalog index of all scanned identities
```

## Supported Media Formats

- **Voice Samples:** `.wav` (preferred, uncompressed 16-bit/24-bit 22kHz-48kHz), `.mp3`, `.m4a`, `.flac`, `.ogg`.
- **Face References:** `.png` (lossless portrait), `.jpg`, `.jpeg`, `.webp`.

## Security & Privacy Rules

1. **Local-First Protection:** All files placed here remain local on disk.
2. **Explicit Consent Required:** No voice sample or face reference will ever be transmitted or uploaded to external cloud APIs without your explicit consent and ownership confirmation.
3. **Git Protection:** Personal audio and image files in `sample-files/` are ignored by `.gitignore`. Do not commit real personal media to public repositories.
4. **Synthetic Media Disclosure:** All videos generated using identity references will carry synthetic media provenance metadata.
