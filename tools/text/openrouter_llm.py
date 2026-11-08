"""OpenRouter LLM provider tool for CineForge.

Connects to OpenRouter's OpenAI-compatible API to access hundreds of AI models,
including completely free models (Gemini 2.0 Flash, Llama 3.3 70B, DeepSeek R1, Qwen 2.5)
and Grok models (x-ai/grok-2, x-ai/grok-beta) without requiring separate provider subscriptions.
Ideal for zero-cost scriptwriting, scene planning, storyboard structuring, and translation.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional
import requests

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)

# Recommended zero-cost free models available on OpenRouter
POPULAR_FREE_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "mistralai/mistral-small-24b-instruct-2501:free",
]

# Popular Grok models accessible via OpenRouter
GROK_MODELS = [
    "x-ai/grok-2-1212",
    "x-ai/grok-2-vision-1212",
    "x-ai/grok-beta",
]


class OpenRouterLLM(BaseTool):
    name = "openrouter_llm"
    version = "1.0.0"
    tier = ToolTier.GENERATE
    capability = "llm"
    provider = "openrouter"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = ["env:OPENROUTER_API_KEY"]
    install_instructions = (
        "Configure OPENROUTER_API_KEY from https://openrouter.ai/keys.\n"
        "Unlocks hundreds of models including 100% free models and Grok without multiple accounts."
    )
    fallback = None
    agent_skills = ["openrouter"]

    capabilities = [
        "scriptwriting",
        "scene_planning",
        "translation",
        "structured_ideation",
        "free_tier_generation",
        "grok_access",
    ]
    supports = {
        "free_models": True,
        "grok_models": True,
        "streaming": False,
        "json_schema": True,
        "multilingual": True,
        "bengali": True,
    }
    best_for = [
        "zero-cost scriptwriting and ideation using free tier models (:free suffix)",
        "accessing Grok models (x-ai/grok-2) via single OpenRouter API key",
        "translating scripts into Bengali, Hindi, and regional languages",
        "generating structured JSON scene plans and storyboard briefs",
    ]
    not_good_for = [
        "local offline LLM generation (use ollama)",
        "direct speech or video synthesis (delegates to TTS and video tools)",
    ]

    input_schema = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "User prompt or instructions.",
            },
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["role", "content"],
                    "properties": {
                        "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                        "content": {"type": "string"},
                    },
                },
                "description": "Optional chat message list. If omitted, constructed from prompt and system_prompt.",
            },
            "system_prompt": {
                "type": "string",
                "description": "Optional system instruction for guiding model behavior.",
            },
            "model": {
                "type": "string",
                "default": "google/gemini-2.0-flash-exp:free",
                "description": "OpenRouter model ID (e.g. google/gemini-2.0-flash-exp:free, meta-llama/llama-3.3-70b-instruct:free, x-ai/grok-2-1212).",
            },
            "temperature": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 2.0,
                "default": 0.7,
            },
            "max_tokens": {
                "type": "integer",
                "minimum": 64,
                "maximum": 16384,
                "default": 4096,
            },
            "response_format": {
                "type": "object",
                "description": "Optional format constraint, e.g. {'type': 'json_object'}.",
            },
        },
    }

    output_schema = {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "model": {"type": "string"},
            "finish_reason": {"type": "string"},
            "usage": {"type": "object"},
        },
    }

    def get_status(self) -> ToolStatus:
        return (
            ToolStatus.AVAILABLE
            if os.getenv("OPENROUTER_API_KEY")
            else ToolStatus.UNAVAILABLE
        )

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return ToolResult(
                success=False,
                error="OPENROUTER_API_KEY is not configured. Set it in .env or your environment.",
            )

        model = inputs.get("model") or "google/gemini-2.0-flash-exp:free"
        temperature = float(inputs.get("temperature", 0.7))
        max_tokens = int(inputs.get("max_tokens", 4096))
        messages = inputs.get("messages")

        if not messages:
            prompt = inputs.get("prompt", "").strip()
            if not prompt:
                return ToolResult(success=False, error="Either 'prompt' or 'messages' must be provided.")
            messages = []
            sys_prompt = inputs.get("system_prompt")
            if sys_prompt:
                messages.append({"role": "system", "content": sys_prompt})
            messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if "response_format" in inputs:
            payload["response_format"] = inputs["response_format"]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/cineforge",
            "X-Title": "CineForge Video Production",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
            )
            if resp.status_code != 200:
                return ToolResult(
                    success=False,
                    error=f"OpenRouter returned HTTP {resp.status_code}: {resp.text[:500]}",
                )

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                return ToolResult(success=False, error="OpenRouter returned empty choices array.")

            first_choice = choices[0]
            message_obj = first_choice.get("message", {})
            content = message_obj.get("content", "")
            finish_reason = first_choice.get("finish_reason")
            usage = data.get("usage", {})

            return ToolResult(
                success=True,
                data={
                    "content": content,
                    "model": data.get("model", model),
                    "finish_reason": finish_reason,
                    "usage": usage,
                    "provider": "openrouter",
                },
            )
        except Exception as exc:
            return ToolResult(success=False, error=f"OpenRouter request exception: {exc}")
