"""Tests for TimingReconciler."""
from tools.analysis.timing_reconciler import TimingReconciler


def _make_plan(scenes):
    return {"version": "1.0", "scenes": scenes}


def _make_manifest(assets):
    return {"version": "1.0", "assets": assets}


def test_adjusts_timestamps_from_actual_duration():
    plan = _make_plan([
        {"id": "s1", "start_seconds": 0, "end_seconds": 5},
        {"id": "s2", "start_seconds": 5, "end_seconds": 10},
    ])
    manifest = _make_manifest([
        {"id": "a1", "type": "narration", "scene_id": "s1",
         "path": "s1.mp3", "source_tool": "tts", "duration_seconds": 7.0},
        {"id": "a2", "type": "narration", "scene_id": "s2",
         "path": "s2.mp3", "source_tool": "tts", "duration_seconds": 4.5},
    ])
    t = TimingReconciler()
    result = t.execute({"scene_plan": plan, "asset_manifest": manifest})
    assert result.success
    cuts = result.data["adjusted_cuts"]
    assert cuts[0]["in_seconds"] == 0.0
    assert cuts[0]["out_seconds"] == 7.0  # actual, not planned 5.0
    assert cuts[1]["in_seconds"] == 7.0
    assert cuts[1]["out_seconds"] == 11.5


def test_falls_back_to_planned_duration_when_no_asset():
    plan = _make_plan([{"id": "s1", "start_seconds": 0, "end_seconds": 6}])
    manifest = _make_manifest([])
    t = TimingReconciler()
    result = t.execute({"scene_plan": plan, "asset_manifest": manifest})
    assert result.success
    cuts = result.data["adjusted_cuts"]
    assert cuts[0]["out_seconds"] == 6.0


def test_total_duration_sums_correctly():
    plan = _make_plan([
        {"id": "s1", "start_seconds": 0, "end_seconds": 5},
        {"id": "s2", "start_seconds": 5, "end_seconds": 8},
    ])
    manifest = _make_manifest([
        {"id": "a1", "type": "narration", "scene_id": "s1",
         "path": "x.mp3", "source_tool": "tts", "duration_seconds": 5.0},
        {"id": "a2", "type": "narration", "scene_id": "s2",
         "path": "y.mp3", "source_tool": "tts", "duration_seconds": 3.0},
    ])
    result = TimingReconciler().execute({"scene_plan": plan, "asset_manifest": manifest})
    assert result.data["total_duration_seconds"] == 8.0


def test_drift_warnings_generated():
    plan = _make_plan([{"id": "s1", "start_seconds": 0, "end_seconds": 5}])
    manifest = _make_manifest([
        {"id": "a1", "type": "narration", "scene_id": "s1",
         "path": "x.mp3", "source_tool": "tts", "duration_seconds": 7.5},
    ])
    result = TimingReconciler().execute({"scene_plan": plan, "asset_manifest": manifest})
    assert any("drift" in w for w in result.data["warnings"])


def test_empty_scene_plan_returns_error():
    plan = _make_plan([])
    manifest = _make_manifest([])
    result = TimingReconciler().execute({"scene_plan": plan, "asset_manifest": manifest})
    assert not result.success
    assert "no scenes" in result.error.lower()


def test_gap_seconds_adds_spacing():
    plan = _make_plan([
        {"id": "s1", "start_seconds": 0, "end_seconds": 5},
        {"id": "s2", "start_seconds": 5, "end_seconds": 10},
    ])
    manifest = _make_manifest([
        {"id": "a1", "type": "narration", "scene_id": "s1",
         "path": "s1.mp3", "source_tool": "tts", "duration_seconds": 5.0},
        {"id": "a2", "type": "narration", "scene_id": "s2",
         "path": "s2.mp3", "source_tool": "tts", "duration_seconds": 5.0},
    ])
    result = TimingReconciler().execute({
        "scene_plan": plan, "asset_manifest": manifest, "gap_seconds": 1.0
    })
    cuts = result.data["adjusted_cuts"]
    # s1: 0-5, then gap 1s, s2: 6-11
    assert cuts[1]["in_seconds"] == 6.0
    assert result.data["total_duration_seconds"] == 11.0
