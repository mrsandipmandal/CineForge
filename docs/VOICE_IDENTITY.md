# OpenMontage Matrix — Voice Identity Studio

The **Voice Identity Studio** provides unified voice profile management, cross-scene vocal continuity, and native multilingual speech synthesis and voice cloning for OpenMontage Matrix.

---

## 1. Supported Languages & Target Dialects

OpenMontage Matrix delivers first-class support for three primary languages:

| Language | Locale Code | Script | TTS Support | Voice Cloning Support | Recommended Providers |
|----------|-------------|--------|-------------|-----------------------|-----------------------|
| **Bengali** | `bn-IN` / `bn-BD` | বাংলা | ✅ Full Native | ✅ High Quality | ElevenLabs, Fish Audio, Azure Speech, IndicF5 |
| **Hindi** | `hi-IN` | देवनागरी | ✅ Full Native | ✅ High Quality | ElevenLabs, Fish Audio, Azure Speech, Coqui XTTS-v2, IndicF5 |
| **English** | `en-US` / `en-GB` | Latin | ✅ Full Native | ✅ Studio Grade | ElevenLabs, Fish Audio, OpenAI TTS, Cartesia, Piper |

> **Critical Distinction**: Standard Text-to-Speech (TTS) utilizes predefined synthetic voices (e.g., `bn-IN-BashkarNeural` or `hi-IN-MadhurNeural`). **Voice Cloning** extracts acoustic characteristics from a user-supplied audio sample in `sample-files/voices/` to synthesize speech in the target speaker's unique voice timbre. Ordinary TTS outputs are never mislabeled as cloned voices.

---

## 2. Provider Capability Matrix

| Provider | Bengali TTS | Hindi TTS | Voice Cloning | Enrollment Required | API / Local | Typical Cost | License / Terms |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **ElevenLabs** | ✅ (`eleven_multilingual_v2`) | ✅ (`eleven_multilingual_v2`) | ✅ (Instant Voice Clone) | No (API upload) | Cloud API | ~$0.30 / 1k chars | Commercial SaaS |
| **Fish Audio** | ✅ (`s1` / `s2` multilingual) | ✅ (`s1` / `s2` multilingual) | ✅ (Zero-shot reference) | No | Cloud API / Local | Pay-per-credit / Local free | API SaaS / Open Weights |
| **Azure Speech** | ✅ (`bn-IN-BashkarNeural`, `bn-IN-TanishaaNeural`) | ✅ (`hi-IN-MadhurNeural`, `hi-IN-SwaraNeural`) | ⚠️ (Custom Neural Voice only) | Yes (Enterprise approval) | Cloud API | ~$16.00 / 1M chars | Commercial Cloud |
| **Cartesia** | ❌ (Experimental) | ❌ (Experimental) | ✅ (English, Spanish, French) | No | Cloud API | ~$0.05 / 1k chars | Commercial SaaS |
| **Piper TTS** | ⚠️ (Community models) | ✅ (`hi_IN-cora`) | ❌ (Fixed checkpoints only) | N/A | Local (CPU fast) | Free ($0) | MIT / Open Source |
| **Coqui XTTS-v2** | ⚠️ (Community fine-tunes) | ✅ (Native 17 langs) | ✅ (3-6s reference audio) | No | Local GPU | Free ($0) | CPML (Non-commercial) |
| **IndicF5 / F5-TTS** | ✅ (IndicF5 multilingual) | ✅ (IndicF5 multilingual) | ✅ (Zero-shot flow matching) | No | Local GPU | Free ($0) | Apache 2.0 |

---

## 3. Voice Profile Schema & Structure

Voice profiles reside in `sample-files/voices/<profile_id>/`:

```json
{
  "profile_id": "anirban_roy",
  "name": "Anirban Roy",
  "language": "bn-IN",
  "gender": "male",
  "accent": "Kolkata, West Bengal",
  "description": "Warm, articulate baritone voice suitable for cultural and historical documentaries in Bengali.",
  "recommended_providers": ["elevenlabs", "fish_audio", "azure_tts"],
  "consent": {
    "verified": true,
    "consent_type": "voice_actor_release",
    "notes": "Full rights granted for OpenMontage Matrix documentary narrations."
  },
  "samples": [
    {
      "file": "anirban_sample_01.wav",
      "path": "sample-files/voices/anirban_roy/samples/anirban_sample_01.wav",
      "duration_sec": 14.5,
      "sample_rate": 44100,
      "channels": 1,
      "sha256": "4b68ef9798...",
      "transcription": "নমস্কার, ওপেনমন্টেজ ম্যাট্রিক্সে আপনাকে স্বাগতম।"
    }
  ]
}
```

---

## 4. Voice Routing Workflow

The `VoiceIdentity` tool (`tools/audio/voice_identity.py`) and `TTSSelector` (`tools/audio/tts_selector.py`) collaborate seamlessly:

1. **Selection**: A pipeline stage specifies `voice_profile_id: "anirban_roy"` or `language: "bn-IN"`.
2. **Consent Gate**: The system verifies `consent.verified == True`. If false, execution halts with a consent violation.
3. **Provider Routing**:
   - If `require_cloning: true` is requested, the system prioritizes `fish_audio` or `elevenlabs` with reference sample attachment.
   - If cloning is unavailable or not requested, `TTSSelector` selects `azure_tts` (with `bn-IN-BashkarNeural`) or `elevenlabs` (with `eleven_multilingual_v2`), preserving script punctuation and native phonetics.
4. **Reproducibility**: The generated `asset_manifest.json` logs the exact provider, voice ID, reference audio SHA-256, and consent verification timestamp.
