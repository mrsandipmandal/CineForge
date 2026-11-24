"""Shot prompt builder — converts structured shot language into provider-optimized prompts.
Uses a 5-layer framework based on professional cinematography prompting research:
  Layer 1: Camera (lens, depth of field)
  Layer 2: Movement (shot size, camera movement)
  Layer 3: Subject (description + texture keywords)
  Layer 4: Lighting (lighting key, color temperature)
  Layer 5: Style (adapted from playbook, not verbatim)
This replaces the old approach of prepending a fixed playbook image_prompt_prefix
to every scene description, which made all scenes look the same.
"""
from __future__ import annotations
from typing import Any

# Default style contexts per playbook — used as fallback when style_context is not passed.
# Prevents visually incoherent output from missing style layer in generated asset prompts.
_DEFAULT_STYLE_CONTEXTS: dict[str, dict] = {
    "clean-professional": {
        "mood": "clean, professional, polished",
        "visual_language": {"aesthetic": "minimal, bright, corporate, airy, well-lit"},
    },
    "flat-motion-graphics": {
        "mood": "dynamic, bold, vibrant",
        "visual_language": {"aesthetic": "bold colors, dark background, motion graphics, high contrast"},
    },
    "cinematic": {
        "mood": "dramatic, epic, atmospheric",
        "visual_language": {"aesthetic": "cinematic, film grain, anamorphic, moody, wide aspect"},
    },
    "minimalist-diagram": {
        "mood": "clean, precise, informational",
        "visual_language": {"aesthetic": "minimal, diagram-style, clean lines, whitespace, monochrome accent"},
    },
    "anime-ghibli": {
        "mood": "whimsical, warm, painterly",
        "visual_language": {"aesthetic": "anime, hand-painted, soft light, Ghibli, natural tones"},
    },
    "documentary-montage": {
        "mood": "authentic, grounded, observational",
        "visual_language": {"aesthetic": "documentary, handheld, natural light, real-world, candid"},
    },
}

# Mapping from shot_language enums to natural language for prompting
_SHOT_SIZE_PHRASES = {
    "extreme_wide": "extreme wide shot showing vast environment",
    "wide": "wide shot capturing full scene",
    "medium_wide": "medium-wide shot framing subject with surroundings",
    "medium": "medium shot from waist up",
    "medium_close": "medium close-up from chest up",
    "close_up": "close-up focusing on face or detail",
    "extreme_close_up": "extreme close-up on fine detail",
    "over_shoulder": "over-the-shoulder perspective",
    "insert": "insert shot of specific detail",
    "establishing": "establishing shot setting the location",
}
_MOVEMENT_PHRASES = {
    "static": "locked-off static camera",
    "pan_left": "smooth pan to the left",
    "pan_right": "smooth pan to the right",
    "tilt_up": "gentle tilt upward",
    "tilt_down": "gentle tilt downward",
    "dolly_in": "slow dolly in toward subject",
    "dolly_out": "slow dolly out from subject",
    "tracking_left": "tracking shot moving left alongside subject",
    "tracking_right": "tracking shot moving right alongside subject",
    "crane_up": "crane shot rising upward",
    "crane_down": "crane shot descending",
    "handheld": "handheld camera with natural movement",
    "steadicam": "smooth steadicam following movement",
    "whip_pan": "fast whip pan",
    "orbital": "orbital camera circling subject",
    "zoom_in": "slow zoom in",
    "zoom_out": "slow zoom out",
    "rack_focus": "rack focus shift between foreground and background",
}
_LIGHTING_PHRASES = {
    "high_key": "bright high-key lighting, minimal shadows",
    "low_key": "dramatic low-key lighting with deep shadows",
    "natural": "natural ambient lighting",
    "golden_hour": "warm golden hour sunlight",
    "blue_hour": "cool blue hour twilight",
    "tungsten_warm": "warm tungsten interior lighting",
    "neon": "neon-lit with vibrant color spill",
    "silhouette": "backlit silhouette",
    "rim_lit": "rim lighting highlighting edges",
    "volumetric": "volumetric light with visible rays",
    "overcast_soft": "soft overcast diffused light",
}
_DOF_PHRASES = {
    "shallow": "shallow depth of field with bokeh",
    "medium": "medium depth of field",
    "deep": "deep focus with everything sharp",
}
_COLOR_TEMP_PHRASES = {
    "cool": "cool blue-toned color palette",
    "neutral": "neutral balanced colors",
    "warm": "warm amber-toned color palette",
    "mixed": "mixed color temperatures for contrast",
}


def build_shot_prompt(
    scene: dict[str, Any],
    style_context: dict[str, Any] | None = None,
    playbook_name: str | None = None,
) -> str:
    """Convert a scene with structured shot language into a generation prompt.

    Args:
        scene: Scene dict from scene_plan (with shot_language, description,
               texture_keywords, etc.)
        style_context: Optional playbook-derived style info with keys like
                       'generation_prefix', 'visual_language', 'mood'.
        playbook_name: Optional playbook name used as fallback when
                       style_context is not provided.

    Returns:
        A natural-language prompt optimized for image/video generation.
    """
    # Resolve style context: explicit > playbook default > warn
    _resolved_style = style_context
    if _resolved_style is None:
        if playbook_name:
            _resolved_style = _DEFAULT_STYLE_CONTEXTS.get(playbook_name)
        if _resolved_style is None:
            import warnings
            warnings.warn(
                "build_shot_prompt called without style_context or playbook_name. "
                "Generated images will lack consistent aesthetic direction. "
                "Pass style_context from the active playbook to ensure visual coherence.",
                UserWarning,
                stacklevel=2,
            )

    sl = scene.get("shot_language", {})
    layers: list[str] = []

    # Layer 1: Camera — lens and depth of field
    camera_parts = []
    if sl.get("lens_mm"):
        camera_parts.append(f"{sl['lens_mm']}mm lens")
    if sl.get("depth_of_field"):
        camera_parts.append(_DOF_PHRASES.get(sl["depth_of_field"], ""))
    if camera_parts:
        layers.append(", ".join(filter(None, camera_parts)))

    # Layer 2: Movement — shot size and camera movement
    movement_parts = []
    if sl.get("shot_size"):
        movement_parts.append(_SHOT_SIZE_PHRASES.get(sl["shot_size"], sl["shot_size"]))
    if sl.get("camera_movement") and sl["camera_movement"] != "static":
        movement_parts.append(_MOVEMENT_PHRASES.get(sl["camera_movement"], sl["camera_movement"]))
    if movement_parts:
        layers.append(", ".join(movement_parts))

    # Layer 3: Subject — the scene description + texture keywords
    description = scene.get("description", "")
    texture = scene.get("texture_keywords", [])
    subject_parts = [description]
    if texture:
        subject_parts.append(", ".join(texture))
    layers.append(". ".join(filter(None, subject_parts)))

    # Layer 4: Lighting — lighting key and color temperature
    lighting_parts = []
    if sl.get("lighting_key"):
        lighting_parts.append(_LIGHTING_PHRASES.get(sl["lighting_key"], sl["lighting_key"]))
    if sl.get("color_temperature"):
        lighting_parts.append(_COLOR_TEMP_PHRASES.get(sl["color_temperature"], ""))
    if lighting_parts:
        layers.append(", ".join(filter(None, lighting_parts)))

    # Layer 5: Style — adapted from playbook (NOT verbatim prefix)
    if _resolved_style:
        mood = _resolved_style.get("mood", "")
        visual_lang = _resolved_style.get("visual_language", {})
        style_hint = visual_lang.get("aesthetic", "") or mood
        if style_hint:
            layers.append(f"Style: {style_hint}")

    return ". ".join(filter(None, layers))


def build_batch_prompts(
    scenes: list[dict[str, Any]],
    style_context: dict[str, Any] | None = None,
    playbook_name: str | None = None,
) -> list[dict[str, str]]:
    """Build prompts for all visual scenes in a scene plan.

    Returns list of {scene_id, prompt} dicts.
    """
    results = []
    for scene in scenes:
        scene_type = scene.get("type", "")
        if scene_type in ("transition",):
            continue
        prompt = build_shot_prompt(scene, style_context, playbook_name=playbook_name)
        results.append({
            "scene_id": scene.get("id", "unknown"),
            "prompt": prompt,
            "hero_moment": scene.get("hero_moment", False),
        })
    return results
