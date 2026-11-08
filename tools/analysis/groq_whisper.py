"""Groq Whisper ultra-fast audio transcription tool.

Uses Groq LPU inference for OpenAI Whisper models (whisper-large-v3, whisper-large-v3-turbo)
to transcribe audio files at lightning speed with word-level timestamps.
Outputs standardized transcript JSON compatible with subtitle_gen and CineForge pipelines.
"""

from __future__ import annotations

import json
import os
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


class GroqWhisper(BaseTool):
    name = "groq_whisper"
    version = "1.0.0"
    tier = ToolTier.ANALYZE
    capability = "transcription"
    provider = "groq"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.API

    dependencies = ["env:GROQ_API_KEY"]
    install_instructions = (
        "Configure GROQ_API_KEY from https://console.groq.com/keys.\n"
        "Provides ultra-fast, free-tier Whisper transcription (whisper-large-v3 / turbo) on Groq LPUs."
    )
    fallback = "transcriber"
    fallback_tools = ["transcriber", "azure_stt", "sarvam_stt"]
    agent_skills = ["groq", "speech-to-text"]

    capabilities = [
        "transcription",
        "timestamp_alignment",
        "word_level_timestamps",
        "multilingual",
        "ultra_fast_transcription",
    ]
    supports = {
        "word_timestamps": True,
        "segment_timestamps": True,
        "speaker_diarization": False,
        "multilingual": True,
        "offline": False,
    }
    best_for = [
        "ultra-fast speech-to-text with near-zero latency on Groq LPUs",
        "free-tier cloud transcription using Whisper Large v3",
        "generating word-level timestamps for video subtitles",
    ]
    not_good_for = [
        "offline local execution without network (use local transcriber)",
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
                "description": "Optional ISO-639-1 language code (e.g. 'en', 'bn', 'hi'). Auto-detected if omitted.",
            },
            "model": {
                "type": "string",
                "enum": ["whisper-large-v3", "whisper-large-v3-turbo"],
                "default": "whisper-large-v3",
                "description": "Groq Whisper model to use.",
            },
            "temperature": {
                "type": "number",
                "default": 0.0,
                "description": "Sampling temperature.",
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
            if os.getenv("GROQ_API_KEY")
            else ToolStatus.UNAVAILABLE
        )

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return ToolResult(
                success=False,
                error="GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys and set it in .env.",
            )

        audio_path_raw = inputs.get("audio_path")
        if not audio_path_raw:
            return ToolResult(success=False, error="audio_path is required")

        audio_path = Path(audio_path_raw).resolve()
        if not audio_path.is_file():
            return ToolResult(success=False, error=f"Audio file not found: {audio_path}")

        model = inputs.get("model", "whisper-large-v3")
        temperature = float(inputs.get("temperature", 0.0))
        language = inputs.get("language")

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}

        data: dict[str, Any] = {
            "model": model,
            "response_format": "verbose_json",
            "temperature": str(temperature),
            "timestamp_granularities[]": ["segment", "word"],
        }
        if language:
            data["language"] = language

        try:
            with open(audio_path, "rb") as f:
                files = {"file": (audio_path.name, f, "audio/wav")}
                resp = requests.post(url, headers=headers, files=files, data=data, timeout=180)

            if resp.status_code != 200:
                return ToolResult(
                    success=False,
                    error=f"Groq Whisper failed HTTP {resp.status_code}: {resp.text[:400]}",
                )

            res_json = resp.json()
        except Exception as exc:
            return ToolResult(success=False, error=f"Groq Whisper request error: {exc}")

        full_transcript = res_json.get("text", "").strip()
        detected_language = res_json.get("language", language)
        duration = float(res_json.get("duration", 0.0))

        raw_segments = res_json.get("segments", [])
        raw_words = res_json.get("words", [])

        segments: list[dict[str, Any]] = []
        for idx, s in enumerate(raw_segments):
            segments.append({
                "id": idx,
                "start": round(float(s.get("start", 0.0)), 3),
                "end": round(float(s.get("end", 0.0)), 3),
                "text": s.get("text", "").strip(),
            })

        word_timestamps: list[dict[str, Any]] = []
        for w in raw_words:
            word_timestamps.append({
                "word": w.get("word", ""),
                "start": round(float(w.get("start", 0.0)), 3),
                "end": round(float(w.get("end", 0.0)), 3),
                "probability": 1.0,
            })

        if not segments and full_transcript:
            segments.append({
                "id": 0,
                "start": 0.0,
                "end": round(duration, 3),
                "text": full_transcript,
            })

        result_data = {
            "transcript": full_transcript,
            "segments": segments,
            "word_timestamps": word_timestamps,
            "language": detected_language,
            "duration_seconds": round(duration, 3),
            "provider": "groq",
            "model": model,
        }

        output_dir_raw = inputs.get("output_dir")
        output_dir = Path(output_dir_raw).resolve() if output_dir_raw else audio_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / f"{audio_path.stem}_groq_transcript.json"
        artifact_path.write_text(json.dumps(result_data, indent=2, ensure_ascii=False), encoding="utf-8")

        return ToolResult(
            success=True,
            data=result_data,
            artifacts=[str(artifact_path)],
        )
