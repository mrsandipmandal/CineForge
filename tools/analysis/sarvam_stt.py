"""Sarvam AI Speech-to-Text transcription tool.

Uses the Sarvam Saaras model for native Indian language audio transcription,
specialized in Bengali (bn-IN), Hindi (hi-IN), code-mixed Hinglish/Banglish, and Indic dialects.
Outputs standardized transcripts and segments compatible with subtitle_gen and video pipelines.
"""

from __future__ import annotations

import json
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

_LANG_MAP = {
    "bn": "bn-IN",
    "bengali": "bn-IN",
    "bn-in": "bn-IN",
    "hi": "hi-IN",
    "hindi": "hi-IN",
    "hi-in": "hi-IN",
    "ta": "ta-IN",
    "tamil": "ta-IN",
    "te": "te-IN",
    "telugu": "te-IN",
    "kn": "kn-IN",
    "kannada": "kn-IN",
    "ml": "ml-IN",
    "malayalam": "ml-IN",
    "mr": "mr-IN",
    "marathi": "mr-IN",
    "gu": "gu-IN",
    "gujarati": "gu-IN",
    "pa": "pa-IN",
    "punjabi": "pa-IN",
    "od": "od-IN",
    "odia": "od-IN",
    "en": "en-IN",
    "auto": "unknown",
}


class SarvamSTT(BaseTool):
    name = "sarvam_stt"
    version = "1.0.0"
    tier = ToolTier.ANALYZE
    capability = "transcription"
    provider = "sarvam"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.API

    dependencies = ["env:SARVAM_API_KEY"]
    install_instructions = (
        "Configure SARVAM_API_KEY from https://dashboard.sarvam.ai/.\n"
        "Provides native transcription for Bengali, Hindi, and 10+ Indian languages using Saaras."
    )
    fallback = "transcriber"
    fallback_tools = ["transcriber", "azure_stt", "dashscope_asr"]
    agent_skills = ["sarvam-ai", "speech-to-text"]

    capabilities = [
        "transcription",
        "timestamp_alignment",
        "multilingual",
        "indic_languages",
    ]
    supports = {
        "word_timestamps": True,
        "segment_timestamps": True,
        "speaker_diarization": False,
        "multilingual": True,
        "bengali": True,
        "hindi": True,
        "offline": False,
    }
    best_for = [
        "transcribing Bengali (bn-IN) audio with native vocabulary and colloquial terms",
        "mixed Indic-English speech (Banglish, Hinglish)",
        "Indian accent and regional dialect audio transcription",
    ]
    not_good_for = [
        "offline transcription (use local transcriber with faster-whisper)",
        "non-Indic international languages (use azure_stt or transcriber)",
    ]

    input_schema = {
        "type": "object",
        "required": ["audio_path"],
        "properties": {
            "audio_path": {
                "type": "string",
                "description": "Path to local audio file (.wav, .mp3, .m4a, .flac).",
            },
            "language": {
                "type": "string",
                "default": "bn-IN",
                "description": "Target language code (e.g. bn-IN, hi-IN, auto/unknown).",
            },
            "model": {
                "type": "string",
                "enum": ["saaras:v3", "saaras:v4", "saarika:v2.5"],
                "default": "saaras:v3",
                "description": "Sarvam Saaras STT model version. Default: saaras:v3.",
            },
            "with_timestamps": {
                "type": "boolean",
                "default": True,
                "description": "Whether to return segment and word timestamps.",
            },
            "output_dir": {
                "type": "string",
                "description": "Directory to save the transcript JSON artifact. Defaults to parent of audio file.",
            },
        },
    }

    output_schema = {
        "type": "object",
        "properties": {
            "transcript": {"type": "string"},
            "segments": {"type": "array"},
            "word_timestamps": {"type": "array"},
            "language": {"type": "string"},
            "duration_seconds": {"type": "number"},
        },
    }

    def get_status(self) -> ToolStatus:
        return (
            ToolStatus.AVAILABLE
            if os.getenv("SARVAM_API_KEY")
            else ToolStatus.UNAVAILABLE
        )

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = os.getenv("SARVAM_API_KEY")
        if not api_key:
            return ToolResult(
                success=False,
                error="SARVAM_API_KEY is not set. Please add it to your environment or .env file.",
            )

        audio_path_raw = inputs.get("audio_path")
        if not audio_path_raw:
            return ToolResult(success=False, error="audio_path is required")

        audio_path = Path(audio_path_raw).resolve()
        if not audio_path.is_file():
            return ToolResult(success=False, error=f"Audio file not found: {audio_path}")

        raw_lang = inputs.get("language", "bn-IN").strip().lower()
        target_lang = _LANG_MAP.get(raw_lang, "bn-IN")
        model = inputs.get("model", "saaras:v3")
        with_timestamps = inputs.get("with_timestamps", True)

        url = "https://api.sarvam.ai/speech-to-text"
        headers = {"api-subscription-key": api_key}

        try:
            with open(audio_path, "rb") as f:
                files = {"file": (audio_path.name, f, "audio/wav")}
                data = {
                    "model": model,
                    "language_code": target_lang,
                    "with_timestamps": "true" if with_timestamps else "false",
                }
                resp = requests.post(url, headers=headers, files=files, data=data, timeout=300)

            if resp.status_code != 200:
                return ToolResult(
                    success=False,
                    error=f"Sarvam STT failed HTTP {resp.status_code}: {resp.text[:400]}",
                )

            res_json = resp.json()
        except Exception as exc:
            return ToolResult(success=False, error=f"Sarvam STT request error: {exc}")

        full_transcript = res_json.get("transcript", "").strip()
        raw_timestamps = res_json.get("timestamps", [])
        detected_lang = res_json.get("language_code", target_lang)

        segments: list[dict[str, Any]] = []
        word_timestamps: list[dict[str, Any]] = []

        if isinstance(raw_timestamps, dict):
            words = raw_timestamps.get("words", [])
            starts = raw_timestamps.get("start_time_seconds", [])
            ends = raw_timestamps.get("end_time_seconds", [])
            for idx, (w, s, e) in enumerate(zip(words, starts, ends)):
                w_str = str(w).strip()
                s_val = round(float(s), 3)
                e_val = round(float(e), 3)
                word_timestamps.append({
                    "word": w_str,
                    "start": s_val,
                    "end": e_val,
                    "probability": 1.0,
                })
            # Also create segments (e.g. from sentences or word chunks)
            if word_timestamps:
                segments.append({
                    "id": 0,
                    "start": word_timestamps[0]["start"],
                    "end": word_timestamps[-1]["end"],
                    "text": full_transcript,
                    "words": word_timestamps,
                })
        elif isinstance(raw_timestamps, list) and raw_timestamps:
            for idx, item in enumerate(raw_timestamps):
                if isinstance(item, dict):
                    start = float(item.get("start", 0.0))
                    end = float(item.get("end", 0.0))
                    text = item.get("text", "").strip()
                    seg = {
                        "id": idx,
                        "start": round(start, 3),
                        "end": round(end, 3),
                        "text": text,
                    }
                    segments.append(seg)
                    word_timestamps.append({
                        "word": text,
                        "start": round(start, 3),
                        "end": round(end, 3),
                        "probability": 1.0,
                    })

        if not segments:
            segments.append({
                "id": 0,
                "start": 0.0,
                "end": 0.0,
                "text": full_transcript,
            })

        duration = max((s["end"] for s in segments), default=0.0)

        result_data = {
            "transcript": full_transcript,
            "segments": segments,
            "word_timestamps": word_timestamps,
            "language": detected_lang,
            "duration_seconds": round(duration, 3),
            "provider": "sarvam",
            "model": model,
        }

        output_dir_raw = inputs.get("output_dir")
        output_dir = Path(output_dir_raw).resolve() if output_dir_raw else audio_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / f"{audio_path.stem}_sarvam_transcript.json"
        artifact_path.write_text(json.dumps(result_data, indent=2, ensure_ascii=False), encoding="utf-8")

        return ToolResult(
            success=True,
            data=result_data,
            artifacts=[str(artifact_path)],
        )
