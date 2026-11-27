"""Microsoft Edge TTS — zero-key neural text-to-speech provider.

Leverages the ``edge-tts`` Python package (which proxies Microsoft's
Edge browser read-aloud service) to generate high-quality MP3 narration
in dozens of languages at no API cost.

This tool is entirely **offline-free** in the sense that it needs no API
key or account — but it *does* make HTTPS calls to Microsoft's TTS
endpoint at runtime (similar to how the Edge browser does).

Install:
    pip install edge-tts
    # or via the cineforge extra:
    pip install 'cineforge[tts-local]'

Docs: https://github.com/rany2/edge-tts
"""

from __future__ import annotations

import asyncio
import importlib.util
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

# ---------------------------------------------------------------------------
# Language → default voice mapping
# ---------------------------------------------------------------------------
_LANG_VOICE_MAP: dict[str, str] = {
    "bn-IN": "bn-IN-TanishaaNeural",
    "bn-BD": "bn-BD-NabanitaNeural",
    "hi-IN": "hi-IN-SwaraNeural",
    "en-US": "en-US-AndrewMultilingualNeural",
    "en-IN": "en-IN-NeerjaExpressiveNeural",
    "en-GB": "en-GB-SoniaNeural",
    "en-AU": "en-AU-NatashaNeural",
    "ta-IN": "ta-IN-PallaviNeural",
    "te-IN": "te-IN-ShrutiNeural",
    "ml-IN": "ml-IN-SobhanaNeural",
    "kn-IN": "kn-IN-SapnaNeural",
    "mr-IN": "mr-IN-AarohiNeural",
    "gu-IN": "gu-IN-DhwaniNeural",
    "pa-IN": "pa-IN-OjasvNeural",
    "ur-PK": "ur-PK-UzmaNeural",
    "zh-CN": "zh-CN-XiaoxiaoNeural",
    "ja-JP": "ja-JP-NanamiNeural",
    "ko-KR": "ko-KR-SunHiNeural",
    "fr-FR": "fr-FR-DeniseNeural",
    "de-DE": "de-DE-KatjaNeural",
    "es-ES": "es-ES-ElviraNeural",
    "pt-BR": "pt-BR-FranciscaNeural",
    "ar-SA": "ar-SA-ZariyahNeural",
    "ru-RU": "ru-RU-SvetlanaNeural",
    "it-IT": "it-IT-ElsaNeural",
    "pl-PL": "pl-PL-ZofiaNeural",
    "nl-NL": "nl-NL-ColetteNeural",
    "tr-TR": "tr-TR-EmelNeural",
    "vi-VN": "vi-VN-HoaiMyNeural",
    "id-ID": "id-ID-GadisNeural",
    "th-TH": "th-TH-PremwadeeNeural",
    "ms-MY": "ms-MY-YasminNeural",
    "fi-FI": "fi-FI-NooraNeural",
    "sv-SE": "sv-SE-SofieNeural",
    "nb-NO": "nb-NO-PernilleNeural",
    "da-DK": "da-DK-ChristelNeural",
    "ro-RO": "ro-RO-AlinaNeural",
    "hu-HU": "hu-HU-NoemiNeural",
    "cs-CZ": "cs-CZ-VlastaNeural",
    "sk-SK": "sk-SK-ViktoriaNeural",
    "uk-UA": "uk-UA-PolinaNeural",
    "el-GR": "el-GR-AthinaNeural",
    "he-IL": "he-IL-HilaNeural",
    "af-ZA": "af-ZA-AdriNeural",
    "sw-KE": "sw-KE-ZuriNeural",
    "am-ET": "am-ET-MekdesNeural",
}

_DEFAULT_VOICE = "en-US-AndrewMultilingualNeural"


def _resolve_voice(voice: str | None, language: str | None) -> str:
    """Return the best voice for the given (voice, language) pair."""
    if voice:
        return voice
    if language:
        return _LANG_VOICE_MAP.get(language, _DEFAULT_VOICE)
    return _DEFAULT_VOICE


def _have_edge_tts() -> bool:
    return importlib.util.find_spec("edge_tts") is not None


class EdgeTTSTool(BaseTool):
    """Zero-key neural TTS via Microsoft Edge read-aloud service."""

    name = "edge_tts"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "microsoft_edge"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.API
    cost_per_call = 0.0

    # edge-tts package is optional — not a hard dependency of cineforge core.
    dependencies = []
    install_instructions = (
        "Install the edge-tts package:\n"
        "  pip install edge-tts\n"
        "Or via the CineForge TTS extra:\n"
        "  pip install 'cineforge[tts-local]'"
    )
    fallback_tools = ["piper_tts", "openrouter_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = [
        "text_to_speech",
        "multilingual",
        "voice_selection",
        "language_auto_routing",
    ]
    supports = {
        "voice_cloning": False,
        "multilingual": True,
        "offline": False,
        "native_audio": True,
        "zero_key": True,
    }
    best_for = [
        "zero-key high-quality neural narration",
        "multilingual TTS without an API subscription",
        "Bengali, Hindi, and 70+ language voices",
        "rapid prototyping before committing to a paid TTS provider",
    ]
    not_good_for = [
        "fully offline (air-gapped) environments — it calls Microsoft servers",
        "voice cloning or custom voice identity",
    ]

    # Expose the voice map so agents can enumerate supported languages.
    LANG_VOICE_MAP = _LANG_VOICE_MAP

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to synthesise into speech.",
            },
            "output_path": {
                "type": "string",
                "description": "Destination path for the MP3 file. Auto-generated if omitted.",
            },
            "voice": {
                "type": "string",
                "description": (
                    "Edge TTS voice name, e.g. 'en-US-AndrewMultilingualNeural'. "
                    "Overrides 'language' when both are set."
                ),
            },
            "language": {
                "type": "string",
                "description": (
                    "BCP-47 language tag, e.g. 'bn-IN', 'hi-IN', 'en-US'. "
                    "Auto-maps to the recommended voice for that locale."
                ),
            },
            "rate": {
                "type": "string",
                "default": "+0%",
                "description": "Speaking rate adjustment, e.g. '+0%', '+10%', '-5%'.",
            },
            "volume": {
                "type": "string",
                "default": "+0%",
                "description": "Volume adjustment, e.g. '+0%', '+20%'.",
            },
            "pitch": {
                "type": "string",
                "default": "+0Hz",
                "description": "Pitch adjustment, e.g. '+0Hz', '+50Hz'.",
            },
        },
    }

    def get_status(self) -> ToolStatus:
        """Available when the ``edge-tts`` package is importable."""
        if _have_edge_tts():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def get_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": (
                "Generate MP3 speech from text using Microsoft Edge's neural TTS service. "
                "No API key required. Supports 70+ languages and 400+ voices."
            ),
            "parameters": self.input_schema,
        }

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        if not _have_edge_tts():
            return ToolResult(
                success=False,
                error=(
                    "edge-tts package is not installed. "
                    + self.install_instructions
                ),
            )

        text: str = inputs.get("text", "")
        if not text or not text.strip():
            return ToolResult(success=False, error="'text' must be a non-empty string.")

        import edge_tts  # type: ignore  # noqa: PLC0415

        voice = _resolve_voice(
            inputs.get("voice"),
            inputs.get("language"),
        )
        rate: str = inputs.get("rate", "+0%")
        volume: str = inputs.get("volume", "+0%")
        pitch: str = inputs.get("pitch", "+0Hz")

        # Resolve output path.
        output_path_raw = inputs.get("output_path")
        if output_path_raw:
            out = Path(output_path_raw)
        else:
            import tempfile

            out = Path(tempfile.mktemp(suffix=".mp3", prefix="edge_tts_"))

        out.parent.mkdir(parents=True, exist_ok=True)

        start = time.time()
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                volume=volume,
                pitch=pitch,
            )
            asyncio.run(communicate.save(str(out)))
        except Exception as exc:  # pragma: no cover
            return ToolResult(success=False, error=f"edge-tts synthesis failed: {exc}")

        elapsed = round(time.time() - start, 2)

        if not out.exists() or out.stat().st_size < 256:
            return ToolResult(
                success=False,
                error=f"edge-tts produced an empty or missing file at {out}",
            )

        return ToolResult(
            success=True,
            data={
                "output_path": str(out),
                "voice": voice,
                "language": inputs.get("language", ""),
                "format": "mp3",
                "duration_hint": "unknown",  # edge-tts doesn't expose duration
                "elapsed_seconds": elapsed,
                "text_length": len(text),
            },
            artifacts=[str(out)],
            duration_seconds=elapsed,
            cost_usd=0.0,
        )
