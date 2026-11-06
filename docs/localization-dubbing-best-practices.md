# Localization & Dubbing Best Practices — CineForge

This document establishes the production rules, provider capabilities, and quality guidelines for multilingual video dubbing and subtitle localization in CineForge (`localization-dub` pipeline).

---

## 1. Supported Languages & Provider Matrix

CineForge supports global localization across 50+ languages, with verified support for major Asian and Indic languages including **Hindi** and **Bengali**.

### Indic Languages Matrix (Hindi & Bengali)

| Language | ISO Code | Script & Direction | Verified TTS Providers | Verified STT Providers | Recommended Font (Remotion) |
|---|---|---|---|---|---|
| **Hindi** | `hi-IN` | Devanagari (LTR) | Google TTS (`hi-IN-Neural2-*`), ElevenLabs (`eleven_multilingual_v2`), Azure Speech (`hi-IN-MadhurNeural`, `hi-IN-SwaraNeural`) | Faster-Whisper (`hi`), Azure STT (`hi-IN`), ElevenLabs Scribe v2 | `Noto Sans Devanagari` |
| **Bengali** | `bn-IN`, `bn-BD` | Bengali / Bangla (LTR) | Google TTS (`bn-IN-Wavenet-*`, `bn-BD-Wavenet-*`), ElevenLabs (`eleven_multilingual_v2`), Azure Speech (`bn-IN-BashkarNeural`, `bn-IN-TanishaaNeural`, `bn-BD-PradeepNeural`) | Faster-Whisper (`bn`), Azure STT (`bn-IN`), ElevenLabs Scribe v2 | `Noto Sans Bengali` |

---

## 2. Localization Workflow Stages

The `localization-dub` pipeline executes through 7 sequential stages:

1. **Idea / Scope**:
   - Define source video and target locales (`hi-IN`, `bn-IN`, `es-ES`, etc.).
   - Choose deliverable mode:
     - `subtitles_only`: Generate aligned subtitle SRT/VTT.
     - `voiceover_dub`: Generate translated speech track, duck background audio, mix into output.
     - `lip_sync_dub`: Replace actor speech and align facial phonemes with tools like `kling_lip_sync` or HeyGen.
   - Lock composition runtime (`remotion` or `ffmpeg`).

2. **Script / Translation**:
   - Transcribe source with word-level timestamps using `transcriber`.
   - Translate while preserving timing constraints (target speech duration must match source audio window within ±10%).
   - Maintain a project glossary for brand names, technical jargon, and character names.

3. **Scene Plan**:
   - Map timing-risk scenes where translated syllable counts exceed original spoken duration.
   - For Hindi and Bengali, translation text is often 15-25% longer than English equivalents. Apply concise phrasing or slight speech rate adjustment (1.05x–1.12x) to maintain lip-sync and cut rhythm.

4. **Assets Generation**:
   - Generate speech audio using `tts_selector` or provider tools (`google_tts`, `azure_tts`, `elevenlabs_tts`).
   - Validate audio duration against the planned scene window.
   - When lip sync is requested, submit generated audio and scene frames to `kling_lip_sync` or `heygen_video_translate`.

5. **Edit / Audio Mix**:
   - Duck original speech by -24dB to -30dB or completely mute source vocal track.
   - Mix background music and SFX at standard dialogue mix ratios (voice at -14 LUFS, BGM at -24 LUFS).

6. **Compose**:
   - Render per-locale video using Remotion's `CaptionOverlay`.
   - Ensure UTF-8 font loading for complex scripts (Devanagari conjuncts, Bengali matras).

7. **Publish**:
   - Package per-locale video deliverables with localized titles, descriptions, and tag sets.

---

## 3. Subtitle & Caption Rendering Rules

- **Script Direction**:
  - Bengali and Hindi use **Left-to-Right (LTR)** reading order.
  - Unlike Arabic and Hebrew (which use RTL bidirectional embedding), Bengali and Hindi do not require `direction="rtl"`, but they require proper ligature and conjunct shaping.
- **Font Fallback**:
  - Remotion loads Google Fonts via `@remotion/google-fonts`. Ensure `Noto Sans Devanagari` and `Noto Sans Bengali` are referenced when rendering South Asian subtitles.
- **Reading Speed**:
  - Subtitle line lengths should not exceed 38 characters per line.
  - Display duration should provide at least 1 second per 15 characters to allow comfortable reading.

---

## 4. Quality Gates & Verification

- **Translation Accuracy Gate**: Ensure brand terms, units of measure, and idioms are correctly translated.
- **Timing Gate**: Dubbed audio must start within 0.2s of the original speaker starting and stop before the next cut.
- **Lip-Sync Gate**: In lip-sync mode, verify mouth open/close matches vowel sounds without uncanny stretching.
