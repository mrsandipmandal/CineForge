"""CI/CD integration tests for VoxCPM2 (VoxIndica worker), OpenRouter TTS, and Veo Video."""

import base64
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.audio.openrouter_tts import OpenRouterTTS
from tools.audio.voxcpm2 import VoxCPM2TTS, SESSION_FILE
from tools.video.veo_video import VeoVideo
from tools.base_tool import ToolStatus


class TestVoxCPM2Integration:
    """Test VoxCPM2 tool matches VoxIndica worker contract."""

    def test_metadata_and_capabilities(self):
        tool = VoxCPM2TTS()
        assert tool.name == "voxcpm2_tts"
        assert tool.capability == "tts"
        assert tool.provider == "voxcpm2"
        assert tool.supports["voice_cloning"] is True
        assert tool.supports["bengali"] is True
        assert tool.supports["shutdown"] is True

    def test_session_cache_lifecycle(self, tmp_path):
        tool = VoxCPM2TTS()
        test_session_file = tmp_path / ".test_session.json"
        with patch("tools.audio.voxcpm2.SESSION_FILE", test_session_file):
            VoxCPM2TTS.save_active_session("https://test.trycloudflare.com", "token123")
            assert test_session_file.is_file()
            data = VoxCPM2TTS.get_active_session()
            assert data["tunnel_url"] == "https://test.trycloudflare.com"
            assert data["bearer_token"] == "token123"

            VoxCPM2TTS.clear_active_session()
            assert not test_session_file.is_file()

    @patch("requests.post")
    def test_remote_synthesis_success(self, mock_post, tmp_path):
        dummy_wav = b"RIFF....WAVEfmt ...."
        dummy_b64 = base64.b64encode(dummy_wav).decode("ascii")

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "status": "success",
            "audio_base64": dummy_b64,
            "sample_rate": 48000,
            "duration_seconds": 3.5,
            "gpu": "Tesla T4",
            "vram_used": 5248,
            "generation_seconds": 1.2,
        }
        mock_post.return_value = mock_resp

        tool = VoxCPM2TTS()
        out_file = tmp_path / "cloned.wav"

        result = tool.execute({
            "text": "নমস্কার, এটি ভক্সইন্ডিকা ভয়েস ক্লোনিং টেস্ট।",
            "tunnel_url": "https://active-worker.trycloudflare.com",
            "bearer_token": "secret_hex_token",
            "language": "bn-IN",
            "output_path": str(out_file),
        })

        assert result.success is True
        assert out_file.is_file()
        assert out_file.read_bytes() == dummy_wav
        assert result.data["duration_seconds"] == 3.5
        assert result.data["gpu"] == "Tesla T4"

        # Verify POST request sent to correct endpoint with header
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://active-worker.trycloudflare.com/clone_voice"
        assert kwargs["headers"]["Authorization"] == "Bearer secret_hex_token"
        assert kwargs["json"]["language"] == "bn-IN"

    @patch("subprocess.run")
    @patch("requests.post")
    def test_shutdown_operation(self, mock_post, mock_run):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_post.return_value = mock_resp

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = 'mrsandipmandal/voxindica-voxcpm2-worker stopped'
        mock_run.return_value = mock_proc

        tool = VoxCPM2TTS()
        result = tool.execute({
            "operation": "shutdown",
            "tunnel_url": "https://active-worker.trycloudflare.com",
            "bearer_token": "secret_token",
        })

        assert result.success is True
        assert result.data["operation"] == "shutdown"
        assert result.data["details"]["http_shutdown"] is True
        mock_post.assert_called_with(
            "https://active-worker.trycloudflare.com/shutdown",
            headers={"Authorization": "Bearer secret_token"},
            timeout=10,
        )


class TestOpenRouterTTSIntegration:
    """Test OpenRouter TTS provider tool."""

    def test_metadata_and_cost(self):
        tool = OpenRouterTTS()
        assert tool.name == "openrouter_tts"
        assert tool.capability == "tts"
        assert tool.provider == "openrouter"

        # Free tier models cost 0.0
        assert tool.estimate_cost({"model_id": "heygen/heygen-voice-1-turbo:free", "text": "hello"}) == 0.0
        assert tool.estimate_cost({"model_id": "fish-audio/s2.1-pro-free:free", "text": "hello"}) == 0.0

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
    @patch("requests.post")
    def test_speech_generation_success(self, mock_post, tmp_path):
        dummy_audio = b"\xff\xfb\x90\x00..."  # mp3 header bytes
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.content = dummy_audio
        mock_post.return_value = mock_resp

        tool = OpenRouterTTS()
        out_file = tmp_path / "speech.mp3"

        result = tool.execute({
            "text": "Welcome to CineForge production.",
            "model_id": "heygen/heygen-voice-1-turbo:free",
            "voice": "alloy",
            "output_path": str(out_file),
        })

        assert result.success is True
        assert out_file.is_file()
        assert out_file.read_bytes() == dummy_audio
        assert result.data["model"] == "heygen/heygen-voice-1-turbo:free"

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://openrouter.ai/api/v1/audio/speech"
        assert kwargs["headers"]["Authorization"] == "Bearer test-key-123"
        assert kwargs["json"]["model"] == "heygen/heygen-voice-1-turbo:free"


class TestVeoVideoIntegration:
    """Test Google Veo video generation provider tool."""

    @patch.dict("os.environ", {"GEMINI_API_KEY": "AIzaSyTestKey123"}, clear=False)
    def test_gemini_api_key_status(self):
        tool = VeoVideo()
        assert tool.get_status() == ToolStatus.AVAILABLE

    def test_model_variant_resolution(self):
        tool = VeoVideo()
        assert tool.name == "veo_video"
        assert tool.capability == "video_generation"
        assert tool.provider == "veo"
        assert "veo3.1" in tool.input_schema["properties"]["model_variant"]["default"]
