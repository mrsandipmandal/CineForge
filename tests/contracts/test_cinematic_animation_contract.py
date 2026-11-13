"""Contract tests for Cinematic Animation integration and scene specification adapter."""

import pytest
from lib.cinematic_scene_spec import CinematicSceneSpec
from tools.graphics.blender_world import BlenderWorld, find_blender
from tools.graphics.threejs_world import ThreeJSWorld
from tools.graphics.math_animate import MathAnimate
from tools.character.character_animation import CharacterSpecGenerator


def test_cinematic_scene_spec_to_threejs_validation():
    """Verify CinematicSceneSpec converts to a spec accepted and validated by ThreeJSWorld."""
    spec = CinematicSceneSpec(
        scene_id="mars_flyover",
        title="Red Planet Canyon Flyover",
        duration_seconds=10.0,
        theme="mars_desert",
        terrain_type="canyon",
        ground_color="#a13c18",
        accent_color="#ff765f",
    )
    threejs_spec = spec.to_threejs_world_spec()
    assert threejs_spec["version"] == "1.0"
    assert threejs_spec["title"] == "Red Planet Canyon Flyover"
    assert len(threejs_spec["regions"]) >= 1
    assert len(threejs_spec["camera_path"]) == 3

    # Execute ThreeJSWorld validation operation
    tool = ThreeJSWorld()
    res = tool.execute({
        "operation": "validate",
        "world_spec": threejs_spec,
        "duration_seconds": 10.0,
    })
    assert res.success, res.error
    assert res.data["report"]["valid"] is True


def test_cinematic_scene_spec_to_blender_spec():
    """Verify CinematicSceneSpec converts to valid BlenderWorld spec dictionary."""
    spec = CinematicSceneSpec(
        scene_id="mars_scene",
        title="Mars Surface",
        duration_seconds=5.0,
        theme="mars_desert",
    )
    blender_spec = spec.to_blender_world_spec()
    assert blender_spec["version"] == "1.0"
    assert blender_spec["title"] == "Mars Surface"
    assert "terrain" in blender_spec
    assert "camera" in blender_spec
    assert "lighting" in blender_spec
    assert blender_spec["fps"] == 30
    assert blender_spec["duration"] == 5.0


def test_cinematic_scene_spec_from_scene_plan():
    """Verify construction from a scene in narrative scene_plan."""
    scene = {
        "id": "scene_mars_01",
        "type": "generated",
        "narrative_role": "Hero reveal of Mars crater",
        "description": "Dramatic camera orbit revealing the vast red crater on Mars under the Martian sun",
        "start_seconds": 0.0,
        "end_seconds": 8.0,
    }
    spec = CinematicSceneSpec.from_scene_plan_scene(scene)
    assert spec.scene_id == "scene_mars_01"
    assert spec.duration_seconds == 8.0
    assert spec.theme == "mars_desert"
    assert spec.camera_movement == "orbit"
    assert spec.terrain_type in ["dune", "canyon", "plain"]


def test_blender_world_doctor_and_availability():
    """Verify BlenderWorld doctor executes safely and reports honest status."""
    tool = BlenderWorld()
    assert tool.capability == "3d_world_rendering"
    assert tool.provider == "blender"

    blender_bin = find_blender()
    res = tool.execute({"operation": "doctor"})
    if blender_bin:
        assert res.success is True
        assert res.data["available"] is True
    else:
        assert res.success is False
        assert "Blender not found" in str(res.error)


def test_math_animate_safety_boundary():
    """Verify MathAnimate blocks unsafe code while permitting clean Manim scenes."""
    tool = MathAnimate()
    assert tool.capability == "graphics"
    assert tool.provider == "manim"

    # Blocked code attempting to import os/subprocess
    unsafe_code = """
from manim import *
import os
os.system('ls')
class MyScene(Scene):
    def construct(self):
        pass
"""
    violations = tool._scan_scene_code(unsafe_code)
    assert len(violations) > 0
    assert any("import os" in v.lower() or "os" in v for v in violations)

    # Safe code produces no violations
    safe_code = """
from manim import *
class SquareToCircle(Scene):
    def construct(self):
        circle = Circle()
        self.play(Create(circle))
"""
    assert tool._scan_scene_code(safe_code) == []


def test_character_animation_spec_tool_contract():
    """Verify CharacterSpecGenerator creates valid character specifications."""
    tool = CharacterSpecGenerator()
    assert tool.capability == "character_animation"
    res = tool.execute({
        "name": "RoboGuide",
        "archetype": "guide",
        "palette": {
            "primary": "#3366cc",
            "secondary": "#ff9900",
            "accent": "#ffffff",
        },
    })
    assert res.success is True
    assert "character_design" in res.data
    assert len(res.data["character_design"]["characters"]) > 0
