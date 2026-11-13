"""Tests for Backlot BoardState integration with enhancement artifacts and reports."""

import json
from pathlib import Path
import pytest

from backlot import state as state_mod
from backlot.state import load_board_state


@pytest.fixture
def projects_root(tmp_path, monkeypatch):
    root = tmp_path / "projects"
    root.mkdir()
    monkeypatch.setattr(state_mod, "PROJECTS_DIR", root)
    return root


def _make_project(root: Path, pid: str) -> Path:
    p = root / pid
    (p / "artifacts").mkdir(parents=True)
    (p / "renders").mkdir()
    (p / "project.json").write_text(json.dumps({
        "title": "Mars Film",
        "pipeline_type": "cinematic",
    }), encoding="utf-8")
    return p


def test_board_state_collects_enhancement_report(projects_root: Path):
    """Verify load_board_state collects enhancement_report from artifacts directory."""
    proj = _make_project(projects_root, "mars-mission")
    enh_report = {
        "version": "1.0",
        "input_media": {
            "path": "renders/composed.mp4",
            "duration_seconds": 12.0,
            "resolution": {"width": 1920, "height": 1080},
            "fps": 30.0,
        },
        "output_media": {
            "path": "renders/enhanced.mp4",
        },
        "enhancers": {
            "video_quality": {
                "enabled": True,
                "profile": "cinematic",
                "selection_mode": "user_selected",
            },
            "ai_human": {
                "enabled": False,
                "selection_mode": "not_applicable",
            }
        },
        "status": "completed",
    }
    (proj / "artifacts" / "enhancement_report.json").write_text(json.dumps(enh_report), encoding="utf-8")

    board_state = load_board_state(proj)
    assert "enhancement_report" in board_state["artifacts"]
    loaded = board_state["artifacts"]["enhancement_report"]
    assert loaded["version"] == "1.0"
    assert loaded["enhancers"]["video_quality"]["profile"] == "cinematic"
    assert loaded["enhancers"]["ai_human"]["selection_mode"] == "not_applicable"


def test_board_state_displays_enhancement_stage_in_rail(projects_root: Path):
    """Verify cinematic pipeline stage rail includes enhancement stage."""
    proj = _make_project(projects_root, "cinematic-test")
    board_state = load_board_state(proj)
    stage_names = [st["name"] for st in board_state["stages"]]
    assert "enhancement" in stage_names
    assert stage_names.index("enhancement") == stage_names.index("compose") + 1
    assert stage_names.index("publish") == stage_names.index("enhancement") + 1
