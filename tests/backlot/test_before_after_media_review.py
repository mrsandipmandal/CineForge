"""Tests for Backlot media review, before/after render versions, and media security."""

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
        "title": "Before After Film",
        "pipeline_type": "cinematic",
    }), encoding="utf-8")
    return p


def test_media_scanner_discovers_original_and_enhanced_renders(projects_root: Path):
    """Verify renders directory with before and after outputs is scanned correctly."""
    proj = _make_project(projects_root, "before-after-test")
    renders_dir = proj / "renders"

    # Create dummy render files
    (renders_dir / "composed_v1.mp4").write_bytes(b"dummy_composed_content_v1")
    (renders_dir / "enhanced_v1.mp4").write_bytes(b"dummy_enhanced_content_v1")

    state = load_board_state(proj)
    renders = state["media"]["renders"]
    assert len(renders) == 2
    paths = [r["path"] for r in renders]
    assert any("composed_v1.mp4" in p for p in paths)
    assert any("enhanced_v1.mp4" in p for p in paths)


def test_security_media_path_containment(projects_root: Path):
    """Verify that state scanning does not leak outside project directory."""
    proj = _make_project(projects_root, "security-proj")
    outside_file = projects_root.parent / "secret.mp4"
    outside_file.write_bytes(b"top_secret")

    state = load_board_state(proj)
    for r in state["media"]["renders"]:
        assert not r["path"].startswith("..")
        assert "secret.mp4" not in r["path"]
