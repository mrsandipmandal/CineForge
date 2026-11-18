"""OpenAI.fm TTS provider — Primary Text-to-Speech Engine for CineForge.

Routes to the OpenAI.fm speech generation API (https://www.openai.fm/api/generate)
demonstrating OpenAI's latest text-to-speech models with emotion, custom narration
instructions, multi-voice support (Fable, Alloy, Ash, Coral, Echo, Onyx, Nova,
Sage, Shimmer, Marin, Cedar), and Hindi, Bengali, and English narration.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import requests

from lib.audio_validator import validate_audio_bytes
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

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = "https://www.openai.fm/api/generate"
DEFAULT_VOICE = "fable"

# Official OpenAI.fm voices
SUPPORTED_VOICES = [
    "fable",
    "alloy",
    "ash",
    "ballad",
    "cedar",
    "coral",
    "marin",
    "nova",
    "onyx",
    "sage",
    "verse",
    # Backward-compatible aliases
    "echo",
    "shimmer",
]

# Official OpenAI.fm Vibe delivery presets
VIBE_PRESETS = {
    "mad_scientist": (
        "Delivery: Exaggerated and theatrical, with dramatic pauses, sudden outbursts, and gleeful cackling.\n\n"
        "Voice: High-energy, eccentric, and slightly unhinged, with a manic enthusiasm that rises and falls unpredictably."
    ),
    "sincere": (
        "Voice Affect: Sincere, grounded, and empathetic.\n\n"
        "Tone: Genuine, warm, and honest.\n\n"
        "Pacing: Steady and conversational.\n\n"
        "Emotion: Authentic care and personal connection."
    ),
    "calm": (
        "Voice Affect: Calm, composed, and reassuring; project quiet authority and confidence.\n\n"
        "Tone: Sincere, empathetic, and gently authoritative—express genuine apology while conveying competence.\n\n"
        "Pacing: Steady and moderate; unhurried enough to communicate care, yet efficient enough to demonstrate professionalism.\n\n"
        "Emotion: Genuine empathy and understanding; speak with warmth.\n\n"
        "Pronunciation: Clear and precise, emphasizing key reassurances.\n\n"
        "Pauses: Brief pauses after offering assistance or requesting details, highlighting willingness to listen and support."
    ),
    "gourmet_chef": (
        "Delivery: Passionate, sensory-rich, emphasizing textures and flavors with refined enthusiasm.\n\n"
        "Voice: Sophisticated, articulate, and inviting."
    ),
    "eternal_optimist": (
        "Delivery: Radiant, uplifting, and cheerful with bright cadence and boundless positivity.\n\n"
        "Voice: Warm, smiling, and inspiring."
    ),
}


class OpenAIFMTTS(BaseTool):
    name = "openaifm_tts"
    version = "1.0.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "openaifm"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "OpenAI.fm is the primary default free TTS provider for CineForge.\n"
        "No API key is required. Optional custom endpoint via OPENAI_FM_API_ENDPOINT."
    )
    fallback = "kokoro_tts"
    fallback_tools = ["kokoro_tts", "voxcpm2_tts", "piper_tts", "openai_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = [
        "text_to_speech",
        "voice_selection",
        "narration_instructions",
        "multilingual",
        "primary_tts",
    ]
    supports = {
        "voice_cloning": False,
        "multilingual": True,
        "offline": False,
        "native_audio": True,
        "custom_instructions": True,
    }
    best_for = [
        "primary high-quality cinematic voiceover",
        "expressive narration with custom instructions",
        "multilingual delivery in English, Hindi, and Bengali",
    ]
    not_good_for = [
        "voice cloning from reference audio files",
    ]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to convert to speech",
            },
            "voice": {
                "type": "string",
                "default": DEFAULT_VOICE,
                "enum": SUPPORTED_VOICES,
                "description": f"Voice persona to use. Default: {DEFAULT_VOICE}",
            },
            "voice_id": {
                "type": "string",
                "description": "Alias for voice.",
            },
            "instructions": {
                "type": "string",
                "description": "Custom narration instructions or delivery style (e.g. 'Speak with wonder and gravity').",
            },
            "prompt": {
                "type": "string",
                "description": "Alias for instructions or style directive.",
            },
            "language_code": {
                "type": "string",
                "description": "Language code (e.g. 'en', 'hi', 'bn').",
            },
            "speed": {
                "type": "number",
                "minimum": 0.25,
                "maximum": 4.0,
                "default": 1.0,
                "description": "Playback speed multiplier.",
            },
            "model": {
                "type": "string",
                "default": "gpt-4o-mini-tts",
                "description": "Underlying TTS model identifier.",
            },
            "output_path": {
                "type": "string",
                "description": "Path to write the synthesized audio file (default: tts_output.mp3).",
            },
            "timeout_seconds": {
                "type": "integer",
                "default": 20,
                "description": "HTTP request timeout in seconds.",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=128, vram_mb=0, disk_mb=50, network_required=True,
    )
    retry_policy = RetryPolicy(max_retries=1, backoff_seconds=1.5, retryable_errors=["502", "503", "timeout"])
    side_effects = ["writes audio file to output_path"]
    user_visible_verification = ["Listen to generated audio for clarity and emotional tone"]

    def get_status(self) -> ToolStatus:
        """OpenAI.fm is always available by default as the primary provider."""
        disabled = os.environ.get("OPENAIFM_DISABLED", "").strip().lower() in {"1", "true", "yes"}
        if disabled:
            return ToolStatus.UNAVAILABLE
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        """OpenAI.fm is free to use."""
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        text = str(inputs.get("text") or "").strip()
        if not text:
            return ToolResult(success=False, error="No text provided for speech generation.")

        voice = (
            inputs.get("voice")
            or inputs.get("voice_id")
            or DEFAULT_VOICE
        ).strip().lower()
        if voice not in SUPPORTED_VOICES:
            voice = DEFAULT_VOICE

        instructions = inputs.get("instructions") or inputs.get("prompt") or ""
        vibe = inputs.get("vibe")
        if vibe and str(vibe).lower() in VIBE_PRESETS and not instructions:
            instructions = VIBE_PRESETS[str(vibe).lower()]

        generation_id = inputs.get("generation") or str(uuid.uuid4())
        lang = str(inputs.get("language_code") or "").lower()

        # Language guidance if not already specified
        if "bn" in lang and "bengali" not in instructions.lower():
            instructions = f"Speak naturally and expressively in Bengali. {instructions}".strip()
        elif "hi" in lang and "hindi" not in instructions.lower():
            instructions = f"Speak clearly and naturally in Hindi. {instructions}".strip()

        endpoint = os.environ.get("OPENAI_FM_API_ENDPOINT", DEFAULT_ENDPOINT)
        model = inputs.get("model", "gpt-4o-mini-tts")
        timeout = int(inputs.get("timeout_seconds", 20))

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://www.openai.fm/",
            "Accept": "audio/mpeg, audio/mp3, audio/wav, audio/*, application/json, */*",
        }
        cookie = os.environ.get("OPENAI_FM_COOKIE") or inputs.get("cookie")
        if cookie:
            headers["Cookie"] = cookie
        api_key = os.environ.get("OPENAI_FM_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        params = {
            "input": text,
            "prompt": instructions,
            "voice": voice,
            "generation": generation_id,
        }
        payload = {
            "model": model,
            "voice": voice,
            "input": text,
            "prompt": instructions,
            "instructions": instructions,
            "generation": generation_id,
        }

        output_path = Path(inputs.get("output_path", "tts_output.mp3"))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        response = None
        try:
            # Primary: GET with query params matching official web app
            response = requests.get(endpoint, params=params, headers=headers, timeout=timeout)
            if response.status_code == 405:
                # Fallback to POST
                response = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
        except requests.exceptions.Timeout as exc:
            return ToolResult(
                success=False,
                error=f"OpenAI.fm request timed out after {timeout}s: {exc}",
            )
        except requests.exceptions.ConnectionError as exc:
            return ToolResult(
                success=False,
                error=f"OpenAI.fm connection failed (endpoint unreachable): {exc}",
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                error=f"OpenAI.fm HTTP request error: {exc}",
            )

        if response.status_code == 429:
            return ToolResult(
                success=False,
                error="OpenAI.fm returned HTTP 429 (rate limit / Vercel challenge). Automatic fallback engaged.",
            )

        if response.status_code >= 400:
            error_detail = response.text[:200].strip()
            return ToolResult(
                success=False,
                error=f"OpenAI.fm returned HTTP {response.status_code}: {error_detail}",
            )

        # Extract audio bytes
        audio_bytes: bytes = b""
        content_type = response.headers.get("Content-Type", "").lower()

        if "application/json" in content_type:
            try:
                body = response.json()
                if "audio" in body:
                    raw_b64 = body["audio"]
                    audio_bytes = base64.b64decode(raw_b64)
                elif "audio_base64" in body:
                    audio_bytes = base64.b64decode(body["audio_base64"])
                elif "data" in body and isinstance(body["data"], str):
                    audio_bytes = base64.b64decode(body["data"])
                else:
                    return ToolResult(
                        success=False,
                        error=f"OpenAI.fm JSON response missing audio field: {list(body.keys())}",
                    )
            except Exception as exc:
                return ToolResult(
                    success=False,
                    error=f"Failed to parse OpenAI.fm JSON response: {exc}",
                )
        else:
            audio_bytes = response.content

        # Real audio validation: check magic bytes, min size, and not HTML/error
        is_valid, audio_format, reason = validate_audio_bytes(audio_bytes, min_bytes=100)
        if not is_valid:
            return ToolResult(
                success=False,
                error=f"OpenAI.fm returned invalid audio payload: {reason}",
            )

        # Ensure correct extension
        ext = f".{audio_format}" if audio_format in {"mp3", "wav", "ogg"} else ".mp3"
        if not output_path.suffix or output_path.suffix.lower() not in {".mp3", ".wav", ".ogg"}:
            output_path = output_path.with_suffix(ext)

        try:
            output_path.write_bytes(audio_bytes)
        except Exception as exc:
            return ToolResult(
                success=False,
                error=f"Failed to write OpenAI.fm audio to {output_path}: {exc}",
            )

        duration_sec = round(time.time() - start_time, 2)
        file_size_kb = round(len(audio_bytes) / 1024, 1)

        return ToolResult(
            success=True,
            data={
                "provider": self.provider,
                "tool": self.name,
                "voice": voice,
                "model": model,
                "language_code": lang or "auto",
                "instructions": instructions,
                "format": audio_format,
                "file_size_kb": file_size_kb,
                "output_path": str(output_path),
                "is_primary": True,
            },
            artifacts=[str(output_path)],
            duration_seconds=duration_sec,
            cost_usd=0.0,
            model=model,
        )
