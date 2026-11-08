"""Groq LPU LLM inference tool for CineForge.

Provides ultra-fast, zero-cost (free tier) LLM generation powered by Groq's
Language Processing Units (LPUs). Capable of generating hundreds of tokens per second.
Supports state-of-the-art open models:
- llama-3.3-70b-versatile (primary reasoning and creative scriptwriting)
- llama-3.1-8b-instant (ultra-fast sub-second generation)
- deepseek-r1-distill-llama-70b (deep mathematical and logical reasoning)
- gemma2-9b-it & mixtral-8x7b-32768
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

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"

POPULAR_GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


class GroqLLM(BaseTool):
    name = "groq_llm"
    version = "1.0.0"
    tier = ToolTier.GENERATE
    capability = "llm"
    provider = "groq"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = ["env:GROQ_API_KEY"]
    install_instructions = (
        "Configure GROQ_API_KEY from https://console.groq.com/keys.\n"
        "Provides ultra-fast free tier generation on Llama 3.3, Llama 3.1, and DeepSeek R1."
    )
    fallback = "openrouter_llm"
    fallback_tools = ["openrouter_llm"]
    agent_skills = ["groq"]

    capabilities = [
        "scriptwriting",
        "scene_planning",
        "storyboard_ideation",
        "translation",
        "ultra_fast_generation",
        "free_tier_generation",
    ]
    supports = {
        "ultra_fast_inference": True,
        "free_tier": True,
        "json_schema": True,
        "multilingual": True,
        "bengali": True,
    }
    best_for = [
        "near-instant script and narration generation (500+ tokens/sec)",
        "zero-cost production planning using Llama 3.3 70B",
        "rapid iterative storyboarding and prompt engineering",
    ]
    not_good_for = [
        "offline execution without internet (use local ollama)",
        "direct image/video generation (delegates to visual tools)",
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
                "description": "Optional list of message dicts. If omitted, built from prompt and system_prompt.",
            },
            "system_prompt": {
                "type": "string",
                "description": "Optional system prompt instructing the model.",
            },
            "model": {
                "type": "string",
                "default": DEFAULT_GROQ_MODEL,
                "description": "Groq model ID (e.g. llama-3.3-70b-versatile, llama-3.1-8b-instant, deepseek-r1-distill-llama-70b).",
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
                "maximum": 8192,
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
            if os.getenv("GROQ_API_KEY")
            else ToolStatus.UNAVAILABLE
        )

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return ToolResult(
                success=False,
                error="GROQ_API_KEY is not configured. Set it in .env or your environment (get one free at https://console.groq.com/keys).",
            )

        model = inputs.get("model") or DEFAULT_GROQ_MODEL
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
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if resp.status_code != 200:
                return ToolResult(
                    success=False,
                    error=f"Groq API returned HTTP {resp.status_code}: {resp.text[:500]}",
                )

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                return ToolResult(success=False, error="Groq API returned empty choices array.")

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
                    "provider": "groq",
                },
            )
        except Exception as exc:
            return ToolResult(success=False, error=f"Groq API request exception: {exc}")
