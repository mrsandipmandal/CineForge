"""Tests for NarrationDriftTracker."""
import pytest
from lib.narration_drift_tracker import NarrationDriftTracker


def test_no_drift_ok():
    tracker = NarrationDriftTracker(total_budget_seconds=60.0)
    result = tracker.record(5.0, 5.0)
    assert result["cumulative_drift_seconds"] == 0.0
    assert not result["exceeds_threshold"]
    assert result["recommendation"] == "ok"


def test_small_drift_within_tolerance():
    tracker = NarrationDriftTracker(total_budget_seconds=60.0)
    # 0.1s drift on 60s budget = 0.17% << 5% threshold
    result = tracker.record(5.0, 5.1)
    assert not result["exceeds_threshold"]


def test_cumulative_drift_exceeds_threshold():
    """10 segments each 7% long should exceed threshold by segment 7+."""
    tracker = NarrationDriftTracker(total_budget_seconds=60.0)
    exceeded = False
    for i in range(10):
        result = tracker.record(5.0, 5.35)  # 7% over per segment
        if result["exceeds_threshold"]:
            exceeded = True
    assert exceeded, "Cumulative drift should have exceeded threshold"


def test_recommendation_message_on_exceed():
    tracker = NarrationDriftTracker(total_budget_seconds=10.0)
    # Large single drift
    result = tracker.record(5.0, 8.0)  # 3s drift on 10s budget = 30%
    assert result["exceeds_threshold"]
    assert "re-plan" in result["recommendation"].lower()


def test_reset_clears_state():
    tracker = NarrationDriftTracker(total_budget_seconds=60.0)
    tracker.record(5.0, 6.0)
    tracker.reset()
    assert tracker.current_drift == 0.0
    assert tracker.segments_recorded == 0


def test_zero_budget_raises():
    with pytest.raises(ValueError):
        NarrationDriftTracker(total_budget_seconds=0)


def test_segments_recorded_count():
    tracker = NarrationDriftTracker(total_budget_seconds=60.0)
    result = None
    for i in range(5):
        result = tracker.record(5.0, 5.0)
    assert result["segments_recorded"] == 5


def test_negative_drift_running_short():
    tracker = NarrationDriftTracker(total_budget_seconds=60.0)
    # Running short — actual < expected
    result = tracker.record(10.0, 7.0)  # 3s short on 60s budget = 5% exactly
    assert result["cumulative_drift_seconds"] == -3.0
    # 5% == tolerance boundary, should be at threshold
    assert result["drift_ratio"] == pytest.approx(0.05, abs=0.001)
