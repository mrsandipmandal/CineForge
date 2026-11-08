---
name: groq
description: Ultra-fast LLM inference and Whisper speech-to-text on Groq LPUs. Free tier access to Llama 3.3 70B, Llama 3.1 8B, DeepSeek R1, and Whisper Large v3 with hundreds of tokens per second. Use when generating scripts with near-zero latency or rapidly transcribing audio.
---

# Groq (LPU Inference Engine)

Requires `GROQ_API_KEY` in `.env`. Obtain a free API key at https://console.groq.com/keys.

## Capabilities in CineForge

- **`groq_llm` (`tools/text/groq_llm.py`):** Ultra-fast chat completions (500+ tokens/sec) for scriptwriting, storyboarding, and translation.
- **`groq_whisper` (`tools/analysis/groq_whisper.py`):** Near-instant cloud speech-to-text with word-level timestamps using Whisper Large v3.

## Supported Models

### 1. Language Models (LLM)
| Model ID | Context | Description |
| :--- | :--- | :--- |
| `llama-3.3-70b-versatile` (Default) | 128k | High-intelligence reasoning, creative scriptwriting, deep nuance |
| `llama-3.1-8b-instant` | 128k | Extreme speed (750+ tokens/sec), instant formatting and drafting |
| `deepseek-r1-distill-llama-70b` | 128k | Step-by-step reasoning, mathematical & logical scripting |
| `gemma2-9b-it` | 8k | Google open weights on Groq LPU |
| `mixtral-8x7b-32768` | 32k | Fast MoE architecture |

### 2. Audio Transcription (STT)
| Model ID | Speed | Description |
| :--- | :--- | :--- |
| `whisper-large-v3` (Default) | ~10x realtime | Full accuracy multilingual transcription with word timestamps |
| `whisper-large-v3-turbo` | ~15x realtime | Ultra-fast lightweight transcription |

## Usage Examples

### Script Generation with Llama 3.3 70B
```json
{
  "prompt": "Write a 30-second dramatic voiceover script about the history of tea in Bengal.",
  "model": "llama-3.3-70b-versatile",
  "temperature": 0.7
}
```

### Rapid Audio Transcription
```json
{
  "audio_path": "pipeline/audio/voiceover.wav",
  "model": "whisper-large-v3",
  "language": "en"
}
```
Outputs standardized word and segment timestamps fully compatible with `subtitle_gen`.
