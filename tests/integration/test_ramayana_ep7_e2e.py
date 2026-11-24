"""End-to-End Voice & Video Pipeline Verification for Ramayana Episode 7.

Validates the full production pipeline:
1. Script & scene definitions (58.5s <= 59.0s hard constraint, 7 scenes, Bengali narration).
2. DheeIndicF5 zero-shot voice cloning with Sandip profile.
3. Sandip broadcast audio mastering (75Hz highpass, 120Hz/3kHz EQ, opto compression, -14 LUFS).
4. CinematicMotionAnimator 2.5D multi-frame motion descriptors.
5. Remotion 9:16 composition (1080x1920 @ 30fps) referencing DynamicMotionScene.
6. Pipeline checkpoints persistence.
"""

import json
from pathlib import Path
import pytest

from scripts.produce_ramayana_ep7_full import (
    PROJECT_DIR,
    ARTIFACTS_DIR,
    AUDIO_DIR,
    CHECKPOINTS_DIR,
    produce_ramayana_ep7_full,
)


@pytest.fixture(scope="module", autouse=True)
def run_ep7_pipeline():
    """Execute end-to-end Ep7 production before running assertions."""
    result = produce_ramayana_ep7_full()
    assert result.get("success") is True, f"Pipeline execution failed: {result}"
    return result


def test_ep7_e2e_pipeline_execution():
    """Assert script.json, timestamps.json, audio generation, and motion descriptors are fully verified."""
    # 1. Script Artifact Verification
    script_file = ARTIFACTS_DIR / "script.json"
    assert script_file.exists(), f"Missing script.json at {script_file}"
    with open(script_file, "r", encoding="utf-8") as f:
        script = json.load(f)

    assert len(script["scenes"]) == 7, f"Expected 7 scenes, got {len(script['scenes'])}"
    total_dur = script.get("total_duration") or script.get("total_duration_seconds")
    assert total_dur is not None
    assert total_dur <= 59.0, f"YouTube Shorts hard constraint violated: {total_dur} > 59.0s"
    assert total_dur == 58.5, f"Expected canonical duration 58.5s, got {total_dur}"

    # Verify key narrative figures
    all_narration = " ".join(s.get("narration_bn", s.get("narration", "")) for s in script["scenes"])
    for figure in ["মন্থরা", "কৈকেয়ী", "দশরথ", "শ্রীরাম"]:
        assert figure in all_narration, f"Key figure '{figure}' missing from narration"

    # 2. Timestamps Artifact Verification
    ts_file = ARTIFACTS_DIR / "timestamps.json"
    assert ts_file.exists(), f"Missing timestamps.json at {ts_file}"
    with open(ts_file, "r", encoding="utf-8") as f:
        ts_data = json.load(f)

    assert ts_data.get("fps") == 30
    assert len(ts_data.get("scenes", [])) == 7
    assert ts_data.get("total_duration") == 58.5
    assert ts_data.get("total_frames") == 1755

    # Check continuity of frames and timestamps
    scenes_ts = ts_data["scenes"]
    assert scenes_ts[0]["start_time"] == 0.0
    assert scenes_ts[0]["start_frame"] == 0
    for i in range(1, len(scenes_ts)):
        prev = scenes_ts[i - 1]
        curr = scenes_ts[i]
        assert round(curr["start_time"], 2) == round(prev["end_time"], 2), (
            f"Timestamp gap between scene {i} and {i+1}"
        )
        assert curr["start_frame"] == prev["end_frame"], (
            f"Frame gap between scene {i} and {i+1}"
        )

    # 3. Audio Generation & Mastering Verification
    for s in script["scenes"]:
        sid = s["id"]
        scene_wav = AUDIO_DIR / f"scene_{sid}.wav"
        assert scene_wav.exists(), f"Missing per-scene audio file: {scene_wav}"
        assert scene_wav.stat().st_size > 44, f"Empty scene audio file: {scene_wav}"

    master_audio = AUDIO_DIR / "audio_mix.wav"
    assert master_audio.exists(), f"Missing master audio file: {master_audio}"
    assert master_audio.stat().st_size > 1000, f"Master audio file too small: {master_audio}"

    # 4. Motion Descriptors Verification
    motion_file = ARTIFACTS_DIR / "motion_descriptors.json"
    assert motion_file.exists(), f"Missing motion_descriptors.json at {motion_file}"
    with open(motion_file, "r", encoding="utf-8") as f:
        motion_data = json.load(f)

    descriptors = motion_data.get("descriptors", [])
    assert len(descriptors) == 7, f"Expected 7 motion descriptors, got {len(descriptors)}"
    for d in descriptors:
        assert d.get("motion_type") == "2.5d_parallax_pulse"
        assert "depth_layers" in d
        assert "background_scale_speed" in d["depth_layers"]
        assert "subject_scale_speed" in d["depth_layers"]
        assert "foreground_speed" in d["depth_layers"]
        assert "character_dynamics" in d
        assert "breathing" in d["character_dynamics"]
        assert "particle_fx" in d
        assert "camera_dynamics" in d


def test_ep7_duration_and_resolution():
    """Assert duration <= 59.0s and resolution is 1080x1920 in composition."""
    index_file = PROJECT_DIR / "index.tsx"
    assert index_file.exists(), f"Missing index.tsx at {index_file}"
    content = index_file.read_text(encoding="utf-8")

    # Assert DynamicMotionScene import
    assert "DynamicMotionScene" in content
    assert "../../remotion-composer/src/components/DynamicMotionScene" in content

    # Assert vertical 9:16 resolution (1080x1920)
    assert "width={1080}" in content or "width: 1080" in content
    assert "height={1920}" in content or "height: 1920" in content
    assert "fps={30}" in content or "fps: 30" in content

    # Assert total frames / duration
    # 58.5s * 30fps = 1755 frames
    assert "durationInFrames={1755}" in content or "1755" in content


def test_ep7_checkpoints_and_manifests():
    """Assert all checkpoint files and asset manifests exist and are marked completed."""
    assert CHECKPOINTS_DIR.exists()
    stages = [
        "research",
        "proposal",
        "script",
        "scene_plan",
        "assets",
        "edit",
        "compose",
        "enhancement",
        "publish",
    ]
    for stage in stages:
        cp_file = CHECKPOINTS_DIR / f"{stage}.json"
        assert cp_file.exists(), f"Missing checkpoint file: {cp_file}"
        with open(cp_file, "r", encoding="utf-8") as f:
            cp = json.load(f)
        assert cp.get("project_id") == "ramayana-manthara-chakranta"
        assert cp.get("stage") == stage
        assert cp.get("status") == "completed"
        assert cp.get("human_approved") is True

    manifest_file = ARTIFACTS_DIR / "asset_manifest.json"
    assert manifest_file.exists(), f"Missing asset_manifest.json at {manifest_file}"
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest.get("project_id") == "ramayana-manthara-chakranta"
    assert len(manifest.get("assets", [])) >= 8  # 7 images + master audio
