"""Capability-level text-to-speech selector that enforces strict provider priority and fallbacks.

Default Provider Priority:
  1. OpenAI.fm — Primary default for all TTS requests (high quality, Fable voice, instructions)
  2. Kokoro TTS — First fallback (local 82M open-source model)
  3. VoxCPM2 — Second fallback (flow-matching voice cloning / CUDA / Kaggle)
  4. Other configured free/open-source TTS providers (Piper, Indic, MMS, F5)
  5. Official OpenAI TTS API — Last resort, optional and disabled unless explicitly enabled by user.

Enforces automatic detection of connection failures, timeouts, HTTP errors,
and invalid audio responses, seamlessly trying the next eligible provider.
Paid providers are strictly protected and never called silently.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib.audio_validator import validate_audio_file
from lib.tts_config import (
    DEFAULT_PRIORITY,
    get_effective_priority,
    is_paid_provider,
    load_tts_config,
    save_tts_config,
)
from tools.base_tool import (
    BaseTool,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)

logger = logging.getLogger(__name__)


class TTSSelector(BaseTool):
    name = "tts_selector"
    version = "1.0.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "selector"
    stability = ToolStability.PRODUCTION
    runtime = ToolRuntime.HYBRID
    agent_skills = ["text-to-speech", "elevenlabs"]

    capabilities = [
        "text_to_speech",
        "provider_selection",
        "strict_fallback_priority",
        "paid_provider_protection",
        "audio_validation",
    ]
    supports = {
        "user_preference_routing": True,
        "offline_fallback": True,
        "multilingual": True,
        "automatic_fallback": True,
        "paid_provider_gating": True,
    }
    best_for = [
        "preflight tool selection",
        "user-facing recommendation flows",
        "fault-tolerant speech generation with strict OpenAI.fm -> Kokoro -> VoxCPM2 priority",
    ]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string", "description": "Text to convert to speech"},
            "instructions": {
                "type": "string",
                "description": "Custom narration instructions or emotion/style cues (supported by OpenAI.fm).",
            },
            "prompt": {
                "type": "string",
                "description": "Alias for instructions or style directive.",
            },
            "voice": {
                "type": "string",
                "description": "Voice name or ID. OpenAI.fm supports fable, alloy, ash, coral, etc. Default: fable.",
            },
            "voice_id": {
                "type": "string",
                "description": "Alias for voice.",
            },
            "voice_profile_id": {
                "type": "string",
                "description": "Voice profile identifier for voice consistency.",
            },
            "language_code": {
                "type": "string",
                "description": "Language code (e.g. en, hi, bn).",
            },
            "speed": {
                "type": "number",
                "minimum": 0.25,
                "maximum": 4.0,
                "default": 1.0,
                "description": "Speaking rate multiplier.",
            },
            "speaking_rate": {
                "type": "number",
                "description": "Alias for speed.",
            },
            "pitch": {
                "type": "number",
                "description": "Pitch adjustment.",
            },
            "timestamps": {
                "type": "boolean",
                "default": False,
                "description": "Request word timestamps when the selected provider supports them.",
            },
            "preferred_provider": {
                "type": "string",
                "description": "Provider name or 'auto'. Default: 'openaifm'.",
                "default": "auto",
            },
            "preferred_tool": {
                "type": "string",
                "description": "Exact tool name (e.g. openaifm_tts). If specified, runs in manual mode without fallback.",
            },
            "preferred_model": {
                "type": "string",
                "description": "Exact tool name to attempt first.",
            },
            "allowed_providers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Restrict execution to a subset of provider names.",
            },
            "allow_paid": {
                "type": "boolean",
                "default": False,
                "description": "Whether paid providers (e.g. official OpenAI API, ElevenLabs) are permitted. Default: False.",
            },
            "enable_paid_providers": {
                "type": "boolean",
                "description": "Alias for allow_paid.",
            },
            "auto_fallback": {
                "type": "boolean",
                "default": True,
                "description": "Whether to automatically fall back to the next provider on failure. Default: True.",
            },
            "manual_mode": {
                "type": "boolean",
                "default": False,
                "description": "If True, runs only the primary/selected provider without fallback.",
            },
            "timeout_seconds": {
                "type": "integer",
                "default": 20,
                "description": "Timeout per provider attempt in seconds.",
            },
            "output_path": {
                "type": "string",
                "description": "Output audio file path.",
            },
            "operation": {
                "type": "string",
                "enum": ["generate", "rank", "get_config", "set_config"],
                "default": "generate",
                "description": "Operation mode. 'generate', 'rank', 'get_config', or 'set_config'.",
            },
            "config_updates": {
                "type": "object",
                "description": "Dictionary of configuration updates for set_config operation.",
            },
        },
    }

    def _prepare_task_context(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Normalize task context from inputs, mapping language codes to style/intent keywords."""
        from lib.scoring import normalize_task_context

        task_ctx = dict(inputs.get("task_context") or {})
        lang = str(inputs.get("language_code") or "").lower()
        LANG_SIGNAL_MAP = {
            "bn": ["bengali", "multilingual", "indic", "narration"],
            "hi": ["hindi", "multilingual", "indic", "narration"],
            "zh": ["chinese", "mandarin", "multilingual", "narration"],
        }
        for code, signals in LANG_SIGNAL_MAP.items():
            if code in lang:
                existing = list(task_ctx.get("style_keywords") or [])
                task_ctx["style_keywords"] = list(set(existing) | set(signals))
                if not task_ctx.get("intent"):
                    task_ctx["intent"] = " ".join(signals)
                break
        return normalize_task_context(
            task_ctx,
            prompt=inputs.get("text", ""),
            capability=self.capability,
            operation=inputs.get("operation", "generate"),
        )

    def _providers(self) -> list[BaseTool]:
        """Auto-discover TTS providers from the registry."""
        from tools.tool_registry import registry

        registry.ensure_discovered()
        return [t for t in registry.get_by_capability("tts") if t.name != self.name]

    @property
    def fallback_tools(self) -> list[str]:
        """Dynamically built list of available provider tools."""
        return [t.name for t in self._providers()]

    @property
    def provider_matrix(self) -> dict[str, dict[str, str]]:
        matrix = {}
        for tool in self._providers():
            strength = ", ".join(tool.best_for) if tool.best_for else tool.name
            matrix[tool.provider] = {"tool": tool.name, "strength": strength}
        return matrix

    def get_status(self) -> ToolStatus:
        if any(tool.get_status() == ToolStatus.AVAILABLE for tool in self._providers()):
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        # Default policy prioritizes free OpenAI.fm / Kokoro / VoxCPM2 -> 0.0
        allow_paid = inputs.get("allow_paid", False) or inputs.get("enable_paid_providers", False)
        if not allow_paid:
            return 0.0
        preferred = inputs.get("preferred_provider", "auto")
        if preferred == "openai":
            tool = next((t for t in self._providers() if t.provider == "openai"), None)
            return tool.estimate_cost(inputs) if tool else 0.0
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        operation = inputs.get("operation", "generate")

        # Config operations
        if operation == "get_config":
            cfg = load_tts_config()
            cfg["discovered_providers"] = [
                {
                    "provider": t.provider,
                    "name": t.name,
                    "status": t.get_status().value,
                    "is_paid": is_paid_provider(t.provider),
                }
                for t in self._providers()
            ]
            return ToolResult(success=True, data=cfg)

        if operation == "set_config":
            updates = inputs.get("config_updates") or {}
            saved = save_tts_config(updates)
            return ToolResult(success=True, data=saved)

        # Rank mode
        if operation == "rank":
            effective_priority = get_effective_priority(inputs)
            tools_by_provider = {t.provider: t for t in self._providers()}
            rankings = []
            for idx, p in enumerate(effective_priority, 1):
                t = tools_by_provider.get(p)
                rankings.append({
                    "priority": idx,
                    "provider": p,
                    "tool": t.name if t else None,
                    "status": t.get_status().value if t else "not_installed",
                    "is_paid": is_paid_provider(p),
                    "is_primary": (idx == 1 and p == "openaifm"),
                })
            return ToolResult(
                success=True,
                data={
                    "primary_provider": "openaifm",
                    "rankings": rankings,
                    "priority_rankings": rankings,
                    "allow_paid": inputs.get("allow_paid", False),
                },
            )

        # Standard Speech Generation with Strict Priority & Fallback Loop
        return self._generate_with_fallback(inputs)

    def _generate_with_fallback(self, inputs: dict[str, Any]) -> ToolResult:
        cfg = load_tts_config()
        text = str(inputs.get("text") or "").strip()
        if not text:
            return ToolResult(success=False, error="Text parameter is required for TTS generation.")

        allow_paid = bool(
            inputs.get("allow_paid")
            or inputs.get("enable_paid_providers")
            or cfg.get("allow_paid_providers", False)
        )
        auto_fallback = bool(
            inputs.get("auto_fallback", cfg.get("auto_fallback", True))
            and not inputs.get("manual_mode", cfg.get("manual_mode", False))
        )
        preferred_tool_name = inputs.get("preferred_tool")

        # Discover all TTS tools
        discovered = self._providers()
        tool_by_name = {t.name: t for t in discovered}
        tools_by_provider: dict[str, list[BaseTool]] = {}
        for t in discovered:
            tools_by_provider.setdefault(t.provider, []).append(t)

        # Handle exact preferred_tool request (manual single tool mode)
        if preferred_tool_name:
            target_tool = tool_by_name.get(preferred_tool_name)
            if not target_tool:
                return ToolResult(
                    success=False,
                    error=f"Requested preferred_tool '{preferred_tool_name}' not found in registry.",
                )
            if is_paid_provider(target_tool.provider) and not allow_paid:
                return ToolResult(
                    success=False,
                    error=(
                        f"Tool '{preferred_tool_name}' is backed by paid provider '{target_tool.provider}'. "
                        "Paid providers are disabled. Pass allow_paid=True to enable."
                    ),
                )
            if target_tool.get_status() != ToolStatus.AVAILABLE:
                return ToolResult(
                    success=False,
                    error=f"Requested tool '{preferred_tool_name}' is UNAVAILABLE.",
                )
            adapted = self._adapt_inputs(target_tool, inputs)
            res = target_tool.execute(adapted)
            if res.success:
                if res.data is None:
                    res.data = {}
                res.data.setdefault("selected_provider", target_tool.provider)
                res.data.setdefault("selected_tool", target_tool.name)
                res.data["fallback_occurred"] = False
            return res

        # Assemble prioritized candidates
        priority_providers = get_effective_priority(inputs, allow_paid_override=allow_paid)
        candidate_tools: list[BaseTool] = []

        for prov in priority_providers:
            plist = tools_by_provider.get(prov, [])
            for t in plist:
                if t.get_status() == ToolStatus.AVAILABLE:
                    candidate_tools.append(t)

        # If user explicitly preferred a model, ensure it is tried first
        pref_model = inputs.get("preferred_model")
        if pref_model and pref_model in tool_by_name:
            p_tool = tool_by_name[pref_model]
            if p_tool in candidate_tools:
                candidate_tools.remove(p_tool)
            if p_tool.get_status() == ToolStatus.AVAILABLE:
                if not (is_paid_provider(p_tool.provider) and not allow_paid):
                    candidate_tools.insert(0, p_tool)

        if not candidate_tools:
            # Check why none are available
            if not allow_paid and any(is_paid_provider(t.provider) for t in discovered if t.get_status() == ToolStatus.AVAILABLE):
                return ToolResult(
                    success=False,
                    error=(
                        "All free TTS providers are currently unavailable or not configured. "
                        "Paid providers (e.g. Official OpenAI TTS) exist but are disabled by policy. "
                        "Pass allow_paid=True to enable paid fallback or configure OpenAI.fm / Kokoro / VoxCPM2."
                    ),
                )
            return ToolResult(
                success=False,
                error="No eligible TTS providers are currently installed, configured, or available.",
            )

        fallback_history: list[dict[str, Any]] = []

        # Execute in priority order with automatic fallback
        for idx, tool in enumerate(candidate_tools):
            prov = tool.provider
            is_primary = (idx == 0 and prov == "openaifm")

            # Double-check paid protection
            if is_paid_provider(prov) and not allow_paid:
                continue

            logger.info(
                "Attempting TTS synthesis with [%s] (%s) — priority rank #%d",
                prov, tool.name, idx + 1
            )

            try:
                adapted = self._adapt_inputs(tool, inputs)
            except Exception as exc:
                err_msg = f"Input adaptation error for {tool.name}: {exc}"
                fallback_history.append({"provider": prov, "tool": tool.name, "reason": err_msg, "status": "failed"})
                if not auto_fallback:
                    return ToolResult(success=False, error=err_msg, data={"fallback_history": fallback_history})
                continue

            try:
                result = tool.execute(adapted)
            except Exception as exc:
                err_msg = f"Execution exception in {tool.name}: {exc}"
                fallback_history.append({"provider": prov, "tool": tool.name, "reason": err_msg, "status": "failed"})
                if not auto_fallback:
                    return ToolResult(success=False, error=err_msg, data={"fallback_history": fallback_history})
                continue

            if not result.success:
                err_msg = result.error or f"{tool.name} returned success=False"
                fallback_history.append({"provider": prov, "tool": tool.name, "reason": err_msg, "status": "failed"})
                logger.warning("TTS provider %s failed (%s). Moving to next fallback.", prov, err_msg)
                if not auto_fallback:
                    if result.data is None:
                        result.data = {}
                    result.data["fallback_history"] = fallback_history
                    return result
                continue

            # Validate generated audio on disk
            out_file = result.data.get("output_path") if result.data else None
            if not out_file and result.artifacts:
                out_file = result.artifacts[0]
            if out_file:
                is_valid, fmt, val_reason = validate_audio_file(out_file, min_bytes=100)
                if not is_valid:
                    err_msg = f"Invalid audio output from {tool.name}: {val_reason}"
                    fallback_history.append({"provider": prov, "tool": tool.name, "reason": err_msg, "status": "failed"})
                    logger.warning("Audio validation failed for %s (%s). Falling back.", prov, val_reason)
                    if not auto_fallback:
                        return ToolResult(success=False, error=err_msg, data={"fallback_history": fallback_history})
                    continue

            # SUCCESS! Enrich result with provider and fallback audit trail
            if result.data is None:
                result.data = {}
            result.data["selected_provider"] = prov
            result.data["selected_tool"] = tool.name
            result.data["is_primary_provider"] = is_primary
            result.data["fallback_occurred"] = len(fallback_history) > 0
            result.data["fallback_history"] = fallback_history
            result.data["priority_rank_used"] = idx + 1
            result.data["configured_priority"] = priority_providers

            if fallback_history:
                first_failed = fallback_history[0]
                result.data["fallback_reason"] = (
                    f"Primary provider '{first_failed['provider']}' failed: {first_failed['reason']}. "
                    f"Successfully generated via fallback provider '{prov}'."
                )
                try:
                    from lib.tts_config import record_fallback_event
                    record_fallback_event(first_failed['provider'], str(first_failed['reason']), prov)
                except Exception:
                    pass
            else:
                result.data["fallback_reason"] = None

            logger.info("TTS generation successful using [%s] (%s)", prov, tool.name)
            return result

        # All eligible candidates failed
        failed_summary = "; ".join(f"{h['provider']}: {h['reason']}" for h in fallback_history)
        if not allow_paid:
            return ToolResult(
                success=False,
                error=(
                    f"All attempted free TTS providers failed ({failed_summary}). "
                    "Paid providers are disabled. Pass allow_paid=True to allow official OpenAI API fallback."
                ),
                data={"fallback_history": fallback_history},
            )

        return ToolResult(
            success=False,
            error=f"All eligible TTS providers failed: {failed_summary}",
            data={"fallback_history": fallback_history},
        )

    @staticmethod
    def _adapt_inputs(tool: BaseTool, inputs: dict[str, Any]) -> dict[str, Any]:
        """Translate capability-level controls to provider-native inputs."""
        adapted = dict(inputs)
        props = tool.input_schema.get("properties", {})

        # Map instructions / prompt
        instructions = inputs.get("instructions") or inputs.get("prompt")
        if instructions:
            if "instructions" in props:
                adapted["instructions"] = instructions
            elif "prompt" in props:
                adapted["prompt"] = instructions

        # Map speed / rate
        speed = inputs.get("speed") or inputs.get("speaking_rate")
        if speed is not None:
            if "speed" in props:
                adapted["speed"] = float(speed)
            elif "speaking_rate" in props:
                adapted["speaking_rate"] = float(speed)

        # Map voice / voice_id
        voice = inputs.get("voice") or inputs.get("voice_id")
        if voice:
            if "voice" in props:
                adapted["voice"] = voice
            if "voice_id" in props:
                adapted["voice_id"] = voice

        # Map timestamps -> with_timestamps
        if "timestamps" in inputs and "with_timestamps" in props:
            adapted["with_timestamps"] = bool(inputs["timestamps"])

        # Language adaptation
        lang = str(inputs.get("language_code") or "").lower()

        # Provider specific nuances
        if tool.name == "openaifm_tts":
            # Default to Fable voice for OpenAI.fm if not explicitly set
            if not inputs.get("voice") and not inputs.get("voice_id"):
                adapted["voice"] = "fable"

        elif tool.name == "kokoro_tts":
            if not inputs.get("voice") and not inputs.get("voice_id"):
                adapted["voice"] = "af_heart"

        elif tool.name == "voxcpm2_tts":
            adapted.setdefault("operation", "synthesize")

        elif tool.name == "piper_tts":
            if not adapted.get("model"):
                if "bn" in lang:
                    adapted["model"] = "bn_IN-biswas-medium"
                elif "hi" in lang:
                    adapted["model"] = "hi_IN-priyamvada-medium"
                else:
                    adapted["model"] = "en_US-lessac-medium"

        elif tool.name == "elevenlabs_tts":
            if "bn" in lang:
                adapted.setdefault("model_id", "eleven_multilingual_v2")
            elif "hi" in lang:
                adapted.setdefault("model_id", "eleven_multilingual_v2")

        # Strip selector-only control parameters that providers don't recognize
        for k in (
            "preferred_provider", "allowed_providers", "preferred_tool",
            "allow_paid", "enable_paid_providers", "auto_fallback", "manual_mode",
            "operation", "config_updates",
        ):
            adapted.pop(k, None)

        return adapted
