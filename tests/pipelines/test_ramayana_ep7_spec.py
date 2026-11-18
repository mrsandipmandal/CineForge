"""Specification and validation tests for Ramayana Episode 7 (Manthara's Midnight Plot)."""

import json
from pathlib import Path
import pytest

from scripts.generate_ramayana_ep7_content import generate_ep7_content

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = REPO_ROOT / "projects" / "ramayana-manthara-chakranta"
ARTIFACTS_DIR = PROJECT_DIR / "artifacts"


@pytest.fixture(scope="module", autouse=True)
def ensure_ep7_content():
    """Ensure artifacts are generated before running tests."""
    generate_ep7_content()


def test_ep7_script_structure():
    """Assert project layout, 7 scenes, and duration between 50.0s and 59.5s."""
    project_file = PROJECT_DIR / "project.json"
    assert project_file.exists(), f"Missing project.json at {project_file}"

    with open(project_file, "r", encoding="utf-8") as f:
        proj = json.load(f)

    assert proj.get("project_id") == "ramayana-manthara-chakranta"
    assert proj.get("pipeline_type") == "mythological_shorts"
    assert "মন্থরার কুটিল চক্রান্ত" in proj.get("title", "")

    script_file = ARTIFACTS_DIR / "script.json"
    assert script_file.exists(), f"Missing script.json at {script_file}"

    with open(script_file, "r", encoding="utf-8") as f:
        script = json.load(f)

    scenes = script.get("scenes", [])
    assert len(scenes) == 7, f"Expected 7 scenes, got {len(scenes)}"

    total_duration = script.get("total_duration") or script.get("total_duration_seconds")
    assert total_duration is not None
    assert 50.0 <= total_duration <= 59.5, f"Duration {total_duration} not in [50.0, 59.5]"
    assert total_duration <= 59.0, f"YouTube Shorts hard constraint violated: {total_duration} > 59.0"

    required_keys = {
        "id",
        "start_time",
        "end_time",
        "duration",
        "title",
        "narration_bn",
        "subtitle_bn",
        "visual_prompt",
        "mood",
    }
    for idx, scene in enumerate(scenes, start=1):
        missing = required_keys - set(scene.keys())
        assert not missing, f"Scene {idx} missing required keys: {missing}"
        assert scene["id"] == idx
        assert scene["duration"] > 0
        assert len(scene["visual_prompt"]) > 20
        assert len(scene["mood"]) > 0

    yt_file = ARTIFACTS_DIR / "youtube_metadata.txt"
    assert yt_file.exists(), f"Missing youtube_metadata.txt at {yt_file}"
    yt_text = yt_file.read_text(encoding="utf-8")
    assert "YOUTUBE VIRAL TITLES" in yt_text
    assert "DESCRIPTION & STORYTELLING" in yt_text
    assert "HASHTAGS & TAGS" in yt_text
    assert "PINNED COMMENT" in yt_text


def test_ep7_narration_content():
    """Assert key mythological figures appear in the Bengali narration."""
    script_file = ARTIFACTS_DIR / "script.json"
    with open(script_file, "r", encoding="utf-8") as f:
        script = json.load(f)

    scenes = script["scenes"]
    full_narration = " ".join(s["narration_bn"] for s in scenes)

    required_figures = ["মন্থরা", "কৈকেয়ী", "দশরথ", "শ্রীরাম"]
    for figure in required_figures:
        assert figure in full_narration, f"Required figure '{figure}' missing from narration"

    # Also assert Raja Ravi Varma style visual prompt authenticity
    full_prompts = " ".join(s["visual_prompt"] for s in scenes)
    assert "Raja Ravi Varma" in full_prompts
    assert "9:16" in full_prompts


def test_ep7_timestamps_alignment():
    """Assert continuous timestamp sequence (scene[i].start == scene[i-1].end)."""
    script_file = ARTIFACTS_DIR / "script.json"
    with open(script_file, "r", encoding="utf-8") as f:
        script = json.load(f)

    scenes = script["scenes"]
    assert len(scenes) == 7

    assert scenes[0]["start_time"] == 0.0

    for i in range(1, len(scenes)):
        prev_end = scenes[i - 1]["end_time"]
        curr_start = scenes[i]["start_time"]
        assert round(curr_start, 2) == round(prev_end, 2), (
            f"Gap or overlap detected between scene {scenes[i-1]['id']} "
            f"(end: {prev_end}) and scene {scenes[i]['id']} (start: {curr_start})"
        )

    for s in scenes:
        expected_end = round(s["start_time"] + s["duration"], 2)
        assert round(s["end_time"], 2) == expected_end, (
            f"Scene {s['id']} duration mismatch: start {s['start_time']} + "
            f"duration {s['duration']} != end {s['end_time']}"
        )

    # Verify timestamps.json alignment at 30 fps
    ts_file = ARTIFACTS_DIR / "timestamps.json"
    assert ts_file.exists(), f"Missing timestamps.json at {ts_file}"

    with open(ts_file, "r", encoding="utf-8") as f:
        ts_data = json.load(f)

    assert ts_data.get("fps") == 30
    assert len(ts_data.get("scenes", [])) == 7
    assert ts_data.get("total_duration") == script["total_duration"]

    ts_scenes = ts_data["scenes"]
    assert ts_scenes[0]["start_frame"] == 0
    for i in range(1, len(ts_scenes)):
        assert ts_scenes[i]["start_frame"] == ts_scenes[i - 1]["end_frame"], (
            f"Frame mismatch between scene {i} and {i+1}"
        )
    for s in ts_scenes:
        assert s["end_frame"] - s["start_frame"] == s["duration_frames"]
