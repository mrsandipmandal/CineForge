"""Contract tests for CineForge Universal Interactive Production Wizard."""

import pytest
from lib.production_wizard import (
    MANDATORY_DURATION_OPTIONS,
    ProductionWizard,
    SelectionMode,
    WizardMode,
    extract_duration_from_prompt,
    validate_custom_duration,
)
from schemas.artifacts import validate_artifact


def test_mandatory_duration_options_complete():
    """Verify all 7 mandatory duration options are present."""
    expected = [
        "15–30 seconds",
        "30–60 seconds",
        "1–3 minutes",
        "3–5 minutes",
        "5–10 minutes",
        "Custom",
        "Skip — Let AI Decide",
    ]
    assert MANDATORY_DURATION_OPTIONS == expected


def test_prompt_contains_duration_does_not_ask_again():
    """When the user prompt includes a clear duration, the wizard should not ask again."""
    prompts_with_duration = [
        "Make a 60-second explainer about quantum computing",
        "Create a 10 second cinematic teaser for Mars rover",
        "I need a 2-minute video about photosynthesis",
        "Generate a 30s TikTok reel",
    ]
    for prompt in prompts_with_duration:
        wiz = ProductionWizard(mode=WizardMode.GUIDED, prompt=prompt)
        assert not wiz.should_ask_duration(), f"Failed for prompt: {prompt}"
        assert "duration" in wiz.decisions
        assert wiz.decisions["duration"].selection_mode == SelectionMode.USER_SELECTED


def test_duration_absent_shows_all_choices():
    """When duration is absent from prompt, wizard asks and provides all required options."""
    wiz = ProductionWizard(mode=WizardMode.GUIDED, prompt="Make a video about black holes")
    assert wiz.should_ask_duration()
    options = wiz.get_duration_options()
    assert len(options) == 7
    assert "15–30 seconds" in options
    assert "30–60 seconds" in options
    assert "1–3 minutes" in options
    assert "3–5 minutes" in options
    assert "5–10 minutes" in options
    assert "Custom" in options
    assert "Skip — Let AI Decide" in options


def test_custom_duration_validation():
    """Custom duration validation rejects invalid values and accepts valid numbers/formats."""
    # Valid
    valid, sec, text = validate_custom_duration("45 seconds")
    assert valid and sec == 45.0

    valid, sec, text = validate_custom_duration(90)
    assert valid and sec == 90.0

    valid, sec, text = validate_custom_duration("2 minutes")
    assert valid and sec == 120.0

    # Invalid
    valid, _, err = validate_custom_duration(-5)
    assert not valid
    assert "greater than 0" in err

    valid, _, err = validate_custom_duration("invalid format")
    assert not valid

    valid, _, err = validate_custom_duration(5000)
    assert not valid
    assert "exceed" in err


def test_handle_custom_duration_selection():
    """Selecting Custom with valid duration records user_selected duration."""
    wiz = ProductionWizard(mode=WizardMode.GUIDED, prompt="Explainer")
    rec = wiz.handle_duration_selection("Custom", custom_input="45 seconds")
    assert rec.selection_mode == SelectionMode.USER_SELECTED
    assert "45" in str(rec.selected_value)
    assert not wiz.should_ask_duration()


def test_skip_triggers_ai_decision():
    """Selecting 'Skip — Let AI Decide' triggers a reasoned AI decision record."""
    wiz = ProductionWizard(mode=WizardMode.GUIDED, prompt="A teaser for a sci-fi movie")
    rec = wiz.handle_duration_selection("Skip — Let AI Decide")
    assert rec.selection_mode == SelectionMode.AI_DECIDED
    assert rec.selected_value in ["15–30 seconds", "30–60 seconds", "1–3 minutes", "3–5 minutes", "5–10 minutes"]
    assert rec.decision_reason
    assert len(rec.constraints_considered) > 0
    assert 0.0 <= rec.confidence <= 1.0


def test_previous_answers_survive_checkpoint_resume():
    """Serialized wizard state preserves all decisions and answers upon resume."""
    wiz = ProductionWizard(mode=WizardMode.ADVANCED, prompt="Tell me about Mars")
    wiz.answers["purpose"] = "science_education"
    wiz.answers["platform"] = "youtube"
    wiz.handle_duration_selection("1–3 minutes")

    serialized = wiz.serialize_state()
    resumed = ProductionWizard.resume_state(serialized)

    assert resumed.mode == WizardMode.ADVANCED
    assert resumed.prompt == "Tell me about Mars"
    assert resumed.answers["purpose"] == "science_education"
    assert resumed.answers["duration"] == "1–3 minutes"
    assert "duration" in resumed.decisions
    assert resumed.decisions["duration"].selection_mode == SelectionMode.USER_SELECTED
    assert len(resumed.decision_log) == len(wiz.decision_log)


def test_decision_log_is_append_only():
    """Adding decisions always appends to decision_log without mutating earlier entries."""
    wiz = ProductionWizard(mode=WizardMode.GUIDED, prompt="Test video")
    assert len(wiz.decision_log) == 0

    wiz.handle_duration_selection("30–60 seconds")
    assert len(wiz.decision_log) == 1
    first_id = wiz.decision_log[0]["decision_id"]

    # Re-evaluating or adding another decision
    from lib.production_wizard import DecisionRecord
    rec2 = DecisionRecord(
        category="render_runtime_selection",
        subject="Composition engine",
        selection_mode=SelectionMode.USER_SELECTED,
        selected_value="remotion",
        decision_reason="React-based explainer",
    )
    wiz.record_decision("render_runtime", rec2)

    assert len(wiz.decision_log) == 2
    assert wiz.decision_log[0]["decision_id"] == first_id
    assert wiz.decision_log[1]["decision_id"] != first_id


def test_decision_log_validates_against_schema():
    """All generated decision log entries must validate against decision_log.schema.json."""
    wiz = ProductionWizard(mode=WizardMode.GUIDED, prompt="Test")
    wiz.handle_duration_selection("Skip — Let AI Decide")

    payload = {
        "version": "1.0",
        "project_id": "test-project-123",
        "decisions": wiz.decision_log,
    }
    # Validate against actual JSON schema
    validate_artifact("decision_log", payload)
