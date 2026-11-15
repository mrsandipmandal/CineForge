"""Tests for shot_prompt_builder style context resolution."""
import warnings
from lib.shot_prompt_builder import build_shot_prompt, build_batch_prompts


def _scene(desc="Test scene", shot_size="medium", movement="static", lighting="natural"):
    return {
        "id": "s01", "description": desc, "type": "generated",
        "shot_language": {
            "shot_size": shot_size,
            "camera_movement": movement,
            "lighting_key": lighting,
        },
    }


def test_build_with_explicit_style_context():
    ctx = {"mood": "professional", "visual_language": {"aesthetic": "clean, minimal"}}
    prompt = build_shot_prompt(_scene("Person in office"), style_context=ctx)
    assert "Person in office" in prompt
    assert "clean, minimal" in prompt or "professional" in prompt


def test_build_with_playbook_name_fallback():
    prompt = build_shot_prompt(_scene("Product shot"), playbook_name="clean-professional")
    assert "Product shot" in prompt
    # Should include style from default context, no warning
    assert len(prompt) > 10


def test_build_warns_without_context():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        build_shot_prompt(_scene("Generic scene"))
    assert any("style_context" in str(w.message) for w in caught)


def test_all_playbooks_have_style():
    from lib.shot_prompt_builder import _DEFAULT_STYLE_CONTEXTS
    for name, ctx in _DEFAULT_STYLE_CONTEXTS.items():
        assert ctx.get("mood"), f"playbook {name} missing mood"
        assert ctx.get("visual_language", {}).get("aesthetic"), f"playbook {name} missing aesthetic"


def test_batch_prompts_forwards_playbook():
    scenes = [_scene(f"Scene {i}") for i in range(3)]
    results = build_batch_prompts(scenes, playbook_name="flat-motion-graphics")
    assert len(results) == 3
    for r in results:
        assert len(r["prompt"]) > 10


def test_no_duplicate_style_on_explicit_context():
    """When explicit style_context is passed, playbook_name should not override it."""
    ctx = {"mood": "X_explicit", "visual_language": {"aesthetic": "X_aesthetic"}}
    prompt = build_shot_prompt(_scene("Test"), style_context=ctx, playbook_name="cinematic")
    assert "X_aesthetic" in prompt
    assert "anamorphic" not in prompt  # cinematic default should NOT appear
