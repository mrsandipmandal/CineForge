"""Cinematic motion animator tool for 2.5D depth parallax and micro-motion.

Generates multi-frame 2.5D depth parallax descriptors, character micro-motion
(sinusoidal breathing expansion, eye glint flickers, weapon glow pulses), and
procedural particle dynamics for Remotion compositions.
"""

from __future__ import annotations

import logging
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolTier,
)

logger = logging.getLogger(__name__)


class CinematicMotionAnimator(BaseTool):
    """Generates 2.5D multi-frame cinematic motion descriptors for Remotion.

    Replaces static Ken Burns pan/zoom with true 2.5D depth parallax layers,
    sinusoidal character micro-motions (breathing, subtle eye glints), and
    procedural particle dynamics (golden embers, dark palace shadows, lightning)
    to elevate visual immersion and guarantee monetization compliance.
    """

    name = "cinematic_motion_animator"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "video_post"
    provider = "remotion"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    runtime = ToolRuntime.LOCAL
    determinism = Determinism.DETERMINISTIC

    agent_skills = [
        "remotion",
        "remotion-best-practices",
        "mythological-video-production",
    ]
    capabilities = [
        "cinematic_motion_animation",
        "depth_parallax",
        "character_micro_motion",
    ]

    input_schema = {
        "type": "object",
        "properties": {
            "scenes": {
                "type": "array",
                "items": {"type": "object"},
                "description": "List of scene dictionaries to process.",
            },
            "scene": {
                "type": "object",
                "description": "Single scene dictionary to process.",
            },
            "id": {
                "type": "string",
                "description": "Scene identifier.",
            },
            "image": {
                "type": "string",
                "description": "Path to primary scene image.",
            },
            "action": {
                "type": "string",
                "description": "Action description for the scene.",
            },
            "mood": {
                "type": "string",
                "description": "Atmospheric mood for the scene.",
            },
            "particle_fx": {
                "type": ["string", "object"],
                "description": "Particle effect preset or custom dictionary.",
            },
        },
    }

    output_schema = {
        "type": "object",
        "properties": {
            "descriptors": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Generated cinematic motion descriptors.",
            },
            "count": {
                "type": "integer",
                "description": "Number of descriptors generated.",
            },
        },
    }

    def build_motion_descriptor(self, scene_dict: dict[str, Any]) -> dict[str, Any]:
        """Validate scene data and generate 2.5D depth parallax and micro-motion parameters."""
        if not isinstance(scene_dict, dict):
            raise ValueError("scene_dict must be a dictionary")

        scene_id = str(scene_dict.get("id") or scene_dict.get("scene_id") or "scene_1")
        image = str(scene_dict.get("image") or scene_dict.get("image_path") or "")
        if not image and isinstance(scene_dict.get("images"), list) and scene_dict["images"]:
            image = str(scene_dict["images"][0])

        action = str(scene_dict.get("action", ""))
        mood = str(scene_dict.get("mood", ""))

        try:
            duration_seconds = float(
                scene_dict.get("duration_seconds", scene_dict.get("duration", 5.0))
            )
        except (ValueError, TypeError):
            duration_seconds = 5.0

        # 2.5D Depth parallax parameters
        dl = (
            scene_dict.get("depth_layers")
            if isinstance(scene_dict.get("depth_layers"), dict)
            else {}
        )
        depth_layers = {
            "background_scale_speed": float(dl.get("background_scale_speed", 1.05)),
            "subject_scale_speed": float(dl.get("subject_scale_speed", 1.15)),
            "foreground_speed": float(dl.get("foreground_speed", 1.35)),
        }

        # Character micro-motion dynamics
        cd = (
            scene_dict.get("character_dynamics")
            if isinstance(scene_dict.get("character_dynamics"), dict)
            else {}
        )
        character_dynamics = {
            "breathing": bool(cd.get("breathing", True)),
            "breathing_cycle_sec": float(cd.get("breathing_cycle_sec", 3.2)),
            "eye_glint_flicker": bool(cd.get("eye_glint_flicker", True)),
            "weapon_glow_pulse": bool(cd.get("weapon_glow_pulse", True)),
        }

        # Procedural particle dynamics
        p_fx = scene_dict.get("particle_fx")
        if isinstance(p_fx, dict):
            p_type = p_fx.get("type", "golden_embers")
            p_density = int(p_fx.get("density", 35))
            p_turbulence = float(p_fx.get("turbulence", 1.2))
        elif isinstance(p_fx, str) and p_fx.strip():
            p_type = p_fx.strip()
            p_density = 35
            p_turbulence = 1.2
        else:
            p_type = "golden_embers"
            p_density = 35
            p_turbulence = 1.2

        particle_fx = {
            "type": p_type,
            "density": p_density,
            "turbulence": p_turbulence,
        }

        # Camera dynamics
        cam = (
            scene_dict.get("camera_dynamics")
            if isinstance(scene_dict.get("camera_dynamics"), dict)
            else {}
        )
        camera_dynamics = {
            "rate": float(cam.get("rate", 1.2)),
            "shake_intensity": float(cam.get("shake_intensity", 0.0)),
            "rack_focus_frames": int(cam.get("rack_focus_frames", 12)),
            "whip_pan": bool(cam.get("whip_pan", False)),
        }

        descriptor: dict[str, Any] = {
            "id": scene_id,
            "scene_id": scene_id,
            "image": image,
            "action": action,
            "mood": mood,
            "duration_seconds": duration_seconds,
            "motion_type": "2.5d_parallax_pulse",
            "depth_layers": depth_layers,
            "character_dynamics": character_dynamics,
            "particle_fx": particle_fx,
            "camera_dynamics": camera_dynamics,
        }

        # Forward any extra scene keys (e.g. background_image, subject_image)
        for key, value in scene_dict.items():
            if key not in descriptor:
                descriptor[key] = value

        return descriptor

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        """Generate motion descriptors for a single scene or list of scenes."""
        if not isinstance(inputs, dict):
            return ToolResult(success=False, error="inputs must be a dictionary")

        scenes: list[dict[str, Any]] = []
        if "scenes" in inputs:
            raw_scenes = inputs["scenes"]
            if not isinstance(raw_scenes, list):
                return ToolResult(
                    success=False,
                    error="'scenes' must be a list of scene dictionaries",
                )
            scenes = raw_scenes
        elif "scene" in inputs and isinstance(inputs["scene"], dict):
            scenes = [inputs["scene"]]
        elif inputs:
            # Single scene passed directly
            scenes = [inputs]
        else:
            scenes = []

        try:
            descriptors = [self.build_motion_descriptor(s) for s in scenes]
            return ToolResult(
                success=True,
                data={
                    "descriptors": descriptors,
                    "count": len(descriptors),
                },
            )
        except Exception as exc:
            logger.exception("Failed to build motion descriptors: %s", exc)
            return ToolResult(success=False, error=str(exc))
