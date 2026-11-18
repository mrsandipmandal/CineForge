"""Acceptance Tests for CineForge Image Provider Priority & Fallback Engine.

Validates:
1. Default provider priority and configuration persistence.
2. Quota / rate-limit error detection across common provider patterns (429, RESOURCE_EXHAUSTED, 402, balance exhausted).
3. Image file & byte integrity validation (valid headers, reject HTML/JSON errors).
4. Primary provider success -> no fallback occurs.
5. Primary provider fails with quota/rate-limit error -> automatically falls back to secondary provider.
6. Multiple provider failures chain gracefully until an available provider succeeds.
7. All eligible providers fail -> returns clear descriptive error with full audit trail.
8. Auto-fallback disabled (manual mode) -> fails immediately without attempting fallbacks.
9. Backlot config operations (get_config, set_config).
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from lib.image_config import (
    DEFAULT_IMAGE_PRIORITY,
    is_quota_or_rate_limit_error,
    load_image_config,
    save_image_config,
    validate_image_file,
)
from tools.base_tool import BaseTool, ToolResult, ToolRuntime, ToolStability, ToolStatus, ToolTier
from tools.graphics.image_selector import ImageSelector

# Sample valid binary image byte headers
VALID_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + b"\x00" * 400 + b"\xff\xd9"
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 400 + b"IEND\xaeB`\x82"
VALID_WEBP_BYTES = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 400

# Error payloads that should fail validation
INVALID_HTML_BYTES = (
    b"<!DOCTYPE html><html><head><title>502 Bad Gateway</title></head>"
    b"<body><h1>502 Bad Gateway</h1></body></html>"
)
INVALID_JSON_ERROR_BYTES = (
    b'{"error": {"code": 429, "message": "RESOURCE_EXHAUSTED: quota exceeded for model gemini-3.1-flash-image"}}'
)


class DummyMockImageTool(BaseTool):
    """Configurable mock image tool for fallback testing."""

    def __init__(
        self,
        name: str,
        provider: str,
        status: ToolStatus = ToolStatus.AVAILABLE,
        behavior: str = "success",
        fail_error: str = "Generation failed",
        output_bytes: bytes = VALID_JPEG_BYTES,
    ):
        self.name = name
        self.provider = provider
        self.version = "1.0.0"
        self.tier = ToolTier.GENERATE
        self.capability = "image_generation"
        self.stability = ToolStability.PRODUCTION
        self.runtime = ToolRuntime.API
        self._status = status
        self.behavior = behavior
        self.fail_error = fail_error
        self.output_bytes = output_bytes
        self.call_count = 0
        self.last_inputs: dict[str, Any] = {}
        self.input_schema = {
            "type": "object",
            "required": ["prompt"],
            "properties": {
                "prompt": {"type": "string"},
                "width": {"type": "integer"},
                "height": {"type": "integer"},
                "output_path": {"type": "string"},
            },
        }

    def get_status(self) -> ToolStatus:
        return self._status

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        self.call_count += 1
        self.last_inputs = dict(inputs)

        if self.behavior == "exception":
            raise RuntimeError(f"Connection timeout in {self.name}")

        if self.behavior == "fail":
            return ToolResult(success=False, error=self.fail_error)

        # Success case: write valid image file
        out_path = inputs.get("output_path")
        if not out_path:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                f.write(self.output_bytes)
                out_path = f.name
        else:
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(self.output_bytes)

        return ToolResult(
            success=True,
            data={
                "image_path": str(out_path),
                "output_path": str(out_path),
                "width": inputs.get("width", 1080),
                "height": inputs.get("height", 1920),
            },
            artifacts=[str(out_path)],
        )


@pytest.fixture(autouse=True)
def restore_image_config():
    """Ensure clean config state for each test run."""
    initial = load_image_config()
    yield
    save_image_config(initial)


def test_default_image_priority_and_config():
    """Verify default priority order, persistence and retrieval."""
    cfg = load_image_config()
    assert "primary_provider" in cfg
    assert "provider_priority" in cfg
    assert isinstance(cfg["provider_priority"], list)
    assert len(cfg["provider_priority"]) > 0

    # Ensure google_imagen is top of the default priority list
    assert cfg["provider_priority"][0] == "google_imagen"
    assert cfg["auto_fallback"] is True

    # Test saving custom configuration
    saved = save_image_config({"auto_fallback": False, "timeout_seconds": 45})
    assert saved["auto_fallback"] is False
    assert saved["timeout_seconds"] == 45

    # Reload to verify persistence
    reloaded = load_image_config()
    assert reloaded["auto_fallback"] is False
    assert reloaded["timeout_seconds"] == 45


def test_quota_error_detection():
    """Verify robust recognition of rate limits, quotas, and credit errors."""
    assert is_quota_or_rate_limit_error("429 RESOURCE_EXHAUSTED: Quota exceeded") is True
    assert is_quota_or_rate_limit_error("Rate limit reached for requests per minute") is True
    assert is_quota_or_rate_limit_error("402 Payment Required: Insufficient balance") is True
    assert is_quota_or_rate_limit_error("Account locked: out of credits") is True
    assert is_quota_or_rate_limit_error("User has exceeded their current quota.") is True
    assert is_quota_or_rate_limit_error("403 Forbidden: balance_exhausted") is True

    # Normal non-quota errors should return False
    assert is_quota_or_rate_limit_error("404 Not Found") is False
    assert is_quota_or_rate_limit_error("Invalid prompt syntax") is False
    assert is_quota_or_rate_limit_error("Connection refused") is False


def test_image_validation(tmp_path: Path):
    """Verify validation of image headers and rejection of corrupted or HTML files."""
    valid_file = tmp_path / "valid.jpg"
    valid_file.write_bytes(VALID_JPEG_BYTES)
    is_valid, fmt, reason = validate_image_file(str(valid_file))
    assert is_valid is True
    assert fmt == "jpeg"

    png_file = tmp_path / "valid.png"
    png_file.write_bytes(VALID_PNG_BYTES)
    is_valid, fmt, reason = validate_image_file(str(png_file))
    assert is_valid is True
    assert fmt == "png"

    html_file = tmp_path / "error.html"
    html_file.write_bytes(INVALID_HTML_BYTES)
    is_valid, fmt, reason = validate_image_file(str(html_file))
    assert is_valid is False

    empty_file = tmp_path / "empty.jpg"
    empty_file.write_bytes(b"")
    is_valid, fmt, reason = validate_image_file(str(empty_file))
    assert is_valid is False


def test_primary_provider_success_no_fallback():
    """Primary provider succeeds -> execution succeeds without fallback."""
    selector = ImageSelector()

    primary_tool = DummyMockImageTool("google_imagen", "google_imagen", behavior="success")
    secondary_tool = DummyMockImageTool("fal_flux_image", "fal_flux", behavior="success")

    with patch.object(selector, "_providers", return_value=[primary_tool, secondary_tool]):
        res = selector.execute({"prompt": "A majestic Vedic sunrise over the Himalayas"})

        assert res.success is True
        assert res.data["selected_provider"] == "google_imagen"
        assert res.data["selected_tool"] == "google_imagen"
        assert res.data["fallback_occurred"] is False
        assert len(res.data["fallback_history"]) == 0
        assert primary_tool.call_count == 1
        assert secondary_tool.call_count == 0


def test_primary_fails_with_quota_error_falls_back_to_secondary():
    """Primary fails with 429 quota exhaustion -> gracefully falls back to secondary provider."""
    selector = ImageSelector()

    primary_tool = DummyMockImageTool(
        name="google_imagen",
        provider="google_imagen",
        behavior="fail",
        fail_error="429 RESOURCE_EXHAUSTED: Quota exceeded for model gemini-3.1-flash-image",
    )
    secondary_tool = DummyMockImageTool(
        name="fal_flux_image",
        provider="fal_flux",
        behavior="success",
    )

    with patch.object(selector, "_providers", return_value=[primary_tool, secondary_tool]):
        res = selector.execute({"prompt": "Sacred Ayodhya temple in golden hour"})

        assert res.success is True
        assert res.data["selected_provider"] == "fal_flux"
        assert res.data["selected_tool"] == "fal_flux_image"
        assert res.data["fallback_occurred"] is True
        assert len(res.data["fallback_history"]) == 1
        assert res.data["fallback_history"][0]["provider"] == "google_imagen"
        assert "RESOURCE_EXHAUSTED" in res.data["fallback_history"][0]["reason"]
        assert primary_tool.call_count == 1
        assert secondary_tool.call_count == 1


def test_multiple_failures_chain_fallback():
    """Primary fails (quota), secondary fails (network/exception), tertiary succeeds."""
    selector = ImageSelector()

    tool1 = DummyMockImageTool("google_imagen", "google_imagen", behavior="fail", fail_error="429 Quota Exceeded")
    tool2 = DummyMockImageTool("fal_flux_image", "fal_flux", behavior="exception")
    tool3 = DummyMockImageTool("replicate_image", "replicate", behavior="success")

    with patch.object(selector, "_providers", return_value=[tool1, tool2, tool3]):
        res = selector.execute({"prompt": "Ancient Sanskrit carvings on Shiva bow"})

        assert res.success is True
        assert res.data["selected_provider"] == "replicate"
        assert res.data["selected_tool"] == "replicate_image"
        assert res.data["fallback_occurred"] is True
        assert len(res.data["fallback_history"]) == 2
        assert res.data["fallback_history"][0]["provider"] == "google_imagen"
        assert res.data["fallback_history"][1]["provider"] == "fal_flux"
        assert tool1.call_count == 1
        assert tool2.call_count == 1
        assert tool3.call_count == 1


def test_all_providers_fail_returns_clear_error():
    """All providers fail -> returns clear descriptive error with full history."""
    selector = ImageSelector()

    tool1 = DummyMockImageTool("google_imagen", "google_imagen", behavior="fail", fail_error="429 Quota")
    tool2 = DummyMockImageTool("fal_flux_image", "fal_flux", behavior="fail", fail_error="403 Balance Exhausted")

    with patch.object(selector, "_providers", return_value=[tool1, tool2]):
        res = selector.execute({"prompt": "Mithila palace hall"})

        assert res.success is False
        assert "All attempted image providers failed" in res.error
        assert "fallback_history" in res.data
        assert len(res.data["fallback_history"]) == 2


def test_auto_fallback_disabled_fails_immediately():
    """When auto_fallback is disabled, failure returns immediately without calling secondary."""
    selector = ImageSelector()

    tool1 = DummyMockImageTool("google_imagen", "google_imagen", behavior="fail", fail_error="429 Quota")
    tool2 = DummyMockImageTool("fal_flux_image", "fal_flux", behavior="success")

    with patch.object(selector, "_providers", return_value=[tool1, tool2]):
        res = selector.execute({"prompt": "Pinaka bow", "auto_fallback": False})

        assert res.success is False
        assert tool1.call_count == 1
        assert tool2.call_count == 0
        assert "429 Quota" in res.error


def test_image_selector_get_and_set_config():
    """Backlot UI operations: get_config and set_config work as expected."""
    selector = ImageSelector()
    tool1 = DummyMockImageTool("google_imagen", "google_imagen")

    with patch.object(selector, "_providers", return_value=[tool1]):
        # Test get_config
        get_res = selector.execute({"operation": "get_config"})
        assert get_res.success is True
        assert "provider_priority" in get_res.data
        assert "discovered_providers" in get_res.data

        # Test set_config
        set_res = selector.execute({
            "operation": "set_config",
            "config_updates": {"timeout_seconds": 60, "max_retries": 3},
        })
        assert set_res.success is True
        assert set_res.data["timeout_seconds"] == 60
        assert set_res.data["max_retries"] == 3
