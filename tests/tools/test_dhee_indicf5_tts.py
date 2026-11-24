"""Unit tests for Dhee-Indic-F5 local voice cloning tool."""

from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from tools.base_tool import ToolRuntime, ToolStability, ToolTier
from tools.tool_registry import ToolRegistry


def test_dhee_indicf5_tool_registration():
    from tools.audio.dhee_indicf5_tts import DheeIndicF5TTS

    tool = DheeIndicF5TTS()
    assert tool.name == "dhee_indicf5_tts"
    assert tool.capability == "tts"
    assert tool.provider == "dheeyantra"
    assert tool.tier == ToolTier.GENERATE
    assert tool.stability == ToolStability.PRODUCTION
    assert tool.runtime == ToolRuntime.LOCAL_GPU
    assert "bn-IN" in tool.supports["languages"]
    assert "hi-IN" in tool.supports["languages"]
    assert "en-IN" in tool.supports["languages"]
    assert tool.supports.get("voice_cloning") is True
    assert tool.supports.get("multilingual") is True


def test_dhee_indicf5_sandip_profile_resolution():
    from tools.audio.dhee_indicf5_tts import DheeIndicF5TTS

    tool = DheeIndicF5TTS()
    ref_audio, ref_text = tool.resolve_sandip_reference()
    assert Path(ref_audio).exists()
    assert "নমস্কার আমি সন্দীপ" in ref_text
    assert "অডিওতে বলা কথাটি লিখলে ক্লোনিং নিখুঁত হয়" in ref_text


def test_dhee_indicf5_fallback_generation(tmp_path: Path):
    from tools.audio.dhee_indicf5_tts import DheeIndicF5TTS

    tool = DheeIndicF5TTS()
    out_file = tmp_path / "out.wav"

    # Test fallback triggered when model inference encounters missing weights/error
    with patch.object(tool, "_infer", side_effect=RuntimeError("weights missing")):
        res = tool.execute({"text": "টেস্ট বার্তা", "output_path": str(out_file)})
        assert res.success is True
        assert out_file.exists()
        assert out_file.stat().st_size > 44
        assert res.data.get("fallback_used") is True
        assert res.data.get("sample_rate") == 24000
        assert res.data.get("output_path") == str(out_file)

    # Test force_fallback option
    out_file_forced = tmp_path / "out_forced.wav"
    res_forced = tool.execute({
        "text": "টেস্ট বার্তা",
        "output_path": str(out_file_forced),
        "force_fallback": True,
    })
    assert res_forced.success is True
    assert out_file_forced.exists()
    assert out_file_forced.stat().st_size > 44
    assert res_forced.data.get("fallback_used") is True


def test_dhee_indicf5_mock_model_inference(tmp_path: Path):
    from tools.audio.dhee_indicf5_tts import DheeIndicF5TTS

    tool = DheeIndicF5TTS()
    out_file = tmp_path / "mock_infer.wav"

    # Mocking model inference layer
    with patch.object(tool, "_infer") as mock_infer:
        mock_infer.return_value = tool._create_mock_success_result(
            output_path=str(out_file),
            sample_rate=24000,
            duration_seconds=2.5,
            device="cuda",
        )
        res = tool.execute({
            "text": "জয় শ্রী রাম। অযোধ্যায় রামলালার আগমন।",
            "output_path": str(out_file),
            "device": "cuda",
        })
        assert res.success is True
        assert out_file.exists()
        assert out_file.stat().st_size > 44
        assert res.data.get("fallback_used") is False
        assert res.data.get("sample_rate") == 24000
        assert res.data.get("device") == "cuda"


def test_dhee_indicf5_empty_text_error(tmp_path: Path):
    from tools.audio.dhee_indicf5_tts import DheeIndicF5TTS

    tool = DheeIndicF5TTS()
    res = tool.execute({"text": "   ", "output_path": str(tmp_path / "empty.wav")})
    assert res.success is False
    assert "Text input is required" in res.error


def test_dhee_indicf5_tool_registry_discovery():
    reg = ToolRegistry()
    reg.discover("tools")
    tool = reg.get("dhee_indicf5_tts")
    assert tool is not None
    assert tool.capability == "tts"
    assert tool.provider == "dheeyantra"

