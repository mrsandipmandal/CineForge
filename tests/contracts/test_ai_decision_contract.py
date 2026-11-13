"""Contract tests for AI Decision handling, selection modes, and payment safety."""

import pytest
from lib.production_wizard import (
    DecisionRecord,
    ProductionWizard,
    SelectionMode,
    WizardMode,
    ai_decide_duration,
)


def test_selection_modes_are_distinct():
    """Verify that all 6 selection states are distinct and defined."""
    modes = {
        SelectionMode.USER_SELECTED,
        SelectionMode.AI_DECIDED,
        SelectionMode.NOT_APPLICABLE,
        SelectionMode.DISABLED,
        SelectionMode.UNAVAILABLE,
        SelectionMode.PENDING_USER_INPUT,
    }
    assert len(modes) == 6
    assert SelectionMode.DISABLED != SelectionMode.AI_DECIDED
    assert SelectionMode.NOT_APPLICABLE != SelectionMode.UNAVAILABLE


def test_ai_decision_never_silently_authorizes_payment():
    """AI decisions must never have user_approved=True or authorize paid actions automatically."""
    rec = ai_decide_duration(prompt_intent="Epic Hollywood trailer with expensive visual effects")
    assert rec.selection_mode == SelectionMode.AI_DECIDED
    assert not rec.user_approved
    assert not rec.requires_payment

    # Verify that DecisionRecord defaults ensure safety
    record = DecisionRecord(
        category="provider_selection",
        subject="Image generation provider",
        selection_mode=SelectionMode.AI_DECIDED,
        selected_value="flux_pro",
        decision_reason="Highest cinematic quality",
        confidence=0.85,
        requires_payment=True,
    )
    # Even if requires_payment is True, user_approved MUST be False until explicitly approved
    assert not record.user_approved


def test_explicit_disable_vs_ai_decision():
    """Explicitly disabling a feature must have selection_mode=DISABLED, not AI_DECIDED."""
    rec_disabled = DecisionRecord(
        category="enhancement_selection",
        subject="AI Human Enhancer",
        selection_mode=SelectionMode.DISABLED,
        selected_value="disabled",
        decision_reason="User explicitly chose to disable human enhancement",
    )
    rec_ai = DecisionRecord(
        category="enhancement_selection",
        subject="AI Human Enhancer",
        selection_mode=SelectionMode.AI_DECIDED,
        selected_value="natural",
        decision_reason="AI decided natural enhancement profile based on talking-head footage",
    )
    assert rec_disabled.selection_mode == SelectionMode.DISABLED
    assert rec_ai.selection_mode == SelectionMode.AI_DECIDED
    assert rec_disabled.selection_mode != rec_ai.selection_mode


def test_not_applicable_vs_unavailable():
    """Not applicable (no human subject in footage) differs from unavailable (missing local model)."""
    rec_na = DecisionRecord(
        category="enhancement_selection",
        subject="AI Human Enhancer",
        selection_mode=SelectionMode.NOT_APPLICABLE,
        selected_value="not_applicable",
        decision_reason="No human face or subject detected in scene footage",
    )
    rec_unavail = DecisionRecord(
        category="enhancement_selection",
        subject="AI Human Enhancer",
        selection_mode=SelectionMode.UNAVAILABLE,
        selected_value="unavailable",
        decision_reason="GFPGAN / CodeFormer model weights not installed on local host",
    )
    assert rec_na.selection_mode == SelectionMode.NOT_APPLICABLE
    assert rec_unavail.selection_mode == SelectionMode.UNAVAILABLE
    assert rec_na.selection_mode != rec_unavail.selection_mode


def test_ai_decision_records_reason_and_confidence():
    """All AI decisions must record explicit reasoning, constraints, and valid confidence."""
    rec = ai_decide_duration(
        prompt_intent="A quick TikTok reel for young audience",
        platform="tiktok",
        purpose="entertainment",
    )
    assert rec.selection_mode == SelectionMode.AI_DECIDED
    assert len(rec.decision_reason) > 10
    assert "user_prompt_intent" in rec.constraints_considered
    assert "platform_tiktok" in rec.constraints_considered
    assert 0.0 <= rec.confidence <= 1.0
    assert rec.selected_value in ["30–60 seconds", "15–30 seconds"]
