"""Unit and contract tests for VideoQualityEnhancer."""

import subprocess
from pathlib import Path
import pytest

from schemas.artifacts import validate_artifact
from tools.enhancement.video_quality_enhancer import VideoQualityEnhancer


@pytest.fixture
def sample_render_video(tmp_path: Path) -> Path:
    """Generate a clean synthetic 1-second 640x360 video with audio for testing."""
    video_path = tmp_path / "composed_render.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=1:size=640x360:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        str(video_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return video_path


def test_vqe_tool_contract():
    """Verify tool metadata and capabilities."""
    tool = VideoQualityEnhancer()
    assert tool.capability == "enhancement"
    assert tool.provider == "cineforge"
    assert "video_quality_enhancement" in tool.capabilities
    assert "enhancement_reporting" in tool.capabilities


def test_vqe_prevents_source_overwrite(sample_render_video: Path):
    """VQE must refuse to write to the exact same path as input."""
    tool = VideoQualityEnhancer()
    res = tool.execute({
        "input_path": str(sample_render_video),
        "output_path": str(sample_render_video),
    })
    assert res.success is False
    assert "cannot overwrite" in str(res.error).lower()


def test_vqe_execute_balanced_profile(sample_render_video: Path, tmp_path: Path):
    """Verify balanced profile enhancement and schema-valid report output."""
    tool = VideoQualityEnhancer()
    out_path = tmp_path / "enhanced_render.mp4"

    res = tool.execute({
        "input_path": str(sample_render_video),
        "output_path": str(out_path),
        "profile": "balanced",
        "strength": "medium",
    })
    assert res.success is True, res.error
    assert out_path.exists()
    assert out_path.stat().st_size > 0
    assert sample_render_video.exists()  # Source preserved

    data = res.data
    assert "report" in data
    report = data["report"]
    assert report["version"] == "1.0"
    assert report["status"] == "completed"
    assert report["input_media"]["has_audio"] is True
    assert report["output_media"]["has_audio"] is True
    assert report["qa_results"]["output_decodable"] is True
    assert report["qa_results"]["original_preserved"] is True

    # Validate against actual JSON schema
    validate_artifact("enhancement_report", report)


def test_vqe_execute_disabled_mode(sample_render_video: Path, tmp_path: Path):
    """Verify that disabled profile bypasses enhancement and creates valid report."""
    tool = VideoQualityEnhancer()
    out_path = tmp_path / "disabled_render.mp4"

    res = tool.execute({
        "input_path": str(sample_render_video),
        "output_path": str(out_path),
        "profile": "disabled",
    })
    assert res.success is True, res.error
    assert out_path.exists()

    report = res.data["report"]
    assert report["status"] == "skipped"
    assert report["enhancers"]["video_quality"]["selection_mode"] == "disabled"
    validate_artifact("enhancement_report", report)


def test_vqe_ai_decide_profile(sample_render_video: Path, tmp_path: Path):
    """Verify 'auto' profile triggers reasoned AI decision."""
    tool = VideoQualityEnhancer()
    out_path = tmp_path / "auto_render.mp4"

    res = tool.execute({
        "input_path": str(sample_render_video),
        "output_path": str(out_path),
        "profile": "auto",
    })
    assert res.success is True, res.error
    report = res.data["report"]
    assert report["enhancers"]["video_quality"]["selection_mode"] == "ai_decided"
    assert len(report["enhancers"]["video_quality"]["decision_reason"]) > 0
    validate_artifact("enhancement_report", report)
