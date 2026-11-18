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
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from tools.tool_registry import registry

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
    "local_diffusion",
    "pixabay",
    "pexels",
]

# Free / quota-tier vs paid credit providers
PAID_PROVIDERS = {"openai", "bfl", "fal_flux", "replicate", "atlas", "kling"}

IMAGE_PROVIDER_METADATA = {
    "google_imagen": {
        "label": "Google Imagen",
        "tool_name": "google_imagen",
        "is_paid": False,
        "is_primary": True,
        "description": "Primary photorealistic image generation (gemini-3.1-flash-image / Imagen 3).",
    },
    "fal_flux": {
        "label": "fal.ai FLUX",
        "tool_name": "flux_image",
        "is_paid": True,
        "is_primary": False,
        "description": "Secondary high-speed FLUX.1 / FLUX.2 on fal.ai.",
    },
    "replicate": {
        "label": "Replicate FLUX",
        "tool_name": "flux3_replicate_image",
        "is_paid": True,
        "is_primary": False,
        "description": "Tertiary cloud diffusion provider for FLUX & open models.",
    },
    "bfl": {
        "label": "Black Forest Labs (BFL)",
        "tool_name": "bfl_image",
        "is_paid": True,
        "is_primary": False,
        "description": "Direct BFL API for FLUX.1 [pro] and [dev].",
    },
    "atlas": {
        "label": "Atlas Cloud",
        "tool_name": "atlas_image",
        "is_paid": True,
        "is_primary": False,
        "description": "Multi-model cloud gateway (Seedream 5.0, GPT Image 2, Nano Banana).",
    },
    "dashscope": {
        "label": "DashScope (Qwen-Image)",
        "tool_name": "dashscope_image",
        "is_paid": False,
        "is_primary": False,
        "description": "Alibaba Cloud Bailian Qwen-Image-2.0-Pro text-to-image.",
    },
    "comfyui": {
        "label": "ComfyUI",
        "tool_name": "comfyui_image",
        "is_paid": False,
        "is_primary": False,
        "description": "Local GPU diffusion workflow server (free, offline).",
    },
    "kling": {
        "label": "Kling Official Image",
        "tool_name": "kling_official_image",
        "is_paid": True,
        "is_primary": False,
        "description": "Direct Kling v1.5 / v2.0 image generation API.",
    },
    "openai": {
        "label": "Official OpenAI Image API",
        "tool_name": "openai_image",
        "is_paid": True,
        "is_primary": False,
        "description": "Commercial DALL-E 3 API (platform.openai.com).",
    },
    "local_diffusion": {
        "label": "Local Diffusion (Low-VRAM)",
        "tool_name": "local_diffusion",
        "is_paid": False,
        "is_primary": False,
        "description": "Offline diffusers fallback optimized for 4GB RTX 3050 hardware.",
    },
    "pixabay": {
        "label": "Pixabay Stock",
        "tool_name": "pixabay_image",
        "is_paid": False,
        "is_primary": False,
        "description": "Free royalty-free stock photography library.",
    },
    "pexels": {
        "label": "Pexels Stock",
        "tool_name": "pexels_image",
        "is_paid": False,
        "is_primary": False,
        "description": "Free high-resolution stock photography.",
    },
}

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
        "last_fallback_event": None,
    }


def get_image_status_summary() -> Dict[str, Any]:
    cfg = load_image_config()
    providers = []
    
    # Get available tools from registry
    available_tools = registry.get_by_capability("image_generation")
    available_tool_names = {t.name for t in available_tools}
    
    for p_key in cfg["provider_priority"]:
        meta = IMAGE_PROVIDER_METADATA.get(p_key, {"label": p_key, "is_paid": False, "is_primary": False, "description": ""})
        is_enabled = cfg["enabled_providers"].get(p_key, True)
        is_ready = meta["tool_name"] in available_tool_names
        
        providers.append({
            "key": p_key,
            "label": meta["label"],
            "is_paid": meta["is_paid"],
            "is_primary": meta["is_primary"],
            "description": meta["description"],
            "enabled": is_enabled,
            "ready": is_ready,
        })
        
    # Determine current active
    current_active = None
    for p in providers:
        if p["enabled"] and p["ready"]:
            current_active = p
            break
            
    fallback_status = "ready"
    if current_active and current_active["key"] != cfg["primary_provider"]:
        fallback_status = f"fallback_active ({current_active['label']})"
    elif not current_active:
        fallback_status = "no_providers_available"
        
    return {
        "primary_provider": cfg["primary_provider"],
        "primary_provider_key": "google_imagen", # Based on R1 report
        "provider_priority": cfg["provider_priority"],
        "enabled_providers": cfg["enabled_providers"],
        "auto_fallback": cfg["auto_fallback"],
        "manual_mode": cfg["manual_mode"],
        "providers": providers,
        "last_fallback_event": cfg.get("last_fallback_event"),
        "fallback_status": fallback_status,
        "discovered_providers": list(IMAGE_PROVIDER_METADATA.keys()),
        "discovered_tools": list(available_tool_names),
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

    # Ensure google_imagen is present in priority list
    if not cfg.get("provider_priority"):
        cfg["provider_priority"] = list(DEFAULT_IMAGE_PRIORITY)
    elif "google_imagen" not in cfg["provider_priority"]:
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


def delegate_to_local_diffusion(
    inputs: Dict[str, Any],
    reason: str = "Primary image providers unavailable",
    primary_provider: Optional[str] = None,
) -> Dict[str, Any]:
    """Delegate image generation to local diffusion fallback with low-VRAM guard."""
    from tools.graphics.local_diffusion import generate_local_diffusion_fallback

    cfg = load_image_config()
    
    primary = primary_provider or cfg.get("primary_provider", "google_imagen")
    record_image_fallback_event(primary=primary, reason=reason, fallback="local_diffusion")

    prompt = inputs.get("prompt", "")
    out_path = inputs.get("output_path")
    return generate_local_diffusion_fallback(
        prompt=prompt,
        output_path=out_path,
        negative_prompt=inputs.get("negative_prompt", ""),
        width=inputs.get("width", 512),
        height=inputs.get("height", 512),
        seed=inputs.get("seed"),
        model=inputs.get("model", "stabilityai/stable-diffusion-2-1-base"),
        low_vram=cfg.get("low_vram_guard", True),
    )


def record_image_fallback_event(primary: str, reason: str, fallback: str) -> None:
    """Log and record provider fallback events for Backlot observability."""
    import time

    logger.info(
        "IMAGE FALLBACK EVENT: Primary [%s] failed (%s). Switched to [%s].",
        primary,
        reason,
        fallback,
    )
    event = {
        "timestamp": time.time(),
        "primary_provider": primary,
        "fallback_provider": fallback,
        "reason": reason,
    }
    cfg = load_image_config()
    cfg["last_fallback_event"] = event
    try:
        save_image_config(cfg)
    except Exception as exc:
        logger.warning("Failed to persist image fallback event: %s", exc)
