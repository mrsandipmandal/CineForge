"""Kokoro TTS provider — Local 82M Multilingual Text-to-Speech.

Kokoro-82M is the first local fallback TTS engine in CineForge.
Runs locally using ONNX or PyTorch weights, requiring no external API keys.
Supports 54 voices, multi-language phonemization, and fast inference.
"""

from __future__ import annotations

import logging
import os
import shutil
import time
from pathlib import Path
from typing import Any, Optional

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

DEFAULT_KOKORO_VOICE = "af_heart"


class KokoroTTS(BaseTool):
    name = "kokoro_tts"
    version = "1.0.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "kokoro"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["python:kokoro_onnx"]
    install_instructions = (
        "Install Kokoro TTS dependencies:\n"
        "  pip install kokoro-onnx soundfile\n"
        "Or install the kokoro PyPI package:\n"
        "  pip install kokoro\n"
        "For non-English support on Linux/macOS, ensure espeak-ng is installed."
    )
    fallback = "voxcpm2_tts"
    fallback_tools = ["voxcpm2_tts", "piper_tts", "openai_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = [
        "text_to_speech",
        "voice_selection",
        "offline_generation",
        "local_tts",
    ]
    supports = {
        "voice_cloning": False,
        "multilingual": True,
        "offline": True,
        "native_audio": True,
    }
    best_for = [
        "fast local offline narration",
        "zero-cost text-to-speech with natural cadence",
        "first fallback when cloud TTS is unavailable",
    ]
    not_good_for = [
        "high-accuracy voice cloning from audio samples",
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
                "default": DEFAULT_KOKORO_VOICE,
                "description": f"Kokoro voice ID (e.g. af_heart, am_michael). Default: {DEFAULT_KOKORO_VOICE}",
            },
            "voice_id": {
                "type": "string",
                "description": "Alias for voice.",
            },
            "speed": {
                "type": "number",
                "minimum": 0.5,
                "maximum": 2.0,
                "default": 1.0,
                "description": "Speaking speed rate.",
            },
            "language_code": {
                "type": "string",
                "description": "Language code (e.g. 'en-us', 'en-gb', 'hi', 'bn').",
            },
            "output_path": {
                "type": "string",
                "description": "Path to write the output audio (default: tts_output.wav).",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=2, ram_mb=512, vram_mb=0, disk_mb=350, network_required=False,
    )
    retry_policy = RetryPolicy(max_retries=1, backoff_seconds=1.0)
    side_effects = ["writes audio file to output_path"]
    user_visible_verification = ["Listen to generated audio for speech cadence"]

    def _is_installed(self) -> bool:
        """Check if kokoro, kokoro_onnx, or a local kokoro runner is present."""
        try:
            import kokoro_onnx  # noqa: F401
            return True
        except ImportError:
            pass

        try:
            import kokoro  # noqa: F401
            return True
        except ImportError:
            pass

        # Also check if CLI is available
        if shutil.which("kokoro"):
            return True

        # Custom local server / API URL
        if os.environ.get("KOKORO_API_URL"):
            return True

        return False

    def get_status(self) -> ToolStatus:
        if os.environ.get("KOKORO_DISABLED", "").strip().lower() in {"1", "true", "yes"}:
            return ToolStatus.UNAVAILABLE
        if self._is_installed():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        text = str(inputs.get("text") or "").strip()
        if not text:
            return ToolResult(success=False, error="No text provided for Kokoro TTS.")

        if not self._is_installed():
            return ToolResult(
                success=False,
                error=f"Kokoro TTS is not installed or configured. {self.install_instructions}",
            )

        voice = str(inputs.get("voice") or inputs.get("voice_id") or DEFAULT_KOKORO_VOICE).strip()
        speed = float(inputs.get("speed", 1.0))
        lang = str(inputs.get("language_code") or "en-us").strip().lower()

        output_path = Path(inputs.get("output_path", "tts_output.wav"))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        start_time = time.time()

        # Check if remote Kokoro endpoint is configured
        endpoint = os.environ.get("KOKORO_API_URL")
        if endpoint:
            import requests
            try:
                resp = requests.post(
                    endpoint,
                    json={"text": text, "voice": voice, "speed": speed, "lang": lang},
                    timeout=30,
                )
                if resp.status_code != 200:
                    return ToolResult(
                        success=False,
                        error=f"Kokoro API returned HTTP {resp.status_code}: {resp.text[:150]}",
                    )
                audio_bytes = resp.content
            except Exception as exc:
                return ToolResult(
                    success=False,
                    error=f"Kokoro endpoint request failed: {exc}",
                )
        else:
            # Local synthesis via kokoro-onnx or kokoro library
            try:
                audio_bytes = self._synthesize_local(text, voice, speed, lang)
            except Exception as exc:
                return ToolResult(
                    success=False,
                    error=f"Kokoro local synthesis failed: {exc}",
                )

        # Validate real audio
        is_valid, audio_format, reason = validate_audio_bytes(audio_bytes, min_bytes=100)
        if not is_valid:
            return ToolResult(
                success=False,
                error=f"Kokoro produced invalid audio: {reason}",
            )

        ext = f".{audio_format}" if audio_format in {"wav", "mp3"} else ".wav"
        if not output_path.suffix or output_path.suffix.lower() not in {".wav", ".mp3"}:
            output_path = output_path.with_suffix(ext)

        try:
            output_path.write_bytes(audio_bytes)
        except Exception as exc:
            return ToolResult(
                success=False,
                error=f"Failed to write Kokoro audio to {output_path}: {exc}",
            )

        duration_sec = round(time.time() - start_time, 2)

        return ToolResult(
            success=True,
            data={
                "provider": self.provider,
                "tool": self.name,
                "voice": voice,
                "speed": speed,
                "format": audio_format,
                "output_path": str(output_path),
                "is_local": True,
            },
            artifacts=[str(output_path)],
            duration_seconds=duration_sec,
            cost_usd=0.0,
            model="kokoro-82m",
        )

    def _synthesize_local(self, text: str, voice: str, speed: float, lang: str) -> bytes:
        """Run local Kokoro synthesis using available libraries."""
        # Try kokoro_onnx first
        try:
            import io
            import soundfile as sf
            from kokoro_onnx import Kokoro
            kokoro = Kokoro("kokoro-v0_19.onnx", "voices.json")
            samples, sample_rate = kokoro.create(text, voice=voice, speed=speed, lang=lang)
            buf = io.BytesIO()
            sf.write(buf, samples, sample_rate, format="WAV")
            return buf.getvalue()
        except Exception:
            pass

        # Try kokoro PyTorch package
        try:
            import io
            import soundfile as sf
            from kokoro import KPipeline
            pipeline = KPipeline(lang_code=lang[0] if lang else "a")
            generator = pipeline(text, voice=voice, speed=speed)
            all_audio = []
            sample_rate = 24000
            for _, _, audio in generator:
                all_audio.append(audio)
            import numpy as np
            combined = np.concatenate(all_audio) if all_audio else np.array([])
            buf = io.BytesIO()
            sf.write(buf, combined, sample_rate, format="WAV")
            return buf.getvalue()
        except Exception as exc:
            raise RuntimeError(f"Kokoro local runtime error: {exc}")
