"""OpenRouter Text-to-Speech provider tool for CineForge.

Connects to OpenRouter's OpenAI-compatible speech endpoint (/api/v1/audio/speech)
to generate speech using free and premium audio models, including:
  - heygen/heygen-voice-1-turbo:free
  - fish-audio/s2.1-pro-free:free
  - openai/tts-1 / openai/tts-1-hd
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import requests

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


class OpenRouterTTS(BaseTool):
    name = "openrouter_tts"
    version = "1.0.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "openrouter"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = ["env:OPENROUTER_API_KEY"]
    install_instructions = (
        "Configure OPENROUTER_API_KEY from https://openrouter.ai/keys.\n"
        "Unlocks free speech models such as heygen/heygen-voice-1-turbo:free and fish-audio/s2.1-pro-free:free."
    )
    fallback = "fish_audio_tts"
    fallback_tools = ["fish_audio_tts", "heygen_tts", "piper_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = [
        "text_to_speech",
        "voice_selection",
        "free_tier_generation",
        "multilingual",
    ]
    supports = {
        "free_models": True,
        "multilingual": True,
        "native_audio": True,
        "streaming": False,
    }
    best_for = [
        "Zero-cost voiceover narration with heygen-voice-1-turbo:free",
        "Expressive speech generation via fish-audio/s2.1-pro-free:free",
        "Unified OpenRouter billing with a single API key",
    ]
    not_good_for = ["Offline air-gapped generation (use piper_tts or voxcpm2_tts)"]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {
                "type": "string",
                "description": "Script or dialogue to speak.",
            },
            "model_id": {
                "type": "string",
                "default": "heygen/heygen-voice-1-turbo:free",
                "description": "Speech model ID on OpenRouter (e.g. heygen/heygen-voice-1-turbo:free, fish-audio/s2.1-pro-free:free).",
            },
            "voice": {
                "type": "string",
                "default": "alloy",
                "description": "Voice identifier or speaker name.",
            },
            "speed": {
                "type": "number",
                "default": 1.0,
                "description": "Speech speed multiplier (0.25 to 4.0).",
            },
            "output_path": {
                "type": "string",
                "description": "Target audio file path (mp3/wav).",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=100, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["text", "model_id", "voice"]
    side_effects = ["writes audio file to output_path", "calls OpenRouter API"]
    user_visible_verification = ["Listen to generated audio file for speech clarity and natural pacing"]

    def get_status(self) -> ToolStatus:
        if os.environ.get("OPENROUTER_API_KEY"):
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model_id", "heygen/heygen-voice-1-turbo:free")
        if ":free" in model:
            return 0.0
        # Standard fallback audio cost ~$0.015 per 1,000 characters
        text = inputs.get("text", "")
        return round((len(text) / 1000.0) * 0.015, 4)

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return ToolResult(
                success=False,
                error="OPENROUTER_API_KEY is not configured. " + self.install_instructions,
            )

        text = inputs.get("text", "").strip()
        if not text:
            return ToolResult(success=False, error="'text' is required for speech synthesis.")

        model_id = inputs.get("model_id", "heygen/heygen-voice-1-turbo:free")
        voice = inputs.get("voice", "alloy")
        speed = float(inputs.get("speed", 1.0))
        output_path = Path(inputs.get("output_path", "projects/output/openrouter_speech.mp3"))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        start = time.time()
        url = "https://openrouter.ai/api/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Sandip-Mandal/CineForge",
            "X-Title": "CineForge Video Production",
        }
        payload = {
            "model": model_id,
            "input": text,
            "voice": voice,
            "speed": speed,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=90)
            if not resp.ok:
                detail = resp.text[:1000]
                return ToolResult(
                    success=False,
                    error=f"OpenRouter speech API error ({resp.status_code}): {detail}",
                )

            output_path.write_bytes(resp.content)

            return ToolResult(
                success=True,
                data={
                    "provider": "openrouter",
                    "model": model_id,
                    "voice": voice,
                    "output_path": str(output_path),
                    "file_size_bytes": len(resp.content),
                },
                artifacts=[str(output_path)],
                cost_usd=self.estimate_cost(inputs),
                duration_seconds=round(time.time() - start, 2),
                model=model_id,
            )
        except requests.exceptions.RequestException as e:
            return ToolResult(
                success=False,
                error=f"Failed to connect to OpenRouter speech API: {e}",
            )
