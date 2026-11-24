"""Unit tests for Sandip broadcast audio mastering chain."""

import math
import struct
import wave
from pathlib import Path
from unittest.mock import patch
import pytest

from tools.base_tool import ExecutionMode, ToolRuntime, ToolStability, ToolTier
from tools.tool_registry import ToolRegistry


def _create_test_wav(path: Path, duration_seconds: float = 1.0, sample_rate: int = 24000) -> Path:
    """Generate a valid test sine-wave audio WAV file."""
    num_samples = int(sample_rate * duration_seconds)
    freq = 440.0
    amplitude = 16000

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate
            value = int(amplitude * math.sin(2.0 * math.pi * freq * t))
            frames.extend(struct.pack("<h", value))
        wav.writeframes(frames)
    return path


def test_sandip_audio_master_registration():
    from tools.audio.sandip_audio_master import SandipAudioMaster

    tool = SandipAudioMaster()
    assert tool.name == "sandip_audio_master"
    assert tool.tier == ToolTier.ENHANCE
    assert tool.capability == "audio_enhance"
    assert tool.provider == "ffmpeg"
    assert tool.stability == ToolStability.PRODUCTION
    assert tool.execution_mode == ExecutionMode.SYNC
    assert tool.runtime == ToolRuntime.LOCAL


def test_sandip_audio_master_registry_discovery():
    from tools.audio.sandip_audio_master import SandipAudioMaster

    registry = ToolRegistry()
    registry.discover()
    assert "sandip_audio_master" in registry._tools
    assert isinstance(registry._tools["sandip_audio_master"], SandipAudioMaster)


def test_sandip_audio_master_processing(tmp_path: Path):
    from tools.audio.sandip_audio_master import SandipAudioMaster

    raw_wav = _create_test_wav(tmp_path / "raw.wav", duration_seconds=1.5)
    output_wav = tmp_path / "mastered.wav"

    tool = SandipAudioMaster()
    out = tool.master_narration(str(raw_wav), str(output_wav))

    assert out == str(output_wav)
    assert output_wav.exists()
    assert output_wav.stat().st_size > 44

    # Verify that the mastered output is a readable audio file
    with wave.open(str(output_wav), "rb") as w:
        assert w.getnchannels() >= 1
        assert w.getframerate() > 0
        assert w.getnframes() > 0


def test_sandip_audio_master_execute(tmp_path: Path):
    from tools.audio.sandip_audio_master import SandipAudioMaster

    raw_wav = _create_test_wav(tmp_path / "raw.wav", duration_seconds=1.0)
    output_wav = tmp_path / "custom_mastered.wav"

    tool = SandipAudioMaster()

    # Successful execution with explicit output path
    res = tool.execute({"raw_audio_path": str(raw_wav), "output_path": str(output_wav)})
    assert res.success is True
    assert res.data["output_path"] == str(output_wav)
    assert res.data["lufs_target"] == -14.0
    assert output_wav.exists()

    # Successful execution with default output path
    res_default = tool.execute({"raw_audio_path": str(raw_wav)})
    assert res_default.success is True
    assert "output_path" in res_default.data
    assert Path(res_default.data["output_path"]).exists()
    assert res_default.data["lufs_target"] == -14.0

    # Error handling when file does not exist
    res_err = tool.execute({"raw_audio_path": str(tmp_path / "non_existent.wav")})
    assert res_err.success is False
    assert res_err.error is not None


def test_sandip_audio_master_fallback_when_ffmpeg_fails(tmp_path: Path):
    from tools.audio.sandip_audio_master import SandipAudioMaster

    raw_wav = _create_test_wav(tmp_path / "raw.wav", duration_seconds=0.5)
    output_wav = tmp_path / "fallback_mastered.wav"

    tool = SandipAudioMaster()

    # Simulate ffmpeg failure during run_command
    with patch.object(tool, "run_command", side_effect=RuntimeError("FFmpeg execution error")):
        out = tool.master_narration(str(raw_wav), str(output_wav))
        assert out == str(output_wav)
        assert output_wav.exists()
        # Fallback copy: contents must match original
        assert output_wav.read_bytes() == raw_wav.read_bytes()

    # Also test via execute()
    output_wav2 = tmp_path / "fallback_execute.wav"
    with patch.object(tool, "run_command", side_effect=RuntimeError("FFmpeg execution error")):
        res = tool.execute({"raw_audio_path": str(raw_wav), "output_path": str(output_wav2)})
        assert res.success is True
        assert res.data["output_path"] == str(output_wav2)
        assert res.data.get("fallback_used") is True
        assert output_wav2.exists()
        assert output_wav2.read_bytes() == raw_wav.read_bytes()
