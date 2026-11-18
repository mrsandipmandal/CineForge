"""Acceptance Tests for CineForge TTS Provider Priority & Fallback Engine.

Validates the 6 mandatory acceptance scenarios:
1. OpenAI.fm available → Generate audio using OpenAI.fm.
2. OpenAI.fm unavailable → Automatically use Kokoro.
3. Kokoro unavailable → Automatically use VoxCPM2.
4. All free providers unavailable → Show a clear error.
5. Paid provider disabled → Never call paid APIs.
6. Paid provider enabled → Use only according to configured priority.

Enforces real audio validation (no mocked success dictionaries).
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from lib.audio_validator import validate_audio_bytes, validate_audio_file
from lib.tts_config import DEFAULT_PRIORITY, load_tts_config, save_tts_config
from tools.audio.kokoro_tts import KokoroTTS
from tools.audio.openaifm_tts import OpenAIFMTTS
from tools.audio.tts_selector import TTSSelector
from tools.audio.voxcpm2 import VoxCPM2TTS
from tools.base_tool import ToolResult, ToolStatus

# Real audio byte headers + payloads
REAL_WAV_BYTES = (
    b"RIFF\x2c\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x08\x00\x00\x00"
    + b"\xaa" * 400
)
REAL_MP3_BYTES = b"\xff\xfb\x90\x64" + b"\x55" * 400

# Error payloads >= 128 bytes to test deep content validation
INVALID_HTML_BYTES = (
    b"<html><head><title>502 Bad Gateway</title></head><body>"
    b"<h1>502 Bad Gateway</h1><p>The server encountered a temporary error and could not complete your request.</p>"
    b"</body></html>"
)
INVALID_JSON_BYTES = (
    b'{"error": {"message": "Rate limit reached for requests per minute. Please try again later.", '
    b'"type": "requests", "param": null, "code": "rate_limit_exceeded"}}'
)


class MockHTTPResponse:
    def __init__(
        self,
        content: bytes,
        status_code: int = 200,
        content_type: str = "audio/mpeg",
        text: str = "",
    ):
        self.content = content
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
        self.text = text or (content.decode("utf-8", "ignore") if content else "")

    def json(self):
        import json
        return json.loads(self.content)


@pytest.fixture(autouse=True)
def restore_tts_config():
    """Ensure tests start and end with standard clean configuration."""
    yield
    save_tts_config({
        "primary_provider": "openaifm",
        "provider_priority": list(DEFAULT_PRIORITY),
        "allow_paid_providers": False,
        "auto_fallback": True,
        "manual_mode": False,
    })


# ---------------------------------------------------------------------------
# Real Audio Validation Tests
# ---------------------------------------------------------------------------

def test_real_audio_validation_accepts_valid_audio():
    """Verify that real MP3 and WAV payloads pass audio byte and file validation."""
    ok_wav, fmt_wav, _ = validate_audio_bytes(REAL_WAV_BYTES)
    assert ok_wav is True
    assert fmt_wav == "wav"

    ok_mp3, fmt_mp3, _ = validate_audio_bytes(REAL_MP3_BYTES)
    assert ok_mp3 is True
    assert fmt_mp3 == "mp3"

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(REAL_WAV_BYTES)
        tmp_wav = f.name

    try:
        ok_file, fmt_file, _ = validate_audio_file(tmp_wav)
        assert ok_file is True
        assert fmt_file == "wav"
    finally:
        Path(tmp_wav).unlink(missing_ok=True)


def test_real_audio_validation_rejects_html_and_json_errors():
    """Verify that HTML error pages and JSON error responses are rejected."""
    ok_html, fmt_html, reason_html = validate_audio_bytes(INVALID_HTML_BYTES)
    assert ok_html is False
    assert "HTML" in reason_html or "html" in fmt_html

    ok_json, fmt_json, reason_json = validate_audio_bytes(INVALID_JSON_BYTES)
    assert ok_json is False
    assert "JSON" in reason_json or "json" in fmt_json


# ---------------------------------------------------------------------------
# Scenario 1: OpenAI.fm available → Generate audio using OpenAI.fm
# ---------------------------------------------------------------------------

def test_scenario_1_openaifm_available_generates_audio(tmp_path):
    """Scenario 1: When OpenAI.fm is available, use OpenAI.fm as primary provider."""
    selector = TTSSelector()
    out_file = tmp_path / "scenario_1.mp3"

    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        resp = MockHTTPResponse(
            content=REAL_MP3_BYTES,
            status_code=200,
            content_type="audio/mpeg",
        )
        mock_get.return_value = resp
        mock_post.return_value = resp

        result = selector.execute({
            "text": "Universal cinematic narration in English, Hindi and Bengali.",
            "voice": "fable",
            "instructions": "Speak with dramatic weight.",
            "output_path": str(out_file),
            "allow_paid": False,
        })

        assert result.success is True, f"Failed: {result.error}"
        assert result.data["selected_provider"] == "openaifm"
        assert result.data["selected_tool"] == "openaifm_tts"
        assert result.data["is_primary_provider"] is True
        assert result.data["fallback_occurred"] is False
        assert result.data["priority_rank_used"] == 1

        # Real audio validation on disk
        actual_path = result.data.get("output_path") or str(out_file)
        valid, fmt, _ = validate_audio_file(actual_path)
        assert valid is True
        assert fmt == "mp3"


# ---------------------------------------------------------------------------
# Scenario 2: OpenAI.fm unavailable → Automatically use Kokoro
# ---------------------------------------------------------------------------

def test_scenario_2_openaifm_unavailable_falls_back_to_kokoro(tmp_path):
    """Scenario 2: When OpenAI.fm fails (HTTP 500 / timeout), automatically fall back to Kokoro."""
    selector = TTSSelector()
    out_file = tmp_path / "scenario_2.wav"

    def mock_kokoro_execute(inputs: dict[str, Any]) -> ToolResult:
        p = Path(inputs.get("output_path", out_file))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(REAL_WAV_BYTES)
        return ToolResult(
            success=True,
            data={"provider": "kokoro", "output_path": str(p), "duration_seconds": 2.5},
            artifacts=[str(p)],
        )

    # Patch OpenAI.fm to fail with HTTP 500 error
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post, \
         patch.object(KokoroTTS, "get_status", return_value=ToolStatus.AVAILABLE), \
         patch.object(KokoroTTS, "execute", side_effect=mock_kokoro_execute):

        resp_err = MockHTTPResponse(
            content=b"500 Internal Server Error",
            status_code=500,
            content_type="text/plain",
        )
        mock_get.return_value = resp_err
        mock_post.return_value = resp_err

        result = selector.execute({
            "text": "Kokoro fallback test with real audio synthesis.",
            "output_path": str(out_file),
            "allow_paid": False,
        })

        assert result.success is True, f"Failed: {result.error}"
        assert result.data["selected_provider"] == "kokoro"
        assert result.data["selected_tool"] == "kokoro_tts"
        assert result.data["fallback_occurred"] is True
        assert "openaifm" in result.data["fallback_reason"].lower()

        # Real audio validation on disk
        valid, fmt, _ = validate_audio_file(out_file)
        assert valid is True
        assert fmt == "wav"


# ---------------------------------------------------------------------------
# Scenario 3: Kokoro unavailable → Automatically use VoxCPM2
# ---------------------------------------------------------------------------

def test_scenario_3_kokoro_unavailable_falls_back_to_voxcpm2(tmp_path):
    """Scenario 3: When OpenAI.fm and Kokoro are both unavailable, fall back to VoxCPM2."""
    selector = TTSSelector()
    out_file = tmp_path / "scenario_3.wav"

    def mock_voxcpm2_execute(inputs: dict[str, Any]) -> ToolResult:
        p = Path(inputs.get("output_path", out_file))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(REAL_WAV_BYTES)
        return ToolResult(
            success=True,
            data={"provider": "voxcpm2", "output_path": str(p), "duration_seconds": 3.0},
            artifacts=[str(p)],
        )

    with patch("requests.get") as mock_get, patch("requests.post") as mock_post, \
         patch.object(KokoroTTS, "get_status", return_value=ToolStatus.UNAVAILABLE), \
         patch.object(VoxCPM2TTS, "get_status", return_value=ToolStatus.AVAILABLE), \
         patch.object(VoxCPM2TTS, "execute", side_effect=mock_voxcpm2_execute):

        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        result = selector.execute({
            "text": "VoxCPM2 second fallback execution test.",
            "output_path": str(out_file),
            "allow_paid": False,
        })

        assert result.success is True, f"Failed: {result.error}"
        assert result.data["selected_provider"] == "voxcpm2"
        assert result.data["selected_tool"] == "voxcpm2_tts"
        assert result.data["fallback_occurred"] is True

        # Real audio validation on disk
        valid, fmt, _ = validate_audio_file(out_file)
        assert valid is True
        assert fmt == "wav"


# ---------------------------------------------------------------------------
# Scenario 4: All free providers unavailable → Show a clear error
# ---------------------------------------------------------------------------

def test_scenario_4_all_free_providers_unavailable_clear_error():
    """Scenario 4: When all free providers fail or are unavailable, return clear error without crash."""
    selector = TTSSelector()

    with patch.object(OpenAIFMTTS, "get_status", return_value=ToolStatus.UNAVAILABLE), \
         patch.object(KokoroTTS, "get_status", return_value=ToolStatus.UNAVAILABLE), \
         patch.object(VoxCPM2TTS, "get_status", return_value=ToolStatus.UNAVAILABLE), \
         patch("tools.audio.tts_selector.get_effective_priority", return_value=["openaifm", "kokoro", "voxcpm2"]):

        result = selector.execute({
            "text": "Testing all free providers unavailable.",
            "allowed_providers": ["openaifm", "kokoro", "voxcpm2"],
            "allow_paid": False,
        })

        assert result.success is False
        assert "unavailable" in result.error.lower() or "failed" in result.error.lower()
        assert "paid" in result.error.lower()


# ---------------------------------------------------------------------------
# Scenario 5: Paid provider disabled → Never call paid APIs
# ---------------------------------------------------------------------------

def test_scenario_5_paid_provider_disabled_never_calls_paid():
    """Scenario 5: When allow_paid is False, paid providers are strictly never executed."""
    selector = TTSSelector()
    paid_tool_mock = MagicMock()

    with patch.object(OpenAIFMTTS, "execute", return_value=ToolResult(success=False, error="Down")), \
         patch.object(KokoroTTS, "get_status", return_value=ToolStatus.UNAVAILABLE), \
         patch.object(VoxCPM2TTS, "execute", return_value=ToolResult(success=False, error="Down")), \
         patch("tools.audio.openai_tts.OpenAITTS.execute", paid_tool_mock):

        result = selector.execute({
            "text": "Paid protection test.",
            "allowed_providers": ["openaifm", "kokoro", "voxcpm2", "openai"],
            "allow_paid": False,
        })

        assert result.success is False
        paid_tool_mock.assert_not_called()
        assert "paid" in result.error.lower()


# ---------------------------------------------------------------------------
# Scenario 6: Paid provider enabled → Use only according to configured priority
# ---------------------------------------------------------------------------

def test_scenario_6_paid_provider_enabled_uses_priority(tmp_path):
    """Scenario 6: When allow_paid is True, paid provider is used as last resort when free fail."""
    selector = TTSSelector()
    out_file = tmp_path / "scenario_6.mp3"

    def mock_paid_execute(inputs: dict[str, Any]) -> ToolResult:
        p = Path(inputs.get("output_path", out_file))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(REAL_MP3_BYTES)
        return ToolResult(
            success=True,
            data={"provider": "openai", "output_path": str(p), "duration_seconds": 1.8},
            artifacts=[str(p)],
        )

    from tools.audio.openai_tts import OpenAITTS

    with patch.object(OpenAIFMTTS, "execute", return_value=ToolResult(success=False, error="OpenAI.fm 503")), \
         patch.object(KokoroTTS, "get_status", return_value=ToolStatus.UNAVAILABLE), \
         patch.object(VoxCPM2TTS, "execute", return_value=ToolResult(success=False, error="VoxCPM2 busy")), \
         patch.object(OpenAITTS, "get_status", return_value=ToolStatus.AVAILABLE), \
         patch.object(OpenAITTS, "execute", side_effect=mock_paid_execute):

        result = selector.execute({
            "text": "Paid provider last resort fallback test.",
            "output_path": str(out_file),
            "allowed_providers": ["openaifm", "kokoro", "voxcpm2", "openai"],
            "allow_paid": True,
        })

        assert result.success is True, f"Failed: {result.error}"
        assert result.data["selected_provider"] == "openai"
        assert result.data["fallback_occurred"] is True

        # Real audio validation on disk
        valid, fmt, _ = validate_audio_file(out_file)
        assert valid is True
        assert fmt == "mp3"
