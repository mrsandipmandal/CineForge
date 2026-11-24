"""Cumulative TTS narration drift tracker.

Tracks accumulated timing drift across multiple TTS segments and raises
a warning when cumulative drift exceeds a configurable threshold.

Usage:
    tracker = NarrationDriftTracker(total_budget_seconds=60.0)
    result = tracker.record(expected_seconds=5.0, actual_seconds=5.35)
    if result["exceeds_threshold"]:
        # re-plan remaining segment timing
        pass
"""
from __future__ import annotations


class NarrationDriftTracker:
    """Track cumulative TTS timing drift across a multi-segment narration."""

    def __init__(self, total_budget_seconds: float, tolerance_ratio: float = 0.05):
        """
        Args:
            total_budget_seconds: Total target duration of the video in seconds.
            tolerance_ratio: Maximum acceptable ratio of cumulative drift to total budget (default 5%).
        """
        if total_budget_seconds <= 0:
            raise ValueError("total_budget_seconds must be > 0")
        self.budget = total_budget_seconds
        self.tolerance = tolerance_ratio
        self.accumulated_actual = 0.0
        self.accumulated_expected = 0.0
        self.segments_recorded = 0

    def record(self, expected_seconds: float, actual_seconds: float) -> dict:
        """Record one segment's expected vs actual duration.

        Returns:
            {
                "cumulative_drift_seconds": float,  # positive = running long
                "drift_ratio": float,               # drift / total_budget
                "exceeds_threshold": bool,
                "recommendation": str,
                "segments_recorded": int,
            }
        """
        self.accumulated_expected += expected_seconds
        self.accumulated_actual += actual_seconds
        self.segments_recorded += 1

        drift = self.accumulated_actual - self.accumulated_expected
        ratio = abs(drift) / self.budget

        return {
            "cumulative_drift_seconds": round(drift, 3),
            "drift_ratio": round(ratio, 4),
            "exceeds_threshold": ratio > self.tolerance,
            "recommendation": (
                "Re-plan remaining segment timing to compensate for cumulative drift"
                if ratio > self.tolerance else "ok"
            ),
            "segments_recorded": self.segments_recorded,
        }

    def reset(self) -> None:
        """Reset accumulated state for a new narration pass."""
        self.accumulated_actual = 0.0
        self.accumulated_expected = 0.0
        self.segments_recorded = 0

    @property
    def current_drift(self) -> float:
        """Current cumulative drift in seconds (positive = running long)."""
        return round(self.accumulated_actual - self.accumulated_expected, 3)
