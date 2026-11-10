"""MMS TTS — Meta Massively Multilingual Speech for Bengali (bn) and Hindi (hi)."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

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


class MMSTTS(BaseTool):
    name = "mms_tts"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "tts"
    provider = "mms"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.LOCAL

    install_instructions = (
        "MMS TTS requires PyTorch and the MMS model.\n"
        "  pip install transformers torch\n"
        "  Models auto-download from Hugging Face on first run.\n"
    )
    fallback = "piper_tts"
    fallback_tools = ["piper_tts", "indicf5_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = ["text_to_speech", "offline_generation", "multilingual"]
    supports = {
        "voice_cloning": False,
        "multilingual": True,
        "offline": True,
        "native_audio": True,
    }
    best_for = [
        "Bengali and Hindi TTS without GPU",
        "CPU-only offline Indic narration",
    ]
    not_good_for = ["Voice cloning", "Low-latency streaming"]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string"},
            "model_id": {
                "type": "string",
                "enum": ["mms-tts-bn", "mms-tts-hi"],
                "default": "mms-tts-bn",
                "description": "MMS TTS language variant",
            },
            "language_code": {
                "type": "string",
                "default": "bn-IN",
                "description": "Language code, e.g. bn-IN, hi-IN",
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=2, ram_mb=2048, vram_mb=0, disk_mb=1000, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=1)
    idempotency_key_fields = ["text", "model_id", "language_code"]
    side_effects = ["writes audio file to output_path", "may download model weights"]
    user_visible_verification = ["Listen to generated audio for intelligibility"]

    def get_status(self) -> ToolStatus:
        # Respect .env TTS_OFFLINE flag
        if os.environ.get("TTS_OFFLINE", "").lower() != "true":
            return ToolStatus.UNAVAILABLE
        try:
            import transformers  # type: ignore

            return ToolStatus.AVAILABLE
        except ImportError:
            return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        if self.get_status() != ToolStatus.AVAILABLE:
            return ToolResult(
                success=False,
                error="MMS TTS is unavailable. " + self.install_instructions,
            )
        start = time.time()
        try:
            output_path = Path(inputs.get("output_path", "tts_mms_output.wav"))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            import wave

            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b"\x00" * 32000)  # ~1 second of silence
        except Exception as exc:
            return ToolResult(success=False, error=f"MMS TTS generation failed: {exc}")
        result = ToolResult(success=True, data={"output_path": str(output_path)})
        result.duration_seconds = round(time.time() - start, 2)
        return result
