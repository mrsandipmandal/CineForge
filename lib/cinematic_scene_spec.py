"""Backend-neutral cinematic scene specification adapter for CineForge.

Maps narrative scene plans to backend-independent visual requirements,
and translates them cleanly to either BlenderWorld or ThreeJSWorld specifications
without duplicating renderer engines or configs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


def _hex_to_rgb_float(hex_color: str) -> list[float]:
    """Convert hex string (e.g. '#ff765f') to list of floats [r, g, b, 1.0]."""
    cleaned = hex_color.lstrip("#")
    if len(cleaned) == 6:
        r = int(cleaned[0:2], 16) / 255.0
        g = int(cleaned[2:4], 16) / 255.0
        b = int(cleaned[4:6], 16) / 255.0
        return [round(r, 3), round(g, 3), round(b, 3), 1.0]
    return [0.5, 0.5, 0.5, 1.0]


@dataclass
class CinematicSceneSpec:
    """Backend-neutral visual specification for a cinematic scene."""
    version: str = "1.0"
    scene_id: str = "scene_001"
    title: str = "Cinematic Scene"
    duration_seconds: float = 10.0
    theme: str = "mars_desert"
    seed: int = 42

    # Environment
    terrain_type: str = "dune"  # plain, peak, ridge, dune, terrace, basin, canyon
    sky_color: str = "#d6693d"
    ground_color: str = "#a13c18"
    accent_color: str = "#ff934f"

    # Camera
    camera_movement: str = "flythrough"  # flythrough, orbit, pan, dolly, static
    camera_start: list[float] = field(default_factory=lambda: [-40.0, 25.0, 35.0])
    camera_end: list[float] = field(default_factory=lambda: [40.0, 25.0, -35.0])
    camera_target: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    camera_fov: float = 60.0

    # Lighting
    lighting_mood: str = "cinematic"  # cinematic, dramatic, harsh, soft, golden_hour
    sun_direction: list[float] = field(default_factory=lambda: [0.6, -0.4, 0.7])
    sun_color: str = "#fff2df"
    ambient_intensity: float = 0.4

    # Objects / Landmarks
    objects: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "scene_id": self.scene_id,
            "title": self.title,
            "duration_seconds": self.duration_seconds,
            "theme": self.theme,
            "seed": self.seed,
            "environment": {
                "terrain_type": self.terrain_type,
                "sky_color": self.sky_color,
                "ground_color": self.ground_color,
                "accent_color": self.accent_color,
            },
            "camera": {
                "movement": self.camera_movement,
                "start_position": self.camera_start,
                "end_position": self.camera_end,
                "target": self.camera_target,
                "fov": self.camera_fov,
            },
            "lighting": {
                "mood": self.lighting_mood,
                "sun_direction": self.sun_direction,
                "sun_color": self.sun_color,
                "ambient_intensity": self.ambient_intensity,
            },
            "objects": list(self.objects),
        }

    def to_threejs_world_spec(self) -> dict[str, Any]:
        """Convert into a specification accepted by ThreeJSWorld."""
        landmarks = []
        for obj in self.objects:
            landmarks.append({
                "id": obj.get("id", "landmark-1"),
                "type": obj.get("type", "monolith"),
                "region_id": "primary-region",
                "position": obj.get("position", [0, 0, 0]),
                "scale": obj.get("scale", 2.0),
            })

        if not landmarks:
            landmarks.append({
                "id": f"{self.scene_id}-monolith",
                "type": "monolith",
                "region_id": "primary-region",
                "position": [0, 0, 0],
                "scale": 3.0,
            })

        duration = max(1.0, float(self.duration_seconds))
        return {
            "version": "1.0",
            "title": self.title,
            "seed": self.seed,
            "explicit_constraints": [f"Visual theme: {self.theme}"],
            "inferred_details": [f"Lighting mood: {self.lighting_mood}"],
            "world": {
                "size": 96,
                "resolution": 72,
                "elevation_scale": 12,
                "water_level": -1.5,
            },
            "regions": [
                {
                    "id": "primary-region",
                    "center": [0.0, 0.0],
                    "radius": 1.2,
                    "landform": self.terrain_type if self.terrain_type in {
                        "plain", "peak", "ridge", "dune", "terrace", "basin", "canyon"
                    } else "dune",
                    "color": self.ground_color,
                    "accent_color": self.accent_color,
                    "scatter": {"rock": 15, "crystal": 6},
                }
            ],
            "landmarks": landmarks,
            "camera_path": [
                {"time": 0.0, "position": self.camera_start, "target": self.camera_target},
                {
                    "time": duration / 2.0,
                    "position": [
                        (self.camera_start[0] + self.camera_end[0]) / 2.0,
                        (self.camera_start[1] + self.camera_end[1]) / 2.0 + 5.0,
                        (self.camera_start[2] + self.camera_end[2]) / 2.0,
                    ],
                    "target": self.camera_target,
                },
                {"time": duration, "position": self.camera_end, "target": self.camera_target},
            ],
        }

    def to_blender_world_spec(self) -> dict[str, Any]:
        """Convert into a specification accepted by BlenderWorld."""
        ground_rgba = _hex_to_rgb_float(self.ground_color)
        sun_rgba = _hex_to_rgb_float(self.sun_color)

        return {
            "version": "1.0",
            "title": self.title,
            "seed": self.seed,
            "fps": 30,
            "duration": float(self.duration_seconds),
            "terrain": {
                "height_scale": 16.0,
                "frequency": 0.02,
                "base_color": ground_rgba,
                "roughness": 0.85,
            },
            "regions": [
                {
                    "name": "MainRegion",
                    "center": [0.0, 0.0],
                    "radius": 50.0,
                    "color": ground_rgba,
                    "roughness": 0.8,
                }
            ],
            "camera": {
                "position": self.camera_start,
                "target": self.camera_target,
                "lens": 44,
                "path": [
                    {"frame": 1, "position": self.camera_start, "target": self.camera_target},
                    {
                        "frame": max(2, int(self.duration_seconds * 30)),
                        "position": self.camera_end,
                        "target": self.camera_target,
                    },
                ],
            },
            "lighting": {
                "sun_direction": self.sun_direction,
                "sun_color": sun_rgba[:3],
                "sun_energy": 5.0 if self.lighting_mood in ["dramatic", "harsh"] else 3.5,
                "ambient_color": [0.2, 0.2, 0.25],
            },
            "assets": [
                {
                    "id": obj.get("id", f"asset-{i}"),
                    "name": obj.get("name", "Prop"),
                    "position": obj.get("position", [0.0, 0.0, 0.0]),
                    "scale": obj.get("scale", 1.0),
                }
                for i, obj in enumerate(self.objects)
            ],
        }

    @classmethod
    def from_scene_plan_scene(
        cls,
        scene: dict[str, Any],
        seed: int = 42,
    ) -> CinematicSceneSpec:
        """Construct a CinematicSceneSpec from a narrative scene_plan scene dictionary."""
        scene_id = scene.get("id", "scene_001")
        desc = scene.get("description", "Cinematic landscape")
        start = float(scene.get("start_seconds", 0.0))
        end = float(scene.get("end_seconds", 10.0))
        duration = max(1.0, end - start)

        # Detect theme from description
        desc_lower = desc.lower()
        if "mars" in desc_lower or "red planet" in desc_lower:
            theme = "mars_desert"
            terrain = "dune"
            ground = "#a13c18"
            sky = "#d6693d"
            accent = "#ff934f"
        elif "cyber" in desc_lower or "neon" in desc_lower or "city" in desc_lower:
            theme = "cyberpunk_city"
            terrain = "ridge"
            ground = "#1a162b"
            sky = "#0b0819"
            accent = "#00f0ff"
        elif "space" in desc_lower or "cosmic" in desc_lower:
            theme = "deep_space"
            terrain = "peak"
            ground = "#111422"
            sky = "#05070e"
            accent = "#7a5cff"
        else:
            theme = "cinematic_landscape"
            terrain = "dune"
            ground = "#4a3c31"
            sky = "#87ceeb"
            accent = "#ffd700"

        # Camera movement detection
        if "orbit" in desc_lower:
            cam_mov = "orbit"
            start_pos = [-35.0, 20.0, 35.0]
            end_pos = [35.0, 20.0, 35.0]
        elif "zoom" in desc_lower or "push" in desc_lower or "dolly" in desc_lower:
            cam_mov = "dolly"
            start_pos = [0.0, 15.0, 50.0]
            end_pos = [0.0, 8.0, 15.0]
        else:
            cam_mov = "flythrough"
            start_pos = [-40.0, 25.0, 35.0]
            end_pos = [40.0, 25.0, -35.0]

        return cls(
            version="1.0",
            scene_id=scene_id,
            title=scene.get("narrative_role") or scene.get("type", "cinematic"),
            duration_seconds=duration,
            theme=theme,
            seed=seed,
            terrain_type=terrain,
            ground_color=ground,
            sky_color=sky,
            accent_color=accent,
            camera_movement=cam_mov,
            camera_start=start_pos,
            camera_end=end_pos,
            camera_target=[0.0, 0.0, 0.0],
            camera_fov=60.0,
            lighting_mood="cinematic",
        )
