"""Mochi 1 local video generation."""

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


class Mochi1(BaseTool):
    name = "mochi1_video"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "mochi"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.LOCAL_GPU

    install_instructions = (
        "Mochi 1 requires a local GPU and model weights.\n"
        "  pip install diffusers transformers\n"
        "  Download Mochi 1 weights to library/models/mochi1/\n"
    )
    fallback = "ltx_video_local"
    fallback_tools = ["ltx_video_local", "wan21_video", "stable_video_video"]
    agent_skills = ["ltx2"]

    capabilities = ["text_to_video", "image_to_video"]
    supports = {
        "reference_image": True,
        "offline": True,
        "native_audio": False,
        "local_gpu": True,
    }
    best_for = [
        "Local Mochi 1 video generation",
        "Offline video generation without API costs",
    ]
    not_good_for = ["CPU-only machines", "Low-VRAM GPUs"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "model_variant": {
                "type": "string",
                "enum": ["mochi1-preview"],
                "default": "mochi1-preview",
                "description": "Mochi 1 model variant",
            },
            "reference_image_path": {"type": "string"},
            "width": {"type": "integer", "default": 848},
            "height": {"type": "integer", "default": 480},
            "num_frames": {"type": "integer", "default": 84},
            "num_inference_steps": {"type": "integer", "default": 50},
            "seed": {"type": "integer"},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=4, ram_mb=16384, vram_mb=8192, disk_mb=10000, network_required=False
    )
    retry_policy = RetryPolicy(max_retries=1)
    idempotency_key_fields = ["prompt", "model_variant", "seed"]
    side_effects = ["writes video file to output_path", "may download model weights"]
    user_visible_verification = ["Watch generated clip for motion quality"]

    def get_status(self) -> ToolStatus:
        if os.environ.get("LOCAL_VIDEO_MODEL", "").lower() != "true":
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
                error="Mochi 1 video generation is unavailable. " + self.install_instructions,
            )
        start = time.time()
        try:
            output_path = Path(inputs.get("output_path", "video_mochi1_output.mp4"))
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            return ToolResult(success=False, error=f"Mochi 1 generation failed: {exc}")
        result = ToolResult(success=True, data={"output_path": str(output_path)})
        result.duration_seconds = round(time.time() - start, 2)
        return result
