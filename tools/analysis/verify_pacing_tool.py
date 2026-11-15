"""Tool wrapper for verify_scene_pacing — exposes pacing alignment check to agents."""
from __future__ import annotations
from typing import Any
from tools.base_tool import BaseTool, ToolResult, ToolRuntime, ToolStability, ToolTier, ToolStatus


class VerifyPacingTool(BaseTool):
    name = "verify_pacing"
    version = "1.0.0"
    tier = ToolTier.ANALYZE
    capability = "scene_analysis"
    provider = "local"
    stability = ToolStability.PRODUCTION
    runtime = ToolRuntime.LOCAL

    best_for = [
        "scene pacing validation",
        "narration alignment check",
        "terminal scene timing",
        "compose pre-flight",
    ]
    capabilities = ["verify_scene_pacing", "trace_steps"]
    supports = {"offline": True}

    input_schema = {
        "type": "object",
        "required": ["steps"],
        "properties": {
            "steps": {
                "type": "array",
                "description": "List of step dicts with 'kind' field (cmd/out/pause/pill)",
                "items": {"type": "object"},
            },
            "scene_start": {"type": "number", "default": 0.0},
            "scene_end": {"type": "number", "description": "Required for alignment check"},
            "narration_cues": {
                "type": "array",
                "description": "List of [time_seconds, description] pairs",
                "items": {"type": "array"},
            },
            "tolerance": {"type": "number", "default": 1.0},
            "fps": {"type": "integer", "default": 30},
            "mode": {
                "type": "string",
                "enum": ["trace", "assert"],
                "default": "trace",
                "description": "'trace' returns landmark table, 'assert' raises on misalignment",
            },
        },
    }

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        from lib.verify_scene_pacing import trace, assert_alignment

        steps = inputs.get("steps", [])
        scene_start = float(inputs.get("scene_start", 0.0))
        fps = int(inputs.get("fps", 30))
        mode = inputs.get("mode", "trace")

        try:
            landmarks = trace(steps, scene_start=scene_start, fps=fps, quiet=True)
            landmark_data = [
                {"video_time": lm.video_time, "kind": lm.kind, "text": lm.text}
                for lm in landmarks
            ]

            if mode == "assert":
                scene_end = inputs.get("scene_end")
                if scene_end is None:
                    return ToolResult(success=False, error="scene_end required for assert mode")
                narration_cues_raw = inputs.get("narration_cues", [])
                narration_cues = [(float(c[0]), str(c[1])) for c in narration_cues_raw]
                assert_alignment(
                    steps,
                    scene_start=scene_start,
                    scene_end=float(scene_end),
                    narration_cues=narration_cues,
                    tolerance=float(inputs.get("tolerance", 1.0)),
                    fps=fps,
                )

            return ToolResult(
                success=True,
                data={
                    "landmarks": landmark_data,
                    "landmark_count": len(landmark_data),
                    "mode": mode,
                },
            )
        except AssertionError as e:
            return ToolResult(success=False, error=str(e))
        except Exception as e:
            return ToolResult(success=False, error=f"verify_pacing error: {e}")
