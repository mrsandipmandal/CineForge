"""Unit tests for CinematicMotionAnimator tool."""

from pathlib import Path
import pytest

from tools.base_tool import ExecutionMode, ToolRuntime, ToolStability, ToolTier
from tools.tool_registry import ToolRegistry
from tools.video.cinematic_motion_animator import CinematicMotionAnimator


def test_cinematic_motion_animator_registration():
    """Verify tool metadata, tier, capability, and execution contract."""
    tool = CinematicMotionAnimator()
    assert tool.name == "cinematic_motion_animator"
    assert tool.version == "0.1.0"
    assert tool.tier == ToolTier.CORE
    assert tool.capability == "video_post"
    assert tool.provider == "remotion"
    assert tool.stability == ToolStability.PRODUCTION
    assert tool.execution_mode == ExecutionMode.SYNC
    assert tool.runtime == ToolRuntime.LOCAL


def test_cinematic_motion_animator_registry_discovery():
    """Verify tool is discovered and registered in ToolRegistry."""
    registry = ToolRegistry()
    registry.discover()
    assert "cinematic_motion_animator" in registry._tools
    assert isinstance(
        registry._tools["cinematic_motion_animator"], CinematicMotionAnimator
    )


def test_build_motion_descriptor():
    """Verify 2.5D depth parallax, character dynamics, particle FX, and camera parameters."""
    tool = CinematicMotionAnimator()
    scene = {
        "id": "scene_1",
        "image": "assets/images/scene_1.png",
        "action": "Lord Rama draws the Kodanda bow",
        "mood": "heroic",
        "particle_fx": "golden_embers",
    }

    descriptor = tool.build_motion_descriptor(scene)

    assert descriptor["id"] == "scene_1"
    assert descriptor["scene_id"] == "scene_1"
    assert descriptor["image"] == "assets/images/scene_1.png"
    assert descriptor["action"] == "Lord Rama draws the Kodanda bow"
    assert descriptor["mood"] == "heroic"
    assert descriptor["motion_type"] == "2.5d_parallax_pulse"

    # Depth parallax layers
    assert descriptor["depth_layers"] == {
        "background_scale_speed": 1.05,
        "subject_scale_speed": 1.15,
        "foreground_speed": 1.35,
    }

    # Character micro-motion dynamics
    assert descriptor["character_dynamics"] == {
        "breathing": True,
        "breathing_cycle_sec": 3.2,
        "eye_glint_flicker": True,
        "weapon_glow_pulse": True,
    }

    # Particle physics
    assert descriptor["particle_fx"] == {
        "type": "golden_embers",
        "density": 35,
        "turbulence": 1.2,
    }

    # Camera dynamics
    assert descriptor["camera_dynamics"] == {
        "rate": 1.2,
        "shake_intensity": 0.0,
        "rack_focus_frames": 12,
        "whip_pan": False,
    }


def test_cinematic_motion_animator_execute():
    """Verify batch and multi-scene execution."""
    tool = CinematicMotionAnimator()
    scenes = [
        {
            "id": "scene_1",
            "image": "assets/scene1.png",
            "action": "Rama draws bow",
            "particle_fx": "golden_embers",
        },
        {
            "id": "scene_2",
            "image": "assets/scene2.png",
            "action": "Ravana summons darkness",
            "particle_fx": "dark_palace_shadows",
        },
        {
            "id": "scene_3",
            "image": "assets/scene3.png",
            "action": "Indrajit unleashes divine shockwave",
            "particle_fx": "lightning_shockwaves",
        },
    ]

    res = tool.execute({"scenes": scenes})
    assert res.success is True
    assert "descriptors" in res.data
    assert len(res.data["descriptors"]) == 3
    assert res.data["count"] == 3

    d1, d2, d3 = res.data["descriptors"]
    assert d1["particle_fx"]["type"] == "golden_embers"
    assert d2["particle_fx"]["type"] == "dark_palace_shadows"
    assert d3["particle_fx"]["type"] == "lightning_shockwaves"


def test_cinematic_motion_animator_single_scene_execution():
    """Verify execution with a single scene passed directly or under 'scene'."""
    tool = CinematicMotionAnimator()

    # Direct scene dict
    res_direct = tool.execute(
        {
            "id": "scene_direct",
            "image": "assets/direct.png",
            "particle_fx": "golden_embers",
        }
    )
    assert res_direct.success is True
    assert len(res_direct.data["descriptors"]) == 1
    assert res_direct.data["descriptors"][0]["id"] == "scene_direct"

    # Nested 'scene' dict
    res_nested = tool.execute(
        {
            "scene": {
                "id": "scene_nested",
                "image": "assets/nested.png",
            }
        }
    )
    assert res_nested.success is True
    assert len(res_nested.data["descriptors"]) == 1
    assert res_nested.data["descriptors"][0]["id"] == "scene_nested"


def test_cinematic_motion_animator_custom_overrides():
    """Verify custom parameters for depth, character, particle, and camera dynamics."""
    tool = CinematicMotionAnimator()
    custom_scene = {
        "id": "scene_custom",
        "image": "assets/custom.png",
        "depth_layers": {
            "background_scale_speed": 1.08,
            "subject_scale_speed": 1.25,
            "foreground_speed": 1.45,
        },
        "character_dynamics": {
            "breathing": False,
            "breathing_cycle_sec": 4.0,
            "eye_glint_flicker": False,
            "weapon_glow_pulse": True,
        },
        "particle_fx": {
            "type": "dark_palace_shadows",
            "density": 45,
            "turbulence": 1.8,
        },
        "camera_dynamics": {
            "rate": 1.5,
            "shake_intensity": 0.3,
            "rack_focus_frames": 24,
            "whip_pan": True,
        },
    }

    descriptor = tool.build_motion_descriptor(custom_scene)
    assert descriptor["depth_layers"]["background_scale_speed"] == 1.08
    assert descriptor["depth_layers"]["subject_scale_speed"] == 1.25
    assert descriptor["depth_layers"]["foreground_speed"] == 1.45

    assert descriptor["character_dynamics"]["breathing"] is False
    assert descriptor["character_dynamics"]["breathing_cycle_sec"] == 4.0
    assert descriptor["character_dynamics"]["eye_glint_flicker"] is False

    assert descriptor["particle_fx"]["type"] == "dark_palace_shadows"
    assert descriptor["particle_fx"]["density"] == 45
    assert descriptor["particle_fx"]["turbulence"] == 1.8

    assert descriptor["camera_dynamics"]["rate"] == 1.5
    assert descriptor["camera_dynamics"]["shake_intensity"] == 0.3
    assert descriptor["camera_dynamics"]["rack_focus_frames"] == 24
    assert descriptor["camera_dynamics"]["whip_pan"] is True


def test_cinematic_motion_animator_error_handling():
    """Verify error handling for invalid input structures."""
    tool = CinematicMotionAnimator()

    # Non-dictionary inputs
    res1 = tool.execute("invalid")  # type: ignore[arg-type]
    assert res1.success is False
    assert "inputs must be a dictionary" in res1.error

    # Invalid 'scenes' format
    res2 = tool.execute({"scenes": "not_a_list"})  # type: ignore[dict-item]
    assert res2.success is False
    assert "'scenes' must be a list" in res2.error

    # Non-dictionary scene in build_motion_descriptor
    with pytest.raises(ValueError, match="scene_dict must be a dictionary"):
        tool.build_motion_descriptor("invalid")  # type: ignore[arg-type]
