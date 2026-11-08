---
name: sarvam-ai
description: Native Indian language speech synthesis (Bulbul TTS) and transcription (Saaras STT) for CineForge. Specialized in Bengali (bn-IN), Hindi (hi-IN), and 10+ Indic languages. Use when generating authentic Bengali/Hindi narration, transcribing Indian audio, or handling code-mixed regional speech.
---

# Sarvam AI (Indic Languages & Bengali)

Requires `SARVAM_API_KEY` in `.env`. Obtain from https://dashboard.sarvam.ai/.

## Capabilities in CineForge

- **`sarvam_tts` (`tools/audio/sarvam_tts.py`):** High-fidelity neural voice synthesis using Sarvam Bulbul engine.
- **`sarvam_stt` (`tools/analysis/sarvam_stt.py`):** Regional language transcription using Sarvam Saaras model.

## Supported Languages & Locales

| Language | BCP-47 Code | Script | Best Model |
| :--- | :--- | :--- | :--- |
| **Bengali (বাংলা)** | `bn-IN` | Bengali | `bulbul:v2` |
| **Hindi (हिन्दी)** | `hi-IN` | Devanagari | `bulbul:v2` |
| **Tamil (தமிழ்)** | `ta-IN` | Tamil | `bulbul:v2` |
| **Telugu (తెలుగు)** | `te-IN` | Telugu | `bulbul:v2` |
| **Kannada (ಕನ್ನಡ)** | `kn-IN` | Kannada | `bulbul:v2` |
| **Malayalam (മലയാളം)** | `ml-IN` | Malayalam | `bulbul:v2` |
| **Marathi (मराठी)** | `mr-IN` | Devanagari | `bulbul:v2` |
| **Gujarati (ગુજરાતી)** | `gu-IN` | Gujarati | `bulbul:v2` |
| **Punjabi (ਪੰਜਾਬੀ)** | `pa-IN` | Gurmukhi | `bulbul:v2` |
| **Odia (ଓଡ଼ିଆ)** | `od-IN` | Odia | `bulbul:v2` |
| **English (India)** | `en-IN` | Latin | `bulbul:v2` |

## TTS Usage & Speakers

```json
{
  "text": "সিনেফোর্জে আপনাকে স্বাগতম।",
  "language": "bn-IN",
  "voice_id": "meera",
  "model": "bulbul:v2",
  "speed": 1.0,
  "pitch": 0.0,
  "output_path": "pipeline/narrations/bengali_intro.wav"
}
```

Available speakers:
- Female: `meera`, `pavithra`, `maitreyi`
- Male: `arvind`, `amartya`, `arun`

## Speech-to-Text (Saaras)

```json
{
  "audio_path": "pipeline/audio/interview.wav",
  "language": "bn-IN",
  "model": "saaras:v2",
  "with_timestamps": true
}
```
Outputs standardized word and segment timestamps fully compatible with `subtitle_gen`.
