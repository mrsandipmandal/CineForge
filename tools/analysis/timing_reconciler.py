"""Timing reconciler — adjusts scene cut timestamps to match actual TTS durations.

The scene director assigns timestamps before TTS is generated. After asset
generation, actual narration durations diverge from planned durations by ±15%.
This tool recomputes cut in/out times from actual asset durations so the edit
director works with ground-truth timing, not estimates.

Usage:
    result = timing_reconciler.execute({
        "scene_plan": scene_plan_artifact,
        "asset_manifest": asset_manifest_artifact,
    })
    adjusted_cuts = result.data["adjusted_cuts"]
    total_duration = result.data["total_duration_seconds"]
"""
from __future__ import annotations

from typing import Any

from tools.base_tool import (
    BaseTool,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolTier,
    ToolStatus,
)


class TimingReconciler(BaseTool):
    name = "timing_reconciler"
    version = "1.0.0"
    tier = ToolTier.ANALYZE
    capability = "scene_analysis"
    provider = "local"
    stability = ToolStability.PRODUCTION
    runtime = ToolRuntime.LOCAL

    best_for = [
        "adjusting scene timestamps after TTS generation",
        "preventing narration bleed into adjacent scenes",
        "edit director pre-flight timing check",
        "ground-truth cut timing from probed audio durations",
    ]
    capabilities = ["timing_reconciliation", "cut_adjustment"]
    supports = {"offline": True, "stateless": True}

    input_schema = {
        "type": "object",
        "required": ["scene_plan", "asset_manifest"],
        "properties": {
            "scene_plan": {
                "type": "object",
                "description": "Full scene_plan artifact from scene director",
            },
            "asset_manifest": {
                "type": "object",
                "description": "Full asset_manifest artifact from asset director",
            },
            "gap_seconds": {
                "type": "number",
                "default": 0.0,
                "description": "Optional inter-scene gap in seconds (default 0)",
            },
        },
    }

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        scene_plan = inputs.get("scene_plan", {})
        asset_manifest = inputs.get("asset_manifest", {})
        gap = float(inputs.get("gap_seconds", 0.0))

        scenes = scene_plan.get("scenes", [])
        assets = asset_manifest.get("assets", [])

        if not scenes:
            return ToolResult(success=False, error="scene_plan has no scenes")

        # Build lookup: scene_id -> narration asset with actual duration
        narration_by_scene: dict[str, dict] = {}
        for asset in assets:
            if asset.get("type") in ("narration", "audio") and asset.get("scene_id"):
                sid = asset["scene_id"]
                if sid not in narration_by_scene:
                    narration_by_scene[sid] = asset

        cursor = 0.0
        adjusted_cuts = []
        warnings_list: list[str] = []

        for scene in scenes:
            sid = scene.get("id", "")
            planned_start = scene.get("start_seconds", 0.0)
            planned_end = scene.get("end_seconds", 0.0)
            planned_duration = planned_end - planned_start

            asset = narration_by_scene.get(sid)
            if asset and asset.get("duration_seconds"):
                actual_duration = float(asset["duration_seconds"])
                drift = actual_duration - planned_duration
                if abs(drift) > 0.5:
                    warnings_list.append(
                        f"Scene '{sid}': planned {planned_duration:.2f}s, "
                        f"actual {actual_duration:.2f}s, drift {drift:+.2f}s"
                    )
            else:
                actual_duration = max(0.0, planned_duration)
                if planned_duration > 0:
                    warnings_list.append(
                        f"Scene '{sid}': no narration asset found — "
                        f"using planned duration {planned_duration:.2f}s"
                    )

            adjusted_cuts.append({
                "scene_id": sid,
                "in_seconds": round(cursor, 3),
                "out_seconds": round(cursor + actual_duration, 3),
                "planned_duration": round(planned_duration, 3),
                "actual_duration": round(actual_duration, 3),
                "drift_seconds": round(actual_duration - planned_duration, 3),
            })
            cursor += actual_duration + gap

        total = round(cursor - gap if gap > 0 and cursor > 0 else cursor, 3)

        return ToolResult(
            success=True,
            data={
                "adjusted_cuts": adjusted_cuts,
                "total_duration_seconds": total,
                "scene_count": len(adjusted_cuts),
                "scenes_with_actual_timing": sum(
                    1 for c in adjusted_cuts
                    if narration_by_scene.get(c["scene_id"])
                ),
                "warnings": warnings_list,
            },
        )
