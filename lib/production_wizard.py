"""Universal Interactive Production Wizard for CineForge.

Provides progressive intake, decision resolution, duration extraction,
and AI decision reasoning with strict contract validation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class WizardMode(str, Enum):
    QUICK = "quick"
    GUIDED = "guided"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SelectionMode(str, Enum):
    USER_SELECTED = "user_selected"
    AI_DECIDED = "ai_decided"
    NOT_APPLICABLE = "not_applicable"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"
    PENDING_USER_INPUT = "pending_user_input"


MANDATORY_DURATION_OPTIONS = [
    "15–30 seconds",
    "30–60 seconds",
    "1–3 minutes",
    "3–5 minutes",
    "5–10 minutes",
    "Custom",
    "Skip — Let AI Decide",
]

# Standard duration band midpoints / estimates in seconds
DURATION_BAND_SECONDS = {
    "15–30 seconds": 20.0,
    "30–60 seconds": 45.0,
    "1–3 minutes": 120.0,
    "3–5 minutes": 240.0,
    "5–10 minutes": 420.0,
}


@dataclass
class DecisionRecord:
    """A single production decision with full audit provenance."""
    category: str
    subject: str
    selection_mode: SelectionMode
    selected_value: Any
    decision_reason: str
    constraints_considered: list[str] = field(default_factory=list)
    confidence: float = 1.0
    options_considered: list[dict[str, Any]] = field(default_factory=list)
    user_visible: bool = True
    user_approved: bool = False
    requires_payment: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "subject": self.subject,
            "selection_mode": self.selection_mode.value if isinstance(self.selection_mode, SelectionMode) else str(self.selection_mode),
            "selected_value": self.selected_value,
            "decision_reason": self.decision_reason,
            "constraints_considered": list(self.constraints_considered),
            "confidence": round(float(self.confidence), 2),
            "options_considered": self.options_considered,
            "user_visible": self.user_visible,
            "user_approved": self.user_approved,
            "requires_payment": self.requires_payment,
        }

    def to_decision_log_entry(self, decision_id: str, stage: str = "proposal") -> dict[str, Any]:
        """Convert this decision into a schema-valid decision_log entry."""
        options = self.options_considered
        if not options:
            options = [
                {
                    "option_id": str(self.selected_value),
                    "label": str(self.selected_value),
                    "score": 1.0,
                    "reason": self.decision_reason,
                }
            ]

        return {
            "decision_id": decision_id,
            "stage": stage,
            "category": self.category,
            "subject": self.subject,
            "options_considered": options,
            "selected": str(self.selected_value),
            "reason": self.decision_reason,
            "user_visible": self.user_visible,
            "user_approved": self.user_approved,
            "confidence": min(1.0, max(0.0, round(float(self.confidence), 2))),
        }


def extract_duration_from_prompt(prompt: str) -> Optional[DecisionRecord]:
    """Inspect user prompt for an explicit duration expression.

    If found, returns a DecisionRecord with selection_mode=USER_SELECTED so the wizard
    does not ask the user for duration again.
    """
    if not prompt:
        return None

    # Pattern for seconds: e.g. "60-second", "60 seconds", "60s", "10 sec", "15-30 seconds"
    # Pattern for minutes: e.g. "2-minute", "3 minutes", "2 mins", "1.5 min"
    p_sec = re.search(r'\b(?:(\d+(?:\.\d+)?)\s*(?:-|to)\s*)?(\d+(?:\.\d+)?)[\s-]*(?:seconds?|secs?|s)\b', prompt, re.IGNORECASE)
    if p_sec:
        low = p_sec.group(1)
        high = float(p_sec.group(2))
        if low:
            val_str = f"{low}–{p_sec.group(2)} seconds"
            sec = (float(low) + high) / 2.0
        else:
            val_str = f"{p_sec.group(2)} seconds"
            sec = high

        return DecisionRecord(
            category="concept_selection",
            subject="Target video duration",
            selection_mode=SelectionMode.USER_SELECTED,
            selected_value=val_str,
            decision_reason=f"Explicitly specified in prompt: '{p_sec.group(0)}'",
            constraints_considered=["user_prompt"],
            confidence=1.0,
            options_considered=[{
                "option_id": val_str,
                "label": val_str,
                "score": 1.0,
                "reason": "Direct user prompt request",
            }],
        )

    p_min = re.search(r'\b(?:(\d+(?:\.\d+)?)\s*(?:-|to)\s*)?(\d+(?:\.\d+)?)[\s-]*(?:minutes?|mins?|m)\b', prompt, re.IGNORECASE)
    if p_min:
        low = p_min.group(1)
        high = float(p_min.group(2))
        if low:
            val_str = f"{low}–{p_min.group(2)} minutes"
            sec = ((float(low) + high) / 2.0) * 60.0
        else:
            val_str = f"{p_min.group(2)} minutes"
            sec = high * 60.0

        return DecisionRecord(
            category="concept_selection",
            subject="Target video duration",
            selection_mode=SelectionMode.USER_SELECTED,
            selected_value=val_str,
            decision_reason=f"Explicitly specified in prompt: '{p_min.group(0)}'",
            constraints_considered=["user_prompt"],
            confidence=1.0,
            options_considered=[{
                "option_id": val_str,
                "label": val_str,
                "score": 1.0,
                "reason": "Direct user prompt request",
            }],
        )

    return None


def validate_custom_duration(value: str | float | int) -> tuple[bool, float, str]:
    """Validate a custom duration input.

    Returns (is_valid, duration_in_seconds, formatted_string_or_error).
    """
    if isinstance(value, (int, float)):
        sec = float(value)
        if sec <= 0:
            return False, 0.0, "Duration must be greater than 0 seconds."
        if sec > 3600:
            return False, 0.0, "Duration cannot exceed 60 minutes (3600 seconds)."
        return True, sec, f"{int(sec) if sec.is_integer() else sec} seconds"

    if not isinstance(value, str) or not value.strip():
        return False, 0.0, "Custom duration cannot be empty."

    cleaned = value.strip().lower()

    # Try matching seconds or minutes
    m_sec = re.match(r'^(\d+(?:\.\d+)?)\s*(?:seconds?|secs?|s)?$', cleaned)
    if m_sec:
        sec = float(m_sec.group(1))
        if sec <= 0:
            return False, 0.0, "Duration must be greater than 0 seconds."
        if sec > 3600:
            return False, 0.0, "Duration cannot exceed 3600 seconds."
        return True, sec, f"{int(sec) if sec.is_integer() else sec} seconds"

    m_min = re.match(r'^(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|m)$', cleaned)
    if m_min:
        sec = float(m_min.group(1)) * 60.0
        if sec <= 0:
            return False, 0.0, "Duration must be greater than 0 seconds."
        if sec > 3600:
            return False, 0.0, "Duration cannot exceed 60 minutes."
        return True, sec, f"{m_min.group(1)} minutes ({int(sec)}s)"

    return False, 0.0, f"Unrecognized duration format: '{value}'. Specify e.g. '45 seconds' or '2 minutes'."


def ai_decide_duration(
    prompt_intent: str = "",
    platform: Optional[str] = None,
    purpose: Optional[str] = None,
    style: Optional[str] = None,
) -> DecisionRecord:
    """Make a reasoned AI decision for duration when user chose 'Skip — Let AI Decide'.

    Never silently authorizes paid operations.
    """
    intent_lower = (prompt_intent or "").lower()
    platform_lower = (platform or "").lower()
    purpose_lower = (purpose or "").lower()

    # Constraints considered
    constraints = ["user_prompt_intent"]
    if platform:
        constraints.append(f"platform_{platform}")
    if purpose:
        constraints.append(f"purpose_{purpose}")

    # Platform-specific heuristics
    if any(p in platform_lower for p in ["tiktok", "shorts", "reels"]):
        selected = "30–60 seconds"
        reason = f"Short-form platform ({platform}) optimal engagement is typically 30–60 seconds."
        confidence = 0.92
    elif any(k in intent_lower for k in ["trailer", "teaser", "hype", "promo"]):
        selected = "15–30 seconds"
        reason = "Teaser/trailer format achieves highest impact with a punchy 15–30 second pacing."
        confidence = 0.88
    elif any(k in purpose_lower for k in ["documentary", "deep_dive", "history"]):
        selected = "3–5 minutes"
        reason = "Documentary/historical narrative requires sufficient runtime for beat development and reveals."
        confidence = 0.85
    elif any(k in intent_lower for k in ["explainer", "tutorial", "science"]):
        selected = "1–3 minutes"
        reason = "Educational/explainer concepts best balance audience retention with depth at 1–3 minutes."
        confidence = 0.90
    else:
        # Default balanced choice
        selected = "1–3 minutes"
        reason = "Standard 1–3 minute duration provides enough headroom for narrative pacing and scene variation."
        confidence = 0.80

    options = [
        {"option_id": opt, "label": opt, "score": 0.95 if opt == selected else 0.5, "reason": "Evaluated band"}
        for opt in MANDATORY_DURATION_OPTIONS if opt != "Custom" and opt != "Skip — Let AI Decide"
    ]

    return DecisionRecord(
        category="concept_selection",
        subject="Target video duration",
        selection_mode=SelectionMode.AI_DECIDED,
        selected_value=selected,
        decision_reason=reason,
        constraints_considered=constraints,
        confidence=confidence,
        options_considered=options,
        user_visible=True,
        user_approved=False,
        requires_payment=False,  # Duration decision does not authorize payment
    )


class ProductionWizard:
    """Manages progressive intake questions, decisions, and resume state."""

    def __init__(
        self,
        mode: WizardMode = WizardMode.GUIDED,
        prompt: str = "",
        initial_answers: Optional[dict[str, Any]] = None,
    ) -> None:
        self.mode = mode
        self.prompt = prompt
        self.decisions: dict[str, DecisionRecord] = {}
        self.answers: dict[str, Any] = dict(initial_answers or {})
        self.decision_log: list[dict[str, Any]] = []
        self._next_decision_id = 1

        # Check if duration is already in prompt
        if self.prompt:
            extracted = extract_duration_from_prompt(self.prompt)
            if extracted:
                self.record_decision("duration", extracted)

    def record_decision(self, key: str, record: DecisionRecord) -> None:
        """Record a decision and append to the immutable decision log."""
        self.decisions[key] = record
        self.answers[key] = record.selected_value

        decision_id = f"d-{self._next_decision_id:03d}"
        self._next_decision_id += 1
        entry = record.to_decision_log_entry(decision_id=decision_id)
        self.decision_log.append(entry)

    def should_ask_duration(self) -> bool:
        """Returns True if duration has not been answered or extracted."""
        return "duration" not in self.decisions

    def get_duration_options(self) -> list[str]:
        """Returns the mandatory duration choices."""
        return list(MANDATORY_DURATION_OPTIONS)

    def handle_duration_selection(
        self,
        selection: str,
        custom_input: Optional[str] = None,
    ) -> DecisionRecord:
        """Handle user's duration selection or Skip."""
        clean = selection.strip()

        if clean == "Skip — Let AI Decide" or clean.lower() in {"skip", "ai", "let ai decide"}:
            record = ai_decide_duration(
                prompt_intent=self.prompt,
                platform=self.answers.get("platform"),
                purpose=self.answers.get("purpose"),
            )
            self.record_decision("duration", record)
            return record

        if clean == "Custom" or custom_input:
            val_to_check = custom_input if custom_input else clean
            valid, sec, formatted = validate_custom_duration(val_to_check)
            if not valid:
                raise ValueError(formatted)

            record = DecisionRecord(
                category="concept_selection",
                subject="Target video duration",
                selection_mode=SelectionMode.USER_SELECTED,
                selected_value=formatted,
                decision_reason=f"User specified custom duration: {formatted}",
                constraints_considered=["user_selection"],
                confidence=1.0,
                options_considered=[{
                    "option_id": formatted,
                    "label": formatted,
                    "score": 1.0,
                    "reason": "User custom specification",
                }],
            )
            self.record_decision("duration", record)
            return record

        # Match one of the preset bands
        matched = None
        for opt in MANDATORY_DURATION_OPTIONS:
            if opt in clean or clean in opt:
                matched = opt
                break

        if not matched:
            raise ValueError(
                f"Invalid duration choice '{selection}'. Must be one of: {MANDATORY_DURATION_OPTIONS}"
            )

        record = DecisionRecord(
            category="concept_selection",
            subject="Target video duration",
            selection_mode=SelectionMode.USER_SELECTED,
            selected_value=matched,
            decision_reason=f"User selected duration band: {matched}",
            constraints_considered=["user_selection"],
            confidence=1.0,
            options_considered=[{
                "option_id": matched,
                "label": matched,
                "score": 1.0,
                "reason": "User choice from menu",
            }],
        )
        self.record_decision("duration", record)
        return record

    def serialize_state(self) -> dict[str, Any]:
        """Serialize current wizard state for checkpoint persistence."""
        return {
            "mode": self.mode.value,
            "prompt": self.prompt,
            "answers": self.answers,
            "decisions": {k: d.to_dict() for k, d in self.decisions.items()},
            "decision_log": self.decision_log,
        }

    @classmethod
    def resume_state(cls, data: dict[str, Any]) -> ProductionWizard:
        """Resume wizard from persisted checkpoint metadata."""
        mode = WizardMode(data.get("mode", WizardMode.GUIDED.value))
        prompt = data.get("prompt", "")
        answers = data.get("answers", {})
        wizard = cls(mode=mode, prompt="", initial_answers=answers)
        wizard.prompt = prompt

        decisions_data = data.get("decisions", {})
        for k, d_dict in decisions_data.items():
            record = DecisionRecord(
                category=d_dict["category"],
                subject=d_dict["subject"],
                selection_mode=SelectionMode(d_dict["selection_mode"]),
                selected_value=d_dict["selected_value"],
                decision_reason=d_dict["decision_reason"],
                constraints_considered=d_dict.get("constraints_considered", []),
                confidence=d_dict.get("confidence", 1.0),
                options_considered=d_dict.get("options_considered", []),
                user_visible=d_dict.get("user_visible", True),
                user_approved=d_dict.get("user_approved", False),
                requires_payment=d_dict.get("requires_payment", False),
            )
            wizard.decisions[k] = record

        wizard.decision_log = list(data.get("decision_log", []))
        wizard._next_decision_id = len(wizard.decision_log) + 1
        return wizard
