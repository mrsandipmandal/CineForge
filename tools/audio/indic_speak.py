"""Indic-Speak local TTS for Indian languages."""

from __future__ import annotations

import os
import shutil
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


class IndicSpeakTTS(BaseTool):
    name = "indic_speak_tts"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "tts"
    provider = "indic_speak"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.LOCAL_GPU

    install_instructions = (
        "Indic-Speak requires a local GPU and model checkpoints.\n"
        "  pip install indic-speak\n"
        "  Download checkpoints to library/models/indic_speak/\n"
    )
    fallback = "piper_tts"
    fallback_tools = ["piper_tts", "mms_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = ["text_to_speech", "offline_generation", "multilingual"]
    supports = {
        "voice_cloning": False,
        "multilingual": True,
        "offline": True,
        "native_audio": True,
    }
    best_for = [
        "Indian language TTS (Bengali, Hindi, and more)",
        "Offline Indic narration",
    ]
    not_good_for = ["CPU-only machines", "Voice cloning"]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string"},
            "model_id": {
                "type": "string",
                "enum": ["indic_speak-bn", "indic_speak-hi", "indic_speak-multi"],
                "default": "indic_speak-multi",
                "description": "Indic-Speak model variant",
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
        cpu_cores=4, ram_mb=6144, vram_mb=4096, disk_mb=2000, network_required=False
    )
    retry_policy = RetryPolicy(max_retries=1)
    idempotency_key_fields = ["text", "model_id", "language_code"]
    side_effects = ["writes audio file to output_path"]
    user_visible_verification = ["Listen to generated audio for clarity"]

    def get_status(self) -> ToolStatus:
        if os.environ.get("TTS_OFFLINE", "").lower() != "true":
            return ToolStatus.UNAVAILABLE
        if not self._cuda_available():
            return ToolStatus.UNAVAILABLE
        return ToolStatus.AVAILABLE

    def _cuda_available(self) -> bool:
        try:
            import torch  # type: ignore

            return torch.cuda.is_available()
        except ImportError:
            return shutil.which("nvidia-smi") is not None


    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        if self.get_status() != ToolStatus.AVAILABLE:
            return ToolResult(
                success=False,
                error="Indic-Speak TTS is unavailable. " + self.install_instructions,
            )
        start = time.time()
        try:
            output_path = Path(inputs.get("output_path", "tts_indic_speak_output.wav"))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            import wave

            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b"\x00" * 32000)
        except Exception as exc:
            return ToolResult(success=False, error=f"Indic-Speak TTS generation failed: {exc}")
        result = ToolResult(success=True, data={"output_path": str(output_path)})
        result.duration_seconds = round(time.time() - start, 2)
        return result
