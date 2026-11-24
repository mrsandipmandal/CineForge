"""Tests for TimingReconciler."""
from tools.analysis.timing_reconciler import TimingReconciler


def _plan(scenes):
    return {"version": "1.0", "scenes": scenes}


def _manifest(assets):
    return {"version": "1.0", "assets": assets}


def test_adjusts_timestamps_from_actual_duration():
    plan = _plan([
        {"id": "s1", "start_seconds": 0, "end_seconds": 5},
        {"id": "s2", "start_seconds": 5, "end_seconds": 10},
    ])
    manifest = _manifest([
        {"id": "a1", "type": "narration", "scene_id": "s1",
         "path": "s1.mp3", "source_tool": "tts", "duration_seconds": 7.0},
        {"id": "a2", "type": "narration", "scene_id": "s2",
         "path": "s2.mp3", "source_tool": "tts", "duration_seconds": 4.5},
    ])
    result = TimingReconciler().execute({"scene_plan": plan, "asset_manifest": manifest})
    assert result.success
    cuts = result.data["adjusted_cuts"]
    assert cuts[0]["in_seconds"] == 0.0
    assert cuts[0]["out_seconds"] == 7.0  # actual not planned
    assert cuts[1]["in_seconds"] == 7.0
    assert cuts[1]["out_seconds"] == 11.5


def test_falls_back_to_planned_when_no_asset():
    plan = _plan([{"id": "s1", "start_seconds": 0, "end_seconds": 6}])
    manifest = _manifest([])
    result = TimingReconciler().execute({"scene_plan": plan, "asset_manifest": manifest})
    assert result.success
    assert result.data["adjusted_cuts"][0]["out_seconds"] == 6.0


def test_total_duration_correct():
    plan = _plan([
        {"id": "s1", "start_seconds": 0, "end_seconds": 5},
        {"id": "s2", "start_seconds": 5, "end_seconds": 8},
    ])
    manifest = _manifest([
        {"id": "a1", "type": "narration", "scene_id": "s1",
         "path": "x.mp3", "source_tool": "tts", "duration_seconds": 5.0},
        {"id": "a2", "type": "narration", "scene_id": "s2",
         "path": "y.mp3", "source_tool": "tts", "duration_seconds": 3.0},
    ])
    result = TimingReconciler().execute({"scene_plan": plan, "asset_manifest": manifest})
    assert result.data["total_duration_seconds"] == 8.0


def test_drift_warnings_generated():
    plan = _plan([{"id": "s1", "start_seconds": 0, "end_seconds": 5}])
    manifest = _manifest([
        {"id": "a1", "type": "narration", "scene_id": "s1",
         "path": "x.mp3", "source_tool": "tts", "duration_seconds": 7.5},
    ])
    result = TimingReconciler().execute({"scene_plan": plan, "asset_manifest": manifest})
    assert any("drift" in w for w in result.data["warnings"])


def test_empty_scenes_returns_error():
    result = TimingReconciler().execute(
        {"scene_plan": {"scenes": []}, "asset_manifest": {"assets": []}}
    )
    assert not result.success


def test_gap_seconds_applied():
    plan = _plan([
        {"id": "s1", "start_seconds": 0, "end_seconds": 5},
        {"id": "s2", "start_seconds": 5, "end_seconds": 10},
    ])
    manifest = _manifest([
        {"id": "a1", "type": "narration", "scene_id": "s1",
         "path": "s1.mp3", "source_tool": "tts", "duration_seconds": 5.0},
        {"id": "a2", "type": "narration", "scene_id": "s2",
         "path": "s2.mp3", "source_tool": "tts", "duration_seconds": 5.0},
    ])
    result = TimingReconciler().execute(
        {"scene_plan": plan, "asset_manifest": manifest, "gap_seconds": 0.5}
    )
    cuts = result.data["adjusted_cuts"]
    assert cuts[1]["in_seconds"] == 5.5  # 5.0 + 0.5 gap
