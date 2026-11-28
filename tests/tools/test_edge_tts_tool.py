"""Tests for EdgeTTSTool (tools/audio/edge_tts_tool.py)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.audio.edge_tts_tool import EdgeTTSTool, _resolve_voice, _LANG_VOICE_MAP
from tools.base_tool import ToolStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tool() -> EdgeTTSTool:
    return EdgeTTSTool()


# ---------------------------------------------------------------------------
# Identity / metadata
# ---------------------------------------------------------------------------


def test_tool_name():
    assert _make_tool().name == "edge_tts"


def test_tool_provider():
    assert _make_tool().provider == "microsoft_edge"


def test_tool_capability():
    assert _make_tool().capability == "tts"


def test_tool_cost_zero():
    tool = _make_tool()
    assert tool.estimate_cost({}) == 0.0


def test_tool_has_fallbacks():
    tool = _make_tool()
    assert "piper_tts" in tool.fallback_tools


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


def test_get_status_available_when_edge_tts_importable(monkeypatch):
    monkeypatch.setattr(
        "tools.audio.edge_tts_tool.importlib.util.find_spec",
        lambda name: MagicMock(),  # non-None → found
    )
    assert _make_tool().get_status() == ToolStatus.AVAILABLE


def test_get_status_unavailable_when_edge_tts_missing(monkeypatch):
    monkeypatch.setattr(
        "tools.audio.edge_tts_tool.importlib.util.find_spec",
        lambda name: None,  # None → not found
    )
    assert _make_tool().get_status() == ToolStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Language auto-routing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "language,expected_fragment",
    [
        ("bn-IN", "TanishaaNeural"),
        ("bn-BD", "NabanitaNeural"),
        ("hi-IN", "SwaraNeural"),
        ("en-US", "AndrewNeural"),
        ("en", "AndrewNeural"),
        ("bn", "TanishaaNeural"),
        ("en-IN", "NeerjaExpressiveNeural"),
        ("ta-IN", "PallaviNeural"),
        ("te-IN", "ShrutiNeural"),
    ],
)
def test_language_auto_routing(language, expected_fragment):
    voice = _resolve_voice(None, language)
    assert expected_fragment in voice, f"Expected {expected_fragment!r} in voice for {language!r}, got {voice!r}"


def test_explicit_voice_overrides_language():
    voice = _resolve_voice("en-GB-RyanNeural", "bn-IN")
    assert voice == "en-GB-RyanNeural"


def test_no_voice_no_language_returns_default():
    voice = _resolve_voice(None, None)
    assert "AndrewNeural" in voice


def test_unknown_language_returns_default():
    voice = _resolve_voice(None, "xx-YY")
    assert "AndrewNeural" in voice


def test_lang_voice_map_has_indic_entries():
    for lang in ("bn-IN", "bn-BD", "hi-IN", "ta-IN", "te-IN", "ml-IN", "kn-IN", "mr-IN"):
        assert lang in _LANG_VOICE_MAP, f"{lang} missing from LANG_VOICE_MAP"


# ---------------------------------------------------------------------------
# execute — missing package
# ---------------------------------------------------------------------------


def test_execute_returns_error_when_package_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("tools.audio.edge_tts_tool._have_edge_tts", lambda: False)
    tool = _make_tool()
    result = tool.execute({"text": "hello", "output_path": str(tmp_path / "out.mp3")})
    assert not result.success
    assert "edge-tts" in result.error.lower() or "pip install" in result.error.lower()


# ---------------------------------------------------------------------------
# execute — empty text
# ---------------------------------------------------------------------------


def test_execute_rejects_empty_text(monkeypatch, tmp_path):
    monkeypatch.setattr("tools.audio.edge_tts_tool._have_edge_tts", lambda: True)
    tool = _make_tool()
    result = tool.execute({"text": "   ", "output_path": str(tmp_path / "out.mp3")})
    assert not result.success
    assert "non-empty" in result.error.lower() or "text" in result.error.lower()


# ---------------------------------------------------------------------------
# execute — successful synthesis (async mock)
# ---------------------------------------------------------------------------


def test_execute_success_with_mocked_edge_tts(monkeypatch, tmp_path):
    out_path = tmp_path / "speech.mp3"

    # Build a fake Communicate class whose save() coroutine writes a dummy file.
    async def _fake_save(path: str) -> None:
        Path(path).write_bytes(b"\xff\xfb" * 200)  # 400-byte fake MP3

    fake_communicate = MagicMock()
    fake_communicate.save = _fake_save

    fake_edge_tts_mod = ModuleType("edge_tts")
    fake_edge_tts_mod.Communicate = MagicMock(return_value=fake_communicate)

    monkeypatch.setattr("tools.audio.edge_tts_tool._have_edge_tts", lambda: True)

    import sys

    sys.modules["edge_tts"] = fake_edge_tts_mod
    try:
        tool = _make_tool()
        result = tool.execute(
            {
                "text": "Hello world",
                "output_path": str(out_path),
                "language": "en-US",
            }
        )
    finally:
        del sys.modules["edge_tts"]

    assert result.success, result.error
    assert result.data["format"] == "mp3"
    assert "AndrewNeural" in result.data["voice"]
    assert Path(result.data["output_path"]).exists()


# ---------------------------------------------------------------------------
# execute — auto output path
# ---------------------------------------------------------------------------


def test_execute_generates_output_path_when_omitted(monkeypatch):
    async def _fake_save(path: str) -> None:
        Path(path).write_bytes(b"\xff\xfb" * 200)

    fake_communicate = MagicMock()
    fake_communicate.save = _fake_save

    fake_mod = ModuleType("edge_tts")
    fake_mod.Communicate = MagicMock(return_value=fake_communicate)

    monkeypatch.setattr("tools.audio.edge_tts_tool._have_edge_tts", lambda: True)

    import sys

    sys.modules["edge_tts"] = fake_mod
    try:
        tool = _make_tool()
        result = tool.execute({"text": "Auto path test"})
    finally:
        del sys.modules["edge_tts"]

    assert result.success, result.error
    assert result.data["output_path"].endswith(".mp3")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def test_get_schema_returns_valid_dict():
    schema = _make_tool().get_schema()
    assert schema["name"] == "edge_tts"
    assert "text" in schema["parameters"]["properties"]
    assert "text" in schema["parameters"]["required"]


# ---------------------------------------------------------------------------
# Registry discovery
# ---------------------------------------------------------------------------


def test_registry_discovers_edge_tts():
    from tools.tool_registry import ToolRegistry

    registry = ToolRegistry()
    registry.discover("tools")
    names = registry.list_all()
    assert "edge_tts" in names, f"edge_tts not found in registry. Found: {names[:10]}"


def test_execute_retries_with_fallback_voice_on_no_audio_received(monkeypatch, tmp_path):
    calls: list[str] = []

    class _FakeCommunicate:
        def __init__(self, *, text: str, voice: str, **_kwargs):
            self.voice = voice
            calls.append(voice)

        async def save(self, path: str) -> None:
            if self.voice != "en-US-AriaNeural":
                raise RuntimeError("No audio was received. Please verify that your parameters are correct.")
            Path(path).write_bytes(b"\xff\xfb" * 200)

    fake_mod = ModuleType("edge_tts")
    fake_mod.Communicate = _FakeCommunicate
    monkeypatch.setattr("tools.audio.edge_tts_tool._have_edge_tts", lambda: True)

    import sys

    sys.modules["edge_tts"] = fake_mod
    try:
        out_file = tmp_path / "retry.mp3"
        result = _make_tool().execute({"text": "Retry voice test", "output_path": str(out_file)})
    finally:
        del sys.modules["edge_tts"]

    assert result.success, result.error
    assert len(calls) == 2
    assert result.data["voice"] == "en-US-AriaNeural"
    assert out_file.is_file()
