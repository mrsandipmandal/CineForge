"""Sarvam AI Text-to-Speech provider tool.

Specialized for native Indian languages including Bengali (bn-IN), Hindi (hi-IN),
Tamil (ta-IN), Telugu (te-IN), Kannada (kn-IN), Malayalam (ml-IN), Marathi (mr-IN),
Gujarati (gu-IN), Punjabi (pa-IN), and Odia (od-IN). Uses the Bulbul neural speech engine.
"""

from __future__ import annotations

import base64
import re
from typing import Any
import requests

from tools.audio._speech_api import SpeechAPI
from tools.base_tool import ToolResult

# Map common language codes / aliases to Sarvam BCP-47 codes
_LANG_MAP = {
    "bn": "bn-IN",
    "bengali": "bn-IN",
    "bn-in": "bn-IN",
    "hi": "hi-IN",
    "hindi": "hi-IN",
    "hi-in": "hi-IN",
    "ta": "ta-IN",
    "tamil": "ta-IN",
    "ta-in": "ta-IN",
    "te": "te-IN",
    "telugu": "te-IN",
    "te-in": "te-IN",
    "kn": "kn-IN",
    "kannada": "kn-IN",
    "kn-in": "kn-IN",
    "ml": "ml-IN",
    "malayalam": "ml-IN",
    "ml-in": "ml-IN",
    "mr": "mr-IN",
    "marathi": "mr-IN",
    "mr-in": "mr-IN",
    "gu": "gu-IN",
    "gujarati": "gu-IN",
    "gu-in": "gu-IN",
    "pa": "pa-IN",
    "punjabi": "pa-IN",
    "pa-in": "pa-IN",
    "od": "od-IN",
    "odia": "od-IN",
    "od-in": "od-IN",
    "en": "en-IN",
    "en-in": "en-IN",
}


def _chunk_text(text: str, max_chars: int = 480) -> list[str]:
    """Split long text into sentence chunks within Sarvam's character limits."""
    if len(text) <= max_chars:
        return [text]

    # Split by common sentence delimiters across English and Indic scripts
    sentences = re.split(r"([।\.\?!;\n]+)", text)
    chunks: list[str] = []
    current = ""

    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        sep = sentences[i + 1] if i + 1 < len(sentences) else ""
        piece = (sentence + sep).strip()
        if not piece:
            continue
        if len(current) + len(piece) + 1 <= max_chars:
            current = (current + " " + piece).strip()
        else:
            if current:
                chunks.append(current)
            if len(piece) > max_chars:
                # Sub-chunk by commas or whitespace if a single sentence exceeds limit
                words = piece.split(" ")
                sub = ""
                for w in words:
                    if len(sub) + len(w) + 1 <= max_chars:
                        sub = (sub + " " + w).strip()
                    else:
                        if sub:
                            chunks.append(sub)
                        sub = w
                current = sub
            else:
                current = piece

    if current:
        chunks.append(current)

    return chunks if chunks else [text]


class SarvamTTS(SpeechAPI):
    name = "sarvam_tts"
    provider = "sarvam"
    credential = "SARVAM_API_KEY"
    dependencies = ["env:SARVAM_API_KEY"]
    install_instructions = (
        "Configure SARVAM_API_KEY from https://dashboard.sarvam.ai/.\n"
        "Provides native Bengali (bn-IN), Hindi (hi-IN) and Indic neural speech synthesis."
    )
    supports = {
        "native_audio": True,
        "multilingual": True,
        "bengali": True,
        "hindi": True,
        "indic": True,
        "timestamps": False,
    }
    best_for = [
        "Native Bengali (bn-IN) narration with authentic cadence and pronunciation",
        "High-fidelity Hindi and 10+ Indic languages via Sarvam Bulbul engine",
    ]
    not_good_for = [
        "Fully offline synthesis (use piper_tts)",
        "Direct voice cloning from sample audio (use fish_audio_tts or elevenlabs_tts)",
    ]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string", "minLength": 1, "maxLength": 60000},
            "language": {
                "type": "string",
                "description": "Target Indic language code (e.g. bn-IN, hi-IN, ta-IN). Default: bn-IN.",
            },
            "voice_id": {
                "type": "string",
                "description": "Speaker name (e.g. ritu, aditya, priya, neha, rahul, rohan, kavya, ishita). Default: ritu.",
            },
            "speaker": {
                "type": "string",
                "description": "Alias for voice_id.",
            },
            "model": {
                "type": "string",
                "enum": ["bulbul:v1", "bulbul:v2", "bulbul:v3"],
                "default": "bulbul:v3",
                "description": "Sarvam TTS model version. Default: bulbul:v3.",
            },
            "speed": {
                "type": "number",
                "minimum": 0.5,
                "maximum": 2.0,
                "default": 1.0,
                "description": "Pace of speech.",
            },
            "pitch": {
                "type": "number",
                "minimum": -1.0,
                "maximum": 1.0,
                "default": 0.0,
                "description": "Pitch adjustment.",
            },
            "output_path": {"type": "string"},
            "output_format": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "codec": {"enum": ["wav", "mp3"]},
                    "sample_rate": {"enum": [8000, 16000, 22050]},
                },
            },
        },
    }

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        # Infer output_format codec from output_path extension if not specified
        out_path = inputs.get("output_path")
        if out_path and "output_format" not in inputs:
            from pathlib import Path
            ext = Path(out_path).suffix.lower().lstrip(".")
            if ext in {"wav", "mp3"}:
                inputs["output_format"] = {"codec": ext}
        return super().execute(inputs)

    def generate(self, inputs: dict[str, Any], key: str) -> ToolResult:
        text = inputs.get("text", "").strip()
        if not text:
            raise ValueError("text is required")

        # Resolve language code
        raw_lang = inputs.get("language", "bn-IN").strip().lower()
        target_lang = _LANG_MAP.get(raw_lang, "bn-IN")

        speaker = inputs.get("voice_id") or inputs.get("speaker") or "ritu"
        model = inputs.get("model", "bulbul:v3")
        speed = float(inputs.get("speed", 1.0))
        pitch = float(inputs.get("pitch", 0.0))

        fmt = inputs.get("output_format", {})
        if isinstance(fmt, str):
            codec = fmt
            sample_rate = 22050
        else:
            codec = fmt.get("codec", "wav")
            sample_rate = fmt.get("sample_rate", 22050)

        chunks = _chunk_text(text, max_chars=450)
        audio_bytes_list: list[bytes] = []

        headers = {
            "api-subscription-key": key,
            "Content-Type": "application/json",
        }

        for chunk in chunks:
            payload = {
                "inputs": [chunk],
                "target_language_code": target_lang,
                "speaker": speaker,
                "pitch": pitch,
                "pace": speed,
                "loudness": 1.0,
                "speech_sample_rate": sample_rate,
                "enable_preprocessing": True,
                "model": model,
            }

            resp = requests.post(
                "https://api.sarvam.ai/text-to-speech",
                headers=headers,
                json=payload,
                timeout=90,
            )
            resp.raise_for_status()
            data = resp.json()

            audios = data.get("audios", [])
            if not audios:
                raise ValueError("Sarvam AI returned no audio data")

            for a in audios:
                audio_bytes_list.append(base64.b64decode(a))

        # Concatenate audio bytes (WAV headers if multiple chunks or raw binary)
        combined_audio = b"".join(audio_bytes_list)

        suffix = f".{codec}"
        return self.save_audio(
            inputs,
            combined_audio,
            model=f"sarvam-{model}",
            suffix=suffix,
            extra={
                "language": target_lang,
                "speaker": speaker,
                "chunks_count": len(chunks),
                "model": model,
            },
        )
