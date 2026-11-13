"""Unit and contract tests for AIHumanEnhancer."""

import subprocess
from pathlib import Path
from unittest.mock import patch
import pytest

from schemas.artifacts import validate_artifact
from tools.base_tool import ToolResult
from tools.enhancement.ai_human_enhancer import AIHumanEnhancer


@pytest.fixture
def sample_video_no_face(tmp_path: Path) -> Path:
    """Generate a clean synthetic 1-second video without any faces."""
    video_path = tmp_path / "landscape_render.mp4"
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


def test_ai_human_enhancer_contract():
    """Verify tool metadata and capabilities."""
    tool = AIHumanEnhancer()
    assert tool.capability == "enhancement"
    assert tool.provider == "cineforge"
    assert "human_applicability_analysis" in tool.capabilities
    assert "identity_preservation" in tool.capabilities


def test_ai_human_enhancer_prevents_source_overwrite(sample_video_no_face: Path):
    """Refuse to overwrite source file."""
    tool = AIHumanEnhancer()
    res = tool.execute({
        "input_path": str(sample_video_no_face),
        "output_path": str(sample_video_no_face),
    })
    assert res.success is False
    assert "cannot overwrite" in str(res.error).lower()


def test_ai_human_enhancer_no_face_detected_marks_not_applicable(sample_video_no_face: Path, tmp_path: Path):
    """When no faces are present, mark not_applicable and bypass processing."""
    tool = AIHumanEnhancer()
    out_path = tmp_path / "out_no_face.mp4"

    res = tool.execute({
        "input_path": str(sample_video_no_face),
        "output_path": str(out_path),
        "profile": "natural",
    })
    assert res.success is True, res.error
    assert out_path.exists()
    assert sample_video_no_face.exists()

    report = res.data["report"]
    assert report["status"] == "skipped"
    human_enh = report["enhancers"]["ai_human"]
    assert human_enh["selection_mode"] == "not_applicable"
    assert human_enh["human_subjects_detected"] is False
    assert human_enh["face_count"] == 0

    # Must validate against enhancement_report schema
    validate_artifact("enhancement_report", report)


def test_ai_human_enhancer_face_detected_enhances(sample_video_no_face: Path, tmp_path: Path):
    """When a face is detected, apply enhancement and record face operations."""
    tool = AIHumanEnhancer()
    out_path = tmp_path / "out_with_face.mp4"

    # Mock FaceTracker to simulate face detection on the test video
    mock_tracker_res = ToolResult(
        success=True,
        data={
            "faces": [{"frame_index": 1, "bbox": {"x": 100, "y": 100, "width": 80, "height": 80}}],
            "frame_count": 30,
        },
        duration_seconds=0.1,
    )

    with patch("tools.analysis.face_tracker.FaceTracker.execute", return_value=mock_tracker_res):
        res = tool.execute({
            "input_path": str(sample_video_no_face),
            "output_path": str(out_path),
            "profile": "natural",
            "strength": "medium",
        })
        assert res.success is True, res.error
        assert out_path.exists()

        report = res.data["report"]
        assert report["status"] == "completed"
        human_enh = report["enhancers"]["ai_human"]
        assert human_enh["human_subjects_detected"] is True
        assert human_enh["face_count"] == 1
        assert human_enh["identity_preserved"] is True
        assert len(human_enh["operations"]) > 0

        validate_artifact("enhancement_report", report)


def test_ai_human_enhancer_disabled_mode(sample_video_no_face: Path, tmp_path: Path):
    """When disabled, bypass and generate skipped report."""
    tool = AIHumanEnhancer()
    out_path = tmp_path / "out_disabled.mp4"

    res = tool.execute({
        "input_path": str(sample_video_no_face),
        "output_path": str(out_path),
        "profile": "disabled",
    })
    assert res.success is True, res.error
    report = res.data["report"]
    assert report["status"] == "skipped"
    assert report["enhancers"]["ai_human"]["selection_mode"] == "disabled"
    validate_artifact("enhancement_report", report)
