"""Studio broadcast audio mastering chain for Sandip voice profile."""

from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolTier,
)

logger = logging.getLogger(__name__)

# Mastering filter chain tailored for Sandip's voice profile:
# - 75Hz High-Pass: eliminates low mic rumble & plosives
# - Warmth & Presence EQ: 120Hz warmth (+2.5dB) and 3kHz presence (+1.5dB)
# - Opto Compression: 3:1 ratio, -18dB threshold, 15ms attack, 120ms release
# - EBU R128 Loudness Normalization: Target -14 LUFS, LRA 7, True Peak -1.0 dBFS
SANDIP_MASTERING_FILTER = (
    "highpass=f=75,"
    "equalizer=f=120:width_type=o:width=1.5:g=2.5,"
    "equalizer=f=3000:width_type=o:width=1.5:g=1.5,"
    "acompressor=threshold=-18dB:ratio=3:attack=15:release=120,"
    "loudnorm=I=-14:LRA=7:TP=-1.0"
)


class SandipAudioMaster(BaseTool):
    """Studio broadcast audio mastering chain tailored for Sandip's voice profile."""

    name = "sandip_audio_master"
    version = "1.0.0"
    tier = ToolTier.ENHANCE
    capability = "audio_enhance"
    provider = "ffmpeg"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    runtime = ToolRuntime.LOCAL
    determinism = Determinism.DETERMINISTIC

    dependencies = ["cmd:ffmpeg"]
    install_instructions = "Install FFmpeg: https://ffmpeg.org/download.html"
    agent_skills = ["ffmpeg"]

    capabilities = [
        "audio_mastering",
        "voice_eq",
        "compression",
        "loudnorm",
    ]

    input_schema = {
        "type": "object",
        "required": ["raw_audio_path"],
        "properties": {
            "raw_audio_path": {
                "type": "string",
                "description": "Path to input raw voice narration audio file.",
            },
            "output_path": {
                "type": "string",
                "description": "Path to destination mastered audio file.",
            },
        },
    }

    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=100)
    idempotency_key_fields = ["raw_audio_path", "output_path"]
    side_effects = ["writes mastered broadcast audio to output_path"]
    user_visible_verification = [
        "Verify clear broadcast audio presence and warm low-end",
        "Verify loudness conforms to EBU R128 (-14 LUFS, -1.0 dBFS true peak)",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._last_fallback_used = False

    def master_narration(self, raw_audio_path: str, output_path: str) -> str:
        """Apply FFmpeg audio filtering chain tailored for Sandip's voice profile.

        If FFmpeg is not found in PATH or execution fails, gracefully falls back
        to copying raw_audio_path to output_path and logging a warning.
        """
        raw_p = Path(raw_audio_path)
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        self._last_fallback_used = False

        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            logger.warning(
                "FFmpeg not found in PATH; falling back to direct copy: %s -> %s",
                raw_p,
                out_p,
            )
            self._last_fallback_used = True
            shutil.copyfile(raw_p, out_p)
            return str(out_p)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(raw_p),
            "-af",
            SANDIP_MASTERING_FILTER,
            str(out_p),
        ]

        try:
            self.run_command(cmd)
        except Exception as exc:
            logger.warning(
                "FFmpeg mastering failed (%s); falling back to direct copy: %s -> %s",
                exc,
                raw_p,
                out_p,
            )
            self._last_fallback_used = True
            shutil.copyfile(raw_p, out_p)
            return str(out_p)

        return str(out_p)

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        """Execute audio mastering on input audio."""
        raw_audio_path = inputs.get("raw_audio_path")
        if not raw_audio_path:
            return ToolResult(success=False, error="raw_audio_path is required")

        raw_p = Path(raw_audio_path)
        if not raw_p.exists():
            return ToolResult(success=False, error=f"Raw audio not found: {raw_audio_path}")

        output_path = inputs.get("output_path")
        if not output_path:
            output_path = str(raw_p.with_name(f"{raw_p.stem}_mastered{raw_p.suffix}"))

        start_time = time.time()
        final_out = self.master_narration(str(raw_p), str(output_path))
        elapsed = time.time() - start_time

        return ToolResult(
            success=True,
            data={
                "output_path": final_out,
                "lufs_target": -14.0,
                "fallback_used": self._last_fallback_used,
            },
            artifacts=[final_out],
            duration_seconds=round(elapsed, 2),
        )
