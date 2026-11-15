"""Tests for shot_prompt_builder."""
import warnings
from lib.shot_prompt_builder import build_shot_prompt, build_batch_prompts


def _scene(desc="Test scene", shot_size="medium", movement="static", lighting="natural"):
    return {
        "id": "s01",
        "description": desc,
        "type": "generated",
        "shot_language": {
            "shot_size": shot_size,
            "camera_movement": movement,
            "lighting_key": lighting,
        }
    }


def test_build_shot_prompt_with_style_context():
    scene = _scene("Person walks into bright office")
    ctx = {"mood": "professional", "visual_language": {"aesthetic": "clean, minimal"}}
    prompt = build_shot_prompt(scene, style_context=ctx)
    assert "clean, minimal" in prompt or "professional" in prompt
    assert "Person walks into bright office" in prompt


def test_build_shot_prompt_playbook_fallback():
    scene = _scene("Product shot on white background")
    prompt = build_shot_prompt(scene, playbook_name="clean-professional")
    assert len(prompt) > 10  # just check it runs and produces output


def test_build_shot_prompt_warns_without_context():
    scene = _scene("Generic scene")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        build_shot_prompt(scene)
        assert any("style_context" in str(warning.message) for warning in w)


def test_build_batch_prompts_forwards_playbook():
    scenes = [_scene(f"Scene {i}") for i in range(3)]
    results = build_batch_prompts(scenes, playbook_name="flat-motion-graphics")
    assert len(results) == 3
    for r in results:
        assert "prompt" in r
        assert len(r["prompt"]) > 10


def test_all_shot_sizes_produce_output():
    sizes = ["extreme_wide", "wide", "medium_wide", "medium", "medium_close",
             "close_up", "extreme_close_up", "over_shoulder", "insert", "establishing"]
    for size in sizes:
        s = _scene(shot_size=size)
        ctx = {"mood": "test", "visual_language": {"aesthetic": "test style"}}
        prompt = build_shot_prompt(s, style_context=ctx)
        assert len(prompt) > 0, f"Empty prompt for shot_size={size}"


def test_playbook_name_produces_style_in_layer5():
    """Playbook name should produce a Style layer in the output."""
    scene = _scene("Epic battle scene")
    prompt = build_shot_prompt(scene, playbook_name="cinematic")
    assert "cinematic" in prompt.lower() or "dramatic" in prompt.lower() or "Style" in prompt
