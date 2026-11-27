"""CineForge Centralized TTS Provider Priority & Fallback Configuration.

Defines the system-wide strict TTS provider priority:
1. OpenAI.fm — Primary
2. Kokoro TTS — First fallback
3. VoxCPM2 — Second fallback
4. Other configured free/open-source TTS providers (Piper, MMS, Indic, F5)
5. Official OpenAI TTS API — Last resort, optional and disabled unless explicitly enabled.

Manages persistent configuration, runtime overrides, paid-provider gating,
and UI state reporting for Backlot.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.paths import get_backlot_state_dir, get_workspace_root

logger = logging.getLogger(__name__)

REPO_ROOT = get_workspace_root()
CONFIG_FILE = get_backlot_state_dir() / "tts_settings.json"
_DEFAULT_CONFIG_FILE = CONFIG_FILE


def _get_config_file() -> Path:
    """Return active TTS config file, respecting monkeypatched CONFIG_FILE in tests."""
    if CONFIG_FILE != _DEFAULT_CONFIG_FILE:
        return CONFIG_FILE
    return get_backlot_state_dir() / "tts_settings.json"

# Strict system default provider priority
DEFAULT_PRIORITY: List[str] = [
    "openaifm",
    "kokoro",
    "voxcpm2",
    "piper",
    "indic",
    "mms",
    "f5",
    "openai",
]

# Free vs Paid provider classification
PAID_PROVIDERS = {"openai", "elevenlabs", "azure", "doubao", "dashscope", "kling", "fish_audio", "cartesia"}

PROVIDER_METADATA = {
    "openaifm": {
        "label": "OpenAI.fm",
        "tool_name": "openaifm_tts",
        "is_paid": False,
        "is_primary": True,
        "description": "Primary high-quality TTS engine with Fable voice, instructions, and multilingual support.",
        "endpoint": "https://www.openai.fm/api/generate",
    },
    "kokoro": {
        "label": "Kokoro TTS",
        "tool_name": "kokoro_tts",
        "is_paid": False,
        "is_primary": False,
        "description": "First fallback — local 82M open-source model with 54 voices.",
    },
    "voxcpm2": {
        "label": "VoxCPM2",
        "tool_name": "voxcpm2_tts",
        "is_paid": False,
        "is_primary": False,
        "description": "Second fallback — flow-matching voice cloning and synthesis (Kaggle/CUDA).",
    },
    "piper": {
        "label": "Piper TTS",
        "tool_name": "piper_tts",
        "is_paid": False,
        "is_primary": False,
        "description": "Fast local offline neural text-to-speech fallback.",
    },
    "indic": {
        "label": "Indic TTS",
        "tool_name": "indic_tts",
        "is_paid": False,
        "is_primary": False,
        "description": "Specialized Indian language TTS models (Hindi, Bengali, etc.).",
    },
    "mms": {
        "label": "Meta MMS TTS",
        "tool_name": "mms_tts",
        "is_paid": False,
        "is_primary": False,
        "description": "Massively Multilingual Speech local offline synthesis.",
    },
    "f5": {
        "label": "F5-TTS",
        "tool_name": "f5_tts",
        "is_paid": False,
        "is_primary": False,
        "description": "Flow-matching non-autoregressive speech synthesis.",
    },
    "openai": {
        "label": "Official OpenAI TTS API",
        "tool_name": "openai_tts",
        "is_paid": True,
        "is_primary": False,
        "description": "Commercial paid API (platform.openai.com) — disabled by default unless explicitly allowed.",
    },
    "elevenlabs": {
        "label": "ElevenLabs",
        "tool_name": "elevenlabs_tts",
        "is_paid": True,
        "is_primary": False,
        "description": "Commercial paid voice cloning and generation API.",
    },
    "azure": {
        "label": "Azure Speech TTS",
        "tool_name": "azure_tts",
        "is_paid": True,
        "is_primary": False,
        "description": "Microsoft Azure Cognitive Services Speech API.",
    },
}


def _default_config() -> Dict[str, Any]:
    return {
        "primary_provider": "openaifm",
        "provider_priority": list(DEFAULT_PRIORITY),
        "enabled_providers": {
            "openaifm": True,
            "kokoro": True,
            "voxcpm2": True,
            "piper": True,
            "indic": True,
            "mms": True,
            "f5": True,
            "openai": False,  # Strictly disabled by default
            "elevenlabs": False,
            "azure": False,
        },
        "allow_paid_providers": False,  # Never silently use paid providers
        "auto_fallback": True,          # Enable automatic fallback
        "manual_mode": False,           # If True, strictly use chosen provider
        "max_retries": 1,
        "timeout_seconds": 20,
        "last_fallback_event": None,
    }


def load_tts_config() -> Dict[str, Any]:
    """Load persistent TTS configuration, falling back to defaults."""
    cfg = _default_config()
    config_file = _get_config_file()
    if config_file.is_file():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    # Merge keys
                    for k, v in saved.items():
                        if k in cfg:
                            if isinstance(cfg[k], dict) and isinstance(v, dict):
                                cfg[k].update(v)
                            else:
                                cfg[k] = v
        except Exception as exc:
            logger.warning("Failed to read %s: %s", config_file, exc)

    # Ensure openaifm is present in priority list
    if not cfg.get("provider_priority"):
        cfg["provider_priority"] = list(DEFAULT_PRIORITY)
    elif "openaifm" not in cfg["provider_priority"]:
        cfg["provider_priority"].insert(0, "openaifm")

    return cfg


def save_tts_config(new_config: Dict[str, Any]) -> Dict[str, Any]:
    """Save updated TTS configuration to disk."""
    current = load_tts_config()
    for k, v in new_config.items():
        if k in current:
            if isinstance(current[k], dict) and isinstance(v, dict):
                current[k].update(v)
            else:
                current[k] = v

    config_file = _get_config_file()
    try:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
    except Exception as exc:
        logger.error("Failed to write %s: %s", config_file, exc)

    return current


def is_paid_provider(provider_or_tool: str) -> bool:
    """Return True if the provider or tool name is a paid service."""
    p = provider_or_tool.lower().replace("_tts", "")
    return p in PAID_PROVIDERS


def get_effective_priority(
    inputs: Optional[Dict[str, Any]] = None,
    allow_paid_override: Optional[bool] = None,
) -> List[str]:
    """Compute the ordered, eligible provider list based on config and request inputs."""
    cfg = load_tts_config()
    inputs = inputs or {}

    # Check for runtime overrides
    has_explicit_paid = "allow_paid" in inputs or "enable_paid_providers" in inputs
    explicit_allow_paid = (
        inputs["allow_paid"]
        if "allow_paid" in inputs
        else inputs.get("enable_paid_providers")
    )
    allow_paid = (
        allow_paid_override
        if allow_paid_override is not None
        else inputs.get("allow_paid", inputs.get("enable_paid_providers", cfg.get("allow_paid_providers", False)))
    )

    priority_list = list(cfg.get("provider_priority", DEFAULT_PRIORITY))
    enabled_map = dict(cfg.get("enabled_providers", {}))

    # Input allowed_providers filter
    allowed_set: Optional[set[str]] = None
    allowed_input = inputs.get("allowed_providers")
    if allowed_input and isinstance(allowed_input, list):
        allowed_set = {str(x).lower().replace("_tts", "") for x in allowed_input}
        priority_list = [p for p in priority_list if p in allowed_set]

    # Explicit preferred_provider
    preferred = inputs.get("preferred_provider")
    explicit_pref: Optional[str] = None
    if preferred and preferred != "auto":
        pref_clean = preferred.lower().replace("_tts", "")
        if allowed_set is None or pref_clean in allowed_set:
            if pref_clean in priority_list:
                priority_list.remove(pref_clean)
            priority_list.insert(0, pref_clean)
            if not (has_explicit_paid and explicit_allow_paid is False):
                explicit_pref = pref_clean

    eligible = []
    for p in priority_list:
        is_paid = is_paid_provider(p)
        # Check paid gate — only an explicitly requested preferred_provider may run
        # when allow_paid was omitted; explicit allow_paid=False blocks everything paid.
        if is_paid and not allow_paid and p != explicit_pref:
            continue
        # Check if enabled
        if not enabled_map.get(p, True):
            # If allow_paid is explicitly True or caller explicitly asked for p, allow it
            if not (is_paid and (allow_paid or p == explicit_pref)):
                continue
        eligible.append(p)

    return eligible


def record_fallback_event(provider_failed: str, reason: str, provider_used: str) -> None:
    """Record the latest fallback event for UI display."""
    import time
    event = {
        "failed_provider": provider_failed,
        "reason": reason,
        "used_provider": provider_used,
        "timestamp": time.time(),
    }
    try:
        cfg = load_tts_config()
        cfg["last_fallback_event"] = event
        save_tts_config(cfg)
    except Exception as exc:
        logger.debug("Could not record fallback event: %s", exc)


def get_tts_status_summary() -> Dict[str, Any]:
    """Return a comprehensive TTS status dictionary for UI display and status reporting."""
    cfg = load_tts_config()
    try:
        from tools.tool_registry import registry
        registry.ensure_discovered()
        discovered_tts = registry.get_by_capability("tts")
    except Exception:
        discovered_tts = []

    discovered_tools = {t.name: t for t in discovered_tts}
    tools_by_provider: Dict[str, Any] = {t.provider: t for t in discovered_tts}

    enabled_map = dict(cfg.get("enabled_providers", {}))
    allow_paid = bool(cfg.get("allow_paid_providers", False))

    providers_info = []
    current_active = None

    for p in cfg.get("provider_priority", DEFAULT_PRIORITY):
        meta = PROVIDER_METADATA.get(p, {})
        tool_name = meta.get("tool_name", f"{p}_tts")
        tool = discovered_tools.get(tool_name) or tools_by_provider.get(p)

        try:
            status_val = tool.get_status().value if tool else "not_installed"
        except Exception:
            status_val = "unavailable"

        is_paid = meta.get("is_paid", is_paid_provider(p))
        is_enabled = bool(enabled_map.get(p, True))

        is_available = (status_val == "available") and is_enabled and (not is_paid or allow_paid)
        if current_active is None and is_available:
            current_active = {
                "key": p,
                "label": meta.get("label", p.capitalize()),
                "tool_name": tool_name,
                "is_primary": meta.get("is_primary", False),
            }

        providers_info.append({
            "key": p,
            "label": meta.get("label", p.capitalize()),
            "tool_name": tool_name,
            "is_primary": meta.get("is_primary", False),
            "is_paid": is_paid,
            "is_enabled": is_enabled,
            "status": status_val,
            "available": is_available,
            "description": meta.get("description", ""),
            "endpoint": meta.get("endpoint"),
        })

    fallback_status = "ready"
    if current_active is None:
        fallback_status = "no_providers_available"
    elif current_active["key"] != "openaifm":
        fallback_status = f"fallback_active ({current_active['label']})"

    return {
        "primary_provider": "OpenAI.fm",
        "primary_provider_key": "openaifm",
        "current_active_provider": current_active,
        "fallback_status": fallback_status,
        "allow_paid_providers": allow_paid,
        "auto_fallback": bool(cfg.get("auto_fallback", True)),
        "manual_mode": bool(cfg.get("manual_mode", False)),
        "provider_priority": cfg.get("provider_priority", DEFAULT_PRIORITY),
        "providers": providers_info,
        "last_fallback_event": cfg.get("last_fallback_event"),
    }

