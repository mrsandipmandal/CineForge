"""Tests for Upscale tool video integrity, safety, and audio preservation."""

import subprocess
from pathlib import Path
import pytest
from tools.enhancement.upscale import Upscale


@pytest.fixture
def sample_video(tmp_path: Path) -> Path:
    """Generate a clean synthetic 1-second video with an audio tone for testing."""
    video_path = tmp_path / "test_input.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        str(video_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return video_path


def test_upscale_prevents_source_overwrite(sample_video: Path):
    """Upscale must refuse to overwrite the original input file."""
    tool = Upscale()
    res = tool.execute({
        "input_path": str(sample_video),
        "output_path": str(sample_video),
    })
    assert res.success is False
    assert "cannot overwrite" in str(res.error).lower()


def test_upscale_video_with_audio_preservation(sample_video: Path, tmp_path: Path):
    """Upscaling video must preserve duration, audio stream, and dimensions."""
    tool = Upscale()
    out_path = tmp_path / "upscaled_video.mp4"
    res = tool.execute({
        "input_path": str(sample_video),
        "output_path": str(out_path),
        "scale": 2,
        "model": "ffmpeg_lanczos",
    })
    assert res.success is True, res.error
    assert out_path.exists()
    assert out_path.stat().st_size > 0

    # Probe output to verify 2x dimensions and audio stream
    probe = tool._probe_video(out_path)
    assert probe["width"] == 640
    assert probe["height"] == 480
    assert probe["has_audio"] is True
    assert sample_video.exists()  # Source preserved


def test_upscale_missing_input():
    """Attempting to upscale nonexistent file fails gracefully."""
    tool = Upscale()
    res = tool.execute({"input_path": "/nonexistent/video.mp4"})
    assert res.success is False
    assert "not found" in str(res.error).lower()
