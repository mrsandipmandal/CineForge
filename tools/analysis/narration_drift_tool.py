"""Tool wrapper for NarrationDriftTracker — exposes drift tracking to agents."""
from __future__ import annotations
from typing import Any
from tools.base_tool import BaseTool, ToolResult, ToolRuntime, ToolStability, ToolTier, ToolStatus


class NarrationDriftTool(BaseTool):
    name = "narration_drift_tracker"
    version = "1.0.0"
    tier = ToolTier.ANALYZE
    capability = "scene_analysis"
    provider = "local"
    stability = ToolStability.PRODUCTION
    runtime = ToolRuntime.LOCAL

    best_for = [
        "TTS timing drift detection",
        "cumulative narration drift",
        "audio sync quality",
        "asset director pre-flight",
    ]
    capabilities = ["drift_tracking", "timing_validation"]
    supports = {"offline": True, "stateless": True}

    input_schema = {
        "type": "object",
        "required": ["total_budget_seconds", "segments"],
        "properties": {
            "total_budget_seconds": {
                "type": "number",
                "description": "Total target video duration in seconds",
            },
            "segments": {
                "type": "array",
                "description": "List of {expected_seconds, actual_seconds} pairs",
                "items": {
                    "type": "object",
                    "required": ["expected_seconds", "actual_seconds"],
                    "properties": {
                        "expected_seconds": {"type": "number"},
                        "actual_seconds": {"type": "number"},
                    },
                },
            },
            "tolerance_ratio": {
                "type": "number",
                "default": 0.05,
                "description": "Maximum acceptable drift as ratio of total_budget (default 5%)",
            },
        },
    }

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        from lib.narration_drift_tracker import NarrationDriftTracker

        try:
            tracker = NarrationDriftTracker(
                total_budget_seconds=float(inputs["total_budget_seconds"]),
                tolerance_ratio=float(inputs.get("tolerance_ratio", 0.05)),
            )
            results = []
            for seg in inputs.get("segments", []):
                r = tracker.record(
                    expected_seconds=float(seg["expected_seconds"]),
                    actual_seconds=float(seg["actual_seconds"]),
                )
                results.append(r)

            final = results[-1] if results else {}
            return ToolResult(
                success=True,
                data={
                    "segment_results": results,
                    "final_cumulative_drift_seconds": tracker.current_drift,
                    "final_drift_ratio": final.get("drift_ratio", 0.0),
                    "exceeds_threshold": final.get("exceeds_threshold", False),
                    "recommendation": final.get("recommendation", "ok"),
                    "total_segments": tracker.segments_recorded,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
