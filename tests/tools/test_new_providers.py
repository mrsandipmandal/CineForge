"""Unit and contract tests for Sarvam AI, Groq, and OpenRouter tools.

Monkeypatches network requests so tests run reliably offline and in CI/CD.
"""

import json
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.base_tool import BaseTool, ToolStatus, ToolTier, ToolRuntime
from tools.tool_registry import ToolRegistry
from tools.audio.sarvam_tts import SarvamTTS
from tools.analysis.sarvam_stt import SarvamSTT
from tools.text.groq_llm import GroqLLM
from tools.analysis.groq_whisper import GroqWhisper
from tools.text.openrouter_llm import OpenRouterLLM


class _FakeResponse:
    def __init__(self, json_data=None, content=b"fake-audio-bytes", status_code=200, text=""):
        self._json = json_data or {}
        self.content = content
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class TestSarvamTTS:
    def test_contract(self):
        assert issubclass(SarvamTTS, BaseTool)
        t = SarvamTTS()
        assert t.name == "sarvam_tts"
        assert t.capability == "tts"
        assert t.provider == "sarvam"
        assert t.tier == ToolTier.VOICE
        assert t.runtime == ToolRuntime.API

    def test_status(self, monkeypatch):
        t = SarvamTTS()
        monkeypatch.delenv("SARVAM_API_KEY", raising=False)
        assert t.get_status() == ToolStatus.UNAVAILABLE

        monkeypatch.setenv("SARVAM_API_KEY", "test-key")
        assert t.get_status() == ToolStatus.AVAILABLE

    def test_mock_execute(self, monkeypatch, tmp_path):
        monkeypatch.setenv("SARVAM_API_KEY", "test-key")
        t = SarvamTTS()

        import base64
        fake_b64 = base64.b64encode(b"RIFFdummydata").decode("utf-8")

        def mock_post(url, headers=None, json=None, timeout=None):
            assert "api.sarvam.ai" in url
            return _FakeResponse(json_data={"audios": [fake_b64]})

        import requests
        monkeypatch.setattr(requests, "post", mock_post)

        out_file = tmp_path / "test.wav"
        res = t.execute({
            "text": "নমস্কার",
            "language": "bn-IN",
            "output_path": str(out_file),
        })
        assert res.success is True
        assert out_file.exists()


class TestSarvamSTT:
    def test_contract(self):
        assert issubclass(SarvamSTT, BaseTool)
        t = SarvamSTT()
        assert t.name == "sarvam_stt"
        assert t.capability == "transcription"
        assert t.provider == "sarvam"
        assert t.tier == ToolTier.ANALYZE

    def test_mock_execute(self, monkeypatch, tmp_path):
        monkeypatch.setenv("SARVAM_API_KEY", "test-key")
        t = SarvamSTT()

        fake_audio = tmp_path / "audio.wav"
        fake_audio.write_bytes(b"RIFFfakeaudio")

        def mock_post(url, headers=None, files=None, data=None, timeout=None):
            return _FakeResponse(json_data={
                "transcript": "নমস্কার",
                "language_code": "bn-IN",
                "timestamps": {
                    "words": ["নমস্কার"],
                    "start_time_seconds": [0.0],
                    "end_time_seconds": [1.0],
                }
            })

        import requests
        monkeypatch.setattr(requests, "post", mock_post)

        res = t.execute({
            "audio_path": str(fake_audio),
            "language": "bn-IN",
            "output_dir": str(tmp_path),
        })
        assert res.success is True
        assert res.data["transcript"] == "নমস্কার"
        assert len(res.data["word_timestamps"]) == 1


class TestGroqTools:
    def test_groq_llm_contract(self):
        assert issubclass(GroqLLM, BaseTool)
        t = GroqLLM()
        assert t.name == "groq_llm"
        assert t.capability == "llm"
        assert t.provider == "groq"
        assert t.tier == ToolTier.GENERATE

    def test_groq_llm_mock(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        t = GroqLLM()

        def mock_post(url, headers=None, json=None, timeout=None):
            assert "api.groq.com" in url
            return _FakeResponse(json_data={
                "model": "openai/gpt-oss-120b",
                "choices": [{"message": {"content": "Hello world!"}, "finish_reason": "stop"}],
                "usage": {"total_tokens": 10},
            })

        import requests
        monkeypatch.setattr(requests, "post", mock_post)

        res = t.execute({"prompt": "Hello"})
        assert res.success is True
        assert res.data["content"] == "Hello world!"

    def test_groq_whisper_contract(self):
        assert issubclass(GroqWhisper, BaseTool)
        t = GroqWhisper()
        assert t.name == "groq_whisper"
        assert t.capability == "transcription"
        assert t.provider == "groq"
        assert t.tier == ToolTier.ANALYZE

    def test_groq_whisper_mock(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        t = GroqWhisper()

        fake_audio = tmp_path / "audio.wav"
        fake_audio.write_bytes(b"RIFFfakeaudio")

        def mock_post(url, headers=None, files=None, data=None, timeout=None):
            assert "api.groq.com" in url
            return _FakeResponse(json_data={
                "text": "Hello world",
                "language": "en",
                "duration": 1.5,
                "segments": [{"id": 0, "start": 0.0, "end": 1.5, "text": "Hello world"}],
                "words": [{"word": "Hello", "start": 0.0, "end": 0.7}, {"word": "world", "start": 0.7, "end": 1.5}],
            })

        import requests
        monkeypatch.setattr(requests, "post", mock_post)

        res = t.execute({"audio_path": str(fake_audio), "output_dir": str(tmp_path)})
        assert res.success is True
        assert res.data["transcript"] == "Hello world"
        assert len(res.data["word_timestamps"]) == 2


class TestOpenRouterLLM:
    def test_contract(self):
        assert issubclass(OpenRouterLLM, BaseTool)
        t = OpenRouterLLM()
        assert t.name == "openrouter_llm"
        assert t.capability == "llm"
        assert t.provider == "openrouter"
        assert t.tier == ToolTier.GENERATE

    def test_mock_execute(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        t = OpenRouterLLM()

        def mock_post(url, headers=None, json=None, timeout=None):
            assert "openrouter.ai" in url
            return _FakeResponse(json_data={
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "choices": [{"message": {"content": "Sample script"}, "finish_reason": "stop"}],
                "usage": {"total_tokens": 15},
            })

        import requests
        monkeypatch.setattr(requests, "post", mock_post)

        res = t.execute({"prompt": "Draft a script"})
        assert res.success is True
        assert res.data["content"] == "Sample script"


class TestLocalHardwareProbe:
    def test_probe_contract_and_execution(self):
        from tools.audio.local_hardware_probe import LocalHardwareProbe
        assert issubclass(LocalHardwareProbe, BaseTool)
        probe = LocalHardwareProbe()
        res = probe.execute({"target_language": "bn-IN"})
        assert res.success is True
        assert "hardware" in res.data
        assert "recommendation" in res.data
        assert res.data["recommendation"]["recommended_tool"] == "piper_tts"
        assert res.data["recommendation"]["model_name"] == "bn_BD-google-medium"


class TestPiperTTSOffline:
    def test_status_and_binary(self):
        from tools.audio.piper_tts import PiperTTS
        p = PiperTTS()
        assert p.get_status() == ToolStatus.AVAILABLE
        assert p._get_piper_binary() is not None


class TestIndicTTS:
    def test_contract_and_execution(self):
        from tools.audio.indic_tts import IndicTTS
        assert issubclass(IndicTTS, BaseTool)
        t = IndicTTS()
        assert t.name == "indic_tts"
        assert t.provider == "ai4bharat"
        assert t.capability == "tts"
        assert t.tier == ToolTier.VOICE
        res = t.execute({"text": "নমস্কার", "language": "bn-IN", "speaker": "female"})
        assert res.success is True
        assert res.data["locale"] == "West Bengal, India"


