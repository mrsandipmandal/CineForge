---
name: nvidia-nim
description: NVIDIA NIM (NVIDIA Inference Microservices) integration for CineForge. Accelerated LLM reasoning, scriptwriting, and cinematic worldbuilding with Nemotron-70B, Llama-3.1-405B, DeepSeek-R1, and Qwen 2.5 via hosted cloud endpoints or local containerized microservices on NVIDIA RTX GPUs.
---

# NVIDIA NIM (NVIDIA Inference Microservices)

NVIDIA NIM provides state-of-the-art GPU-accelerated inference for leading foundation and reasoning models. It operates in two complementary deployment modes:

1. **Cloud API (`https://integrate.api.nvidia.com/v1`)**:
   Free 1,000 inference credits upon signup at [build.nvidia.com](https://build.nvidia.com). No local GPU or installation needed.
2. **Local Workstation NIM (`http://localhost:8000/v1`)**:
   Self-hosted Docker containers with TensorRT-LLM optimization for users with local NVIDIA RTX 3080/3090/4080/4090 or workstation GPUs. Zero token cost, 100% private, and offline.

---

## Capabilities in CineForge

- **Tool:** `nvidia_nim_llm` ([`tools/text/nvidia_nim_llm.py`](file:///f:/CineForge/tools/text/nvidia_nim_llm.py))
- **Primary Model:** `nvidia/llama-3.1-nemotron-70b-instruct` (NVIDIA's flagship reasoning model)
- **Extreme Scale Model:** `meta/llama-3.1-405b-instruct` (Largest open model for epic worldbuilding)
- **Multilingual Support:** `qwen/qwen2.5-72b-instruct` (Bengali, Hindi, and regional translations)
- **Deep Reasoning:** `deepseek-ai/deepseek-r1` (Complex technical explainers and math)

---

## Configuration & Environment Variables

Add to your `.env` file:

```env
# Cloud API (1,000 free credits at build.nvidia.com)
NVIDIA_NIM_API_KEY=your_nvidia_api_key_here

# Optional: Override base URL for local self-hosted NIM Docker containers
# NVIDIA_NIM_BASE_URL=http://localhost:8000/v1

# Optional: Override default model
# NVIDIA_NIM_DEFAULT_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
```

---

## Model Catalog

| Model ID | Provider Variant | Primary CineForge Use Case | Context |
| :--- | :--- | :--- | :--- |
| `nvidia/llama-3.1-nemotron-70b-instruct` | **Default** | Scriptwriting, structured scene planning, cinematic narrative | 128k |
| `meta/llama-3.3-70b-instruct` | High-Speed Reasoning | Fast draft iterations, dialogue polish, and scene prompts | 128k |
| `meta/llama-3.1-405b-instruct` | Ultra-High Reasoning | Master storyline architecture, multi-character epics, world lore | 128k |
| `deepseek-ai/deepseek-r1` | Chain-of-Thought | Deep logical analysis, technical explainer script structuring | 128k |
| `qwen/qwen2.5-72b-instruct` | Multilingual & Indic | Bengali, Hindi, and regional scriptwriting & translation | 128k |
| `mistralai/mistral-large-2-instruct` | Creative & Nuanced | European storytelling, concise narration scripts | 128k |

---

## Usage Examples

### 1. Scriptwriting with Nemotron-70B

```json
{
  "prompt": "Write a 45-second compelling video script about the ancient origins of tea in Darjeeling.",
  "model": "nvidia/llama-3.1-nemotron-70b-instruct",
  "temperature": 0.7
}
```

### 2. Epic Worldbuilding with Llama-3.1-405B

```json
{
  "prompt": "Outline a deep sci-fi universe setting on a frozen moon for a 3-part animated series.",
  "model": "meta/llama-3.1-405b-instruct",
  "temperature": 0.8
}
```

### 3. Multilingual Bengali Script Translation with Qwen 2.5 72B

```json
{
  "prompt": "Translate and culturally adapt this English documentary narration into natural Kolkata Bengali.",
  "model": "qwen/qwen2.5-72b-instruct",
  "temperature": 0.5
}
```

### 4. Structured JSON Scene Planning

```json
{
  "system_prompt": "You are a professional film director. Respond strictly with JSON adhering to the scene plan schema.",
  "prompt": "Create 4 scenes for a Mars colony explainer.",
  "model": "nvidia/llama-3.1-nemotron-70b-instruct",
  "response_format": {"type": "json_object"}
}
```

---

## Local Self-Hosted NIM Setup (For Local RTX GPUs)

If you have a local NVIDIA GPU with Docker installed, you can launch a local NIM container:

```bash
docker run -d --gpus all \
  -e NGC_API_KEY=$NGC_API_KEY \
  -v $LOCAL_CACHE:/opt/nim/.cache \
  -p 8000:8000 \
  nvcr.io/nim/meta/llama-3.1-8b-instruct:latest
```

Then in CineForge's `.env`:
```env
NVIDIA_NIM_BASE_URL=http://localhost:8000/v1
```
CineForge will immediately route all `nvidia_nim_llm` calls to your local GPU with zero external network traffic.
