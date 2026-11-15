"""Tests for verify_scene_pacing utilities."""
import pytest
from lib.verify_scene_pacing import step_duration, trace, assert_alignment, Landmark


def test_step_duration_cmd():
    step = {"kind": "cmd", "text": "npm install", "typeSpeed": 0.035, "holdSeconds": 0.3}
    d = step_duration(step)
    assert d > 0.3  # must include hold


def test_step_duration_out():
    step = {"kind": "out", "text": "Done", "holdSeconds": 0.15}
    d = step_duration(step)
    assert d >= 0.15


def test_step_duration_pause():
    step = {"kind": "pause", "seconds": 2.5}
    assert step_duration(step) == 2.5


def test_step_duration_pill():
    step = {"kind": "pill", "text": "Installing..."}
    assert step_duration(step) == 0.0


def test_step_duration_unknown_kind():
    with pytest.raises(ValueError):
        step_duration({"kind": "unknown", "text": "x"})


def test_trace_returns_landmarks():
    steps = [
        {"kind": "cmd", "text": "echo hello"},
        {"kind": "out", "text": "hello"},
        {"kind": "pause", "seconds": 1.0},
    ]
    landmarks = trace(steps, scene_start=10.0, quiet=True)
    assert len(landmarks) == 2  # cmd + out; pause has no visible event
    assert all(isinstance(lm, Landmark) for lm in landmarks)
    assert landmarks[0].video_time >= 10.0


def test_assert_alignment_pass():
    steps = [
        {"kind": "cmd", "text": "git clone repo"},
        {"kind": "out", "text": "Cloning..."},
        {"kind": "pause", "seconds": 2.0},
    ]
    # Compute total step duration so scene_end is tight (no underfill error)
    total = sum(step_duration(s) for s in steps)
    scene_start = 50.0
    scene_end = scene_start + total + 0.1  # small margin to avoid underfill
    # narration cue near the cmd step
    assert_alignment(
        steps,
        scene_start=scene_start,
        scene_end=scene_end,
        narration_cues=[(50.1, "Clone the repo")],
        tolerance=1.5,
    )


def test_assert_alignment_fail_on_bad_cue():
    steps = [
        {"kind": "cmd", "text": "ls"},
        {"kind": "pause", "seconds": 5.0},
    ]
    with pytest.raises(AssertionError) as exc:
        assert_alignment(
            steps,
            scene_start=0.0,
            scene_end=10.0,
            narration_cues=[(8.0, "Way off cue")],
            tolerance=0.5,
        )
    assert "no visual within" in str(exc.value)


def test_overflow_detection():
    # Steps that overflow the scene duration
    steps = [{"kind": "pause", "seconds": 20.0}]
    with pytest.raises(AssertionError) as exc:
        assert_alignment(steps, scene_start=0.0, scene_end=5.0, narration_cues=[], tolerance=1.0)
    assert "overflow" in str(exc.value)
