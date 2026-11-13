"""Tests for the pre-export enhancement stage across pipelines and checkpoints."""

from pathlib import Path
import pytest
import yaml
import jsonschema

from lib.checkpoint import (
    validate_checkpoint,
    get_pipeline_stages,
    CANONICAL_STAGE_ARTIFACTS,
    ALL_KNOWN_STAGES,
)
from lib.pipeline_loader import load_pipeline_readonly


def test_enhancement_stage_in_known_stages():
    """Verify enhancement is recognized across stage collections."""
    assert "enhancement" in ALL_KNOWN_STAGES
    assert CANONICAL_STAGE_ARTIFACTS["enhancement"] == "enhancement_report"


@pytest.mark.parametrize("pipeline_name", [
    "cinematic",
    "animation",
    "talking-head",
    "animated-explainer",
    "avatar-spokesperson",
    "character-animation",
])
def test_pipeline_manifest_contains_enhancement_stage(pipeline_name: str):
    """Verify applicable pipeline manifests declare enhancement after compose and before publish."""
    stages = get_pipeline_stages(pipeline_name)
    assert "enhancement" in stages
    assert "compose" in stages
    assert "publish" in stages

    compose_idx = stages.index("compose")
    enh_idx = stages.index("enhancement")
    pub_idx = stages.index("publish")

    assert enh_idx == compose_idx + 1
    assert pub_idx == enh_idx + 1


def test_unmodified_pipelines_remain_untouched():
    """Pipelines that do not use enhancement (e.g. framework-smoke) remain valid without it."""
    stages = get_pipeline_stages("framework-smoke")
    assert "enhancement" not in stages
    assert stages == ["research", "script"]


def test_checkpoint_validation_enhancement_stage():
    """Verify checkpoint structure validation for enhancement stage."""
    cp_in_progress = {
        "version": "1.0",
        "project_id": "test-project",
        "pipeline_type": "cinematic",
        "stage": "enhancement",
        "status": "in_progress",
        "timestamp": "2026-11-13T12:00:00Z",
        "artifacts": {},
    }
    validate_checkpoint(cp_in_progress)

    cp_completed = {
        "version": "1.0",
        "project_id": "test-project",
        "pipeline_type": "cinematic",
        "stage": "enhancement",
        "status": "completed",
        "timestamp": "2026-11-13T12:00:00Z",
        "artifacts": {
            "enhancement_report": {
                "version": "1.0",
                "input_media": {
                    "path": "renders/render.mp4",
                    "duration_seconds": 10.0,
                    "resolution": {"width": 1920, "height": 1080},
                    "fps": 30.0,
                },
                "output_media": {
                    "path": "renders/final_enhanced.mp4",
                },
                "enhancers": {
                    "video_quality": {
                        "enabled": True,
                        "profile": "cinematic",
                    }
                },
                "status": "completed",
            }
        },
    }
    validate_checkpoint(cp_completed)
