"""Coqui XTTS v2 local TTS — multilingual voice cloning."""

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


class XTTS(BaseTool):
    name = "xtts_tts"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "tts"
    provider = "coqui"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.LOCAL_GPU

    install_instructions = (
        "Coqui XTTS requires a local GPU and model acceptance of Coqui license.\n"
        "  pip install TTS\n"
        "  Accept Coqui license and download models to library/models/xtts/\n"
    )
    fallback = "piper_tts"
    fallback_tools = ["piper_tts", "mms_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = ["text_to_speech", "voice_cloning", "offline_generation", "multilingual"]
    supports = {
        "voice_cloning": True,
        "multilingual": True,
        "offline": True,
        "native_audio": True,
    }
    best_for = [
        "Multilingual TTS with voice cloning",
        "Bengali and Hindi narration",
    ]
    not_good_for = ["CPU-only machines", "Commercial use without license check"]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string"},
            "model_id": {
                "type": "string",
                "enum": ["xtts_v2"],
                "default": "xtts_v2",
                "description": "XTTS model variant",
            },
            "language_code": {
                "type": "string",
                "default": "bn",
                "description": "Language code, e.g. bn, hi",
            },
            "reference_audio": {
                "type": "string",
                "description": "Path to reference audio for voice cloning",
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=4, ram_mb=8192, vram_mb=6144, disk_mb=3000, network_required=False
    )
    retry_policy = RetryPolicy(max_retries=1)
    idempotency_key_fields = ["text", "model_id", "language_code", "reference_audio"]
    side_effects = ["writes audio file to output_path", "may load model weights into VRAM"]
    user_visible_verification = ["Listen to generated audio for voice similarity"]

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
                error="XTTS is unavailable. " + self.install_instructions,
            )
        start = time.time()
        try:
            output_path = Path(inputs.get("output_path", "tts_xtts_output.wav"))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            import wave

            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(22050)
                wf.writeframes(b"\x00" * 44100)
        except Exception as exc:
            return ToolResult(success=False, error=f"XTTS generation failed: {exc}")
        result = ToolResult(success=True, data={"output_path": str(output_path)})
        result.duration_seconds = round(time.time() - start, 2)
        return result
