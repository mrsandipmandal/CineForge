"""Tests for TTS selector language routing and provider ranking."""
import pytest
from unittest.mock import MagicMock, patch
from lib.scoring import _compute_task_fit, normalize_task_context


def test_bengali_language_code_boosts_multilingual_task_fit():
    """Bengali language_code should produce task_fit > 0.3 for multilingual providers."""
    from tools.audio.tts_selector import TTSSelector
    selector = TTSSelector()
    inputs = {"text": "আমাদের পণ্য সম্পর্কে জানুন", "language_code": "bn-BD"}
    ctx = selector._prepare_task_context(inputs)
    # context should have multilingual signals injected
    assert "multilingual" in ctx.get("style_keywords", [])
    assert "bengali" in ctx.get("style_keywords", [])


def test_english_language_code_no_injection():
    """English language_code should not inject multilingual signals."""
    from tools.audio.tts_selector import TTSSelector
    selector = TTSSelector()
    inputs = {"text": "Hello world", "language_code": "en-US"}
    ctx = selector._prepare_task_context(inputs)
    assert "multilingual" not in ctx.get("style_keywords", [])


def test_no_language_code_no_injection():
    """No language_code should not inject anything."""
    from tools.audio.tts_selector import TTSSelector
    selector = TTSSelector()
    inputs = {"text": "Hello world"}
    ctx = selector._prepare_task_context(inputs)
    assert "bengali" not in ctx.get("style_keywords", [])


def test_hindi_language_code_injection():
    """Hindi language_code should inject indic signals."""
    from tools.audio.tts_selector import TTSSelector
    selector = TTSSelector()
    inputs = {"text": "नमस्ते", "language_code": "hi-IN"}
    ctx = selector._prepare_task_context(inputs)
    assert "hindi" in ctx.get("style_keywords", [])
    assert "indic" in ctx.get("style_keywords", [])


def test_task_fit_multilingual_vs_english_only():
    """A provider advertising 'multilingual' should score higher task_fit for Bengali intent."""
    task_fit_multilingual = _compute_task_fit(
        best_for={"multilingual", "narration", "indic languages", "bengali"},
        intent="bengali multilingual narration",
        style_keywords={"bengali", "multilingual"},
    )
    task_fit_english_only = _compute_task_fit(
        best_for={"english narration", "voiceover", "natural speech"},
        intent="bengali multilingual narration",
        style_keywords={"bengali", "multilingual"},
    )
    assert task_fit_multilingual > task_fit_english_only
