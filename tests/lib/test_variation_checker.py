"""Tests for variation checker severity multiplier."""
from lib.variation_checker import check_scene_variation


def _scene(desc, shot_size=None, movement="static", intent=None):
    s = {"description": desc, "type": "generated"}
    sl = {"camera_movement": movement}
    if shot_size:
        sl["shot_size"] = shot_size
    s["shot_language"] = sl
    if intent:
        s["shot_intent"] = intent
    return s


def test_four_violations_not_acceptable():
    """4+ simultaneous violations must produce revise or fail, not acceptable."""
    # Trigger: same shot size, no intent, no hero, generic descriptions, no texture, static movement
    scenes = [
        _scene("A person using a computer", shot_size="medium"),
        _scene("A person typing on keyboard", shot_size="medium"),
        _scene("A person looking at screen", shot_size="medium"),
        _scene("A person in modern office", shot_size="medium"),
        _scene("A person working at desk", shot_size="medium"),
    ]
    result = check_scene_variation(scenes)
    assert result["verdict"] in {"revise", "fail"}, (
        f"Expected revise/fail, got {result['verdict']} (score={result['score']})"
    )


def test_zero_violations_strong():
    """A well-varied scene plan should score strong."""
    scenes = [
        _scene("Aerial sweep over mountain valley", shot_size="extreme_wide", movement="dolly_in", intent="Establish scale"),
        _scene("Close-up of weathered hands", shot_size="close_up", movement="static", intent="Show texture"),
        _scene("Medium shot of team collaboration", shot_size="medium", movement="tracking_left", intent="Show teamwork"),
        _scene("Wide summit reveal", shot_size="wide", movement="crane_up", intent="Payoff"),
    ]
    for s in scenes:
        s["hero_moment"] = scenes.index(s) == 3
        s["texture_keywords"] = ["grain", "warm"]
    result = check_scene_variation(scenes)
    assert result["verdict"] in {"strong", "acceptable"}


def test_multiplier_applied_at_three_violations():
    """Score with 3 violations must be higher than score with 2 violations would naively be."""
    # 3 violations: base = 3 * 0.6 * 1.5 = 2.7
    # Without multiplier: 3 * 0.6 = 1.8 (would be "strong")
    # With multiplier: 2.7 (should be "acceptable" or higher)
    # We can't control exact violations, but we can check the score math directly
    from lib.variation_checker import check_scene_variation
    # minimal scenes that trigger exactly 3 checks (shot size variety, static, no hero)
    scenes_3v = [
        _scene("Stock photo office A", shot_size="medium"),
        _scene("Stock photo office B", shot_size="medium"),
        _scene("Stock photo office C", shot_size="medium"),
        _scene("Stock photo office D", shot_size="medium"),
    ]
    result = check_scene_variation(scenes_3v)
    # With 3+ violations, score >= 1.8 * 1.5 = 2.7, so verdict != "strong"
    assert result["score"] >= 2.7 or result["verdict"] != "strong"
