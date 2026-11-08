---
name: openrouter
description: Multi-model AI gateway integration for CineForge with OpenRouter. Access 100% free models (Gemini 2.0 Flash, Llama 3.3 70B, DeepSeek R1, Qwen 2.5) and xAI Grok models (grok-2, grok-beta) via a single unified API key. Use for zero-cost scriptwriting, storyboard planning, multi-lingual translations, and creative ideation.
---

# OpenRouter

Requires `OPENROUTER_API_KEY` in `.env`. Obtain from https://openrouter.ai/keys.

## Capabilities in CineForge

- **`openrouter_llm` (`tools/text/openrouter_llm.py`):** Unified chat completions adapter.
- Accesses hundreds of models with a single credit/key setup.
- Provides 100% free models (`:free` suffix) with zero billing required.
- Provides seamless access to xAI Grok without a dedicated xAI billing account.

## Top Free Tier Models (`:free`)

| Model Identifier | Provider | Best For |
| :--- | :--- | :--- |
| `google/gemini-2.0-flash-exp:free` | Google | High speed, large context, creative scene ideation |
| `meta-llama/llama-3.3-70b-instruct:free` | Meta | Narrative depth, conversational scriptwriting |
| `deepseek/deepseek-r1:free` | DeepSeek | Step-by-step reasoning, complex pipeline logic |
| `qwen/qwen-2.5-72b-instruct:free` | Alibaba | High proficiency in multilingual & Bengali translation |
| `mistralai/mistral-small-24b-instruct-2501:free` | Mistral | Concise, punchy marketing scripts and voiceover cues |

## Grok Models on OpenRouter

| Model Identifier | Provider | Description |
| :--- | :--- | :--- |
| `x-ai/grok-2-1212` | xAI | State-of-the-art Grok reasoning and script generation |
| `x-ai/grok-2-vision-1212` | xAI | Visual inspection and storyboard critique |
| `x-ai/grok-beta` | xAI | Fast experimental Grok responses |

## Usage Examples

### 1. Free Scriptwriting
```json
{
  "prompt": "Write a 30-second dramatic script about exploring the Sundarbans in Bengali and English.",
  "model": "google/gemini-2.0-flash-exp:free",
  "temperature": 0.7
}
```

### 2. Grok Generation
```json
{
  "prompt": "Draft an engaging YouTube short script introducing an AI-first movie studio.",
  "model": "x-ai/grok-2-1212",
  "temperature": 0.8
}
```

### 3. Structured JSON Scene Planning
```json
{
  "system_prompt": "You are a cinematic director. Respond only in JSON with fields: scenes, audio_cue, visual_cue.",
  "prompt": "Create a 3-scene plan for an educational clip on black holes.",
  "model": "meta-llama/llama-3.3-70b-instruct:free",
  "response_format": {"type": "json_object"}
}
```
