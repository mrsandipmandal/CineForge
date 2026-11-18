"""CineForge Centralized Image Provider Priority & Fallback Configuration.

Defines the system-wide strict image provider priority:
1. Google Imagen (gemini-3.1-flash-image / Imagen 3) — Primary
2. fal.ai FLUX (FLUX.1 / FLUX.2 on fal.ai) — Secondary
3. Replicate FLUX — Tertiary
4. Black Forest Labs (BFL) Direct API
5. Atlas Cloud (Seedream, GPT Image 2, Nano Banana)
6. DashScope (Qwen-Image)
7. ComfyUI (Local GPU diffusion)
8. Kling Official Image
9. Official OpenAI Image API
10. Free Stock Providers (Pixabay, Pexels)

Manages persistent configuration, quota error detection, image binary validation,
runtime overrides, and Backlot UI integration.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = REPO_ROOT / ".backlot" / "image_settings.json"

# Strict system default image provider priority
DEFAULT_IMAGE_PRIORITY: List[str] = [
    "google_imagen",
    "fal_flux",
    "replicate",
    "bfl",
    "atlas",
    "dashscope",
    "comfyui",
    "kling",
    "openai",
    "pixabay",
    "pexels",
]

# Free / quota-tier vs paid credit providers
PAID_PROVIDERS = {"openai", "bfl", "fal_flux", "replicate", "atlas", "kling"}

# Known quota, rate-limit, and credit exhaustion patterns
QUOTA_ERROR_PATTERNS = (
    "429",
    "resource_exhausted",
    "rate limit",
    "rate_limit",
    "quota exceeded",
    "quota_exceeded",
    "insufficient balance",
    "insufficient credits",
    "out of credits",
    "balance_exhausted",
    "402",
    "payment required",
    "exceeded their current quota",
    "account locked",
    "credit limit reached",
)


def _default_config() -> Dict[str, Any]:
    return {
        "primary_provider": "google_imagen",
        "provider_priority": list(DEFAULT_IMAGE_PRIORITY),
        "enabled_providers": {p: True for p in DEFAULT_IMAGE_PRIORITY},
        "auto_fallback": True,
        "manual_mode": False,
        "max_retries": 1,
        "timeout_seconds": 30,
    }


def load_image_config() -> Dict[str, Any]:
    """Load persistent image configuration, falling back to defaults."""
    cfg = _default_config()
    if CONFIG_FILE.is_file():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    for k, v in saved.items():
                        if k in cfg:
                            if isinstance(cfg[k], dict) and isinstance(v, dict):
                                cfg[k].update(v)
                            else:
                                cfg[k] = v
        except Exception as exc:
            logger.warning("Failed to read %s: %s", CONFIG_FILE, exc)

    # Ensure google_imagen remains at the top of priority unless explicitly customized
    if not cfg["provider_priority"] or cfg["provider_priority"][0] != "google_imagen":
        if "google_imagen" in cfg["provider_priority"]:
            cfg["provider_priority"].remove("google_imagen")
        cfg["provider_priority"].insert(0, "google_imagen")

    return cfg


def save_image_config(new_config: Dict[str, Any]) -> Dict[str, Any]:
    """Save updated image configuration to disk."""
    current = load_image_config()
    for k, v in new_config.items():
        if k in current:
            if isinstance(current[k], dict) and isinstance(v, dict):
                current[k].update(v)
            else:
                current[k] = v

    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
    except Exception as exc:
        logger.error("Failed to write %s: %s", CONFIG_FILE, exc)

    return current


def is_quota_or_rate_limit_error(error: Any) -> bool:
    """Return True if error string or object represents a 429, quota exhaustion, or credit lock."""
    if not error:
        return False
    text = str(error).lower()
    return any(p in text for p in QUOTA_ERROR_PATTERNS)


def validate_image_bytes(data: bytes, min_bytes: int = 100) -> Tuple[bool, str, str]:
    """Inspect raw binary image data for valid headers and non-corrupted content."""
    if not data or len(data) < min_bytes:
        return False, "unknown", f"Image payload too small or empty ({len(data) if data else 0} bytes)"

    # HTML / JSON error response check
    sample_text = data[:256].lower()
    if b"<html" in sample_text or b"<!doctype" in sample_text or b"<body" in sample_text:
        return False, "html_error", "Received HTML error page instead of image"
    if b'{"error"' in sample_text or b'"message"' in sample_text:
        return False, "json_error", "Received JSON error payload instead of image"

    # Check magic headers
    if data.startswith(b"\xff\xd8\xff"):
        return True, "jpeg", "Valid JPEG image"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return True, "png", "Valid PNG image"
    if data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP":
        return True, "webp", "Valid WEBP image"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return True, "gif", "Valid GIF image"

    return False, "unknown", "Unrecognized binary header format"


def validate_image_file(path_str: str | Path, min_bytes: int = 100) -> Tuple[bool, str, str]:
    """Validate that file exists, has sufficient size, and contains valid image binary bytes."""
    path = Path(path_str)
    if not path.is_file():
        return False, "missing", f"Image file not found: {path}"

    try:
        data = path.read_bytes()
        return validate_image_bytes(data, min_bytes=min_bytes)
    except Exception as exc:
        return False, "read_error", f"Error reading file {path}: {exc}"


def get_effective_image_priority(inputs: Optional[Dict[str, Any]] = None) -> List[str]:
    """Compute the ordered, eligible image provider priority list."""
    cfg = load_image_config()
    configured = list(cfg.get("provider_priority", DEFAULT_IMAGE_PRIORITY))
    enabled = cfg.get("enabled_providers", {})

    # Filter out disabled providers
    filtered = [p for p in configured if enabled.get(p, True)]

    # Handle request-level allowed providers
    if inputs and inputs.get("allowed_providers"):
        allowed = set(inputs["allowed_providers"])
        filtered = [p for p in filtered if p in allowed]

    # Handle request-level preferred provider
    if inputs and inputs.get("preferred_provider") and inputs["preferred_provider"] != "auto":
        pref = inputs["preferred_provider"]
        if pref in filtered:
            filtered.remove(pref)
            filtered.insert(0, pref)

    return filtered


def record_image_fallback_event(primary: str, reason: str, fallback: str) -> None:
    """Log and record provider fallback events for Backlot observability."""
    logger.info(
        "IMAGE FALLBACK EVENT: Primary [%s] failed (%s). Switched to [%s].",
        primary,
        reason,
        fallback,
    )
