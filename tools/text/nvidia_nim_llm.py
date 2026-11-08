"""NVIDIA NIM (NVIDIA Inference Microservices) LLM provider tool for CineForge.

Provides high-performance, GPU-accelerated LLM reasoning and script generation
via NVIDIA NIM cloud endpoints (https://integrate.api.nvidia.com/v1) or
local self-hosted NIM Docker containers (e.g., http://localhost:8000/v1).

Supports flagship reasoning, creative writing, and worldbuilding models:
- nvidia/llama-3.1-nemotron-70b-instruct (primary default for reasoning & scriptwriting)
- meta/llama-3.3-70b-instruct (fast reasoning and dialogue polish)
- meta/llama-3.1-405b-instruct (ultra-high capacity master storyline and worldbuilding)
- deepseek-ai/deepseek-r1 (deep reasoning and complex technical explainers)
- qwen/qwen2.5-72b-instruct (multilingual, Bengali, Hindi, and regional scripts)
- mistralai/mistral-large-2-instruct (nuanced narrative and concise narration)
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

DEFAULT_NIM_MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"
DEFAULT_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

POPULAR_NIM_MODELS = [
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "meta/llama-3.3-70b-instruct",
    "meta/llama-3.1-405b-instruct",
    "deepseek-ai/deepseek-r1",
    "qwen/qwen2.5-72b-instruct",
    "mistralai/mistral-large-2-instruct",
]


class NvidiaNimLLM(BaseTool):
    name = "nvidia_nim_llm"
    version = "1.0.0"
    tier = ToolTier.GENERATE
    capability = "llm"
    provider = "nvidia_nim"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.HYBRID

    dependencies = ["env:NVIDIA_NIM_API_KEY"]
    install_instructions = (
        "Configure NVIDIA_NIM_API_KEY (or NVIDIA_API_KEY) from https://build.nvidia.com.\n"
        "Provides 1,000 free inference credits on cloud endpoints, or connect to local "
        "NIM containers on NVIDIA RTX GPUs by setting NVIDIA_NIM_BASE_URL=http://localhost:8000/v1."
    )
    fallback = "openrouter_llm"
    fallback_tools = ["openrouter_llm", "groq_llm"]
    agent_skills = ["nvidia-nim"]

    capabilities = [
        "scriptwriting",
        "scene_planning",
        "cinematic_worldbuilding",
        "storyboard_ideation",
        "translation",
        "nemotron_reasoning",
        "local_nim_inference",
    ]
    supports = {
        "nemotron": True,
        "llama_405b": True,
        "deepseek_r1": True,
        "json_schema": True,
        "multilingual": True,
        "bengali": True,
        "local_self_hosted": True,
    }
    best_for = [
        "complex cinematic narrative and multi-scene scripts via Nemotron-70B",
        "ultra-high scale worldbuilding and documentary structures via Llama-3.1-405B",
        "accelerated local inference on NVIDIA RTX GPUs via containerized NIMs",
        "multilingual script translation and cultural localization via Qwen 2.5 72B",
    ]
    not_good_for = [
        "direct image or video rendering (delegates to visual generators)",
        "speech audio synthesis (delegates to TTS tools)",
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
                "default": DEFAULT_NIM_MODEL,
                "description": (
                    f"NIM model ID (e.g. {DEFAULT_NIM_MODEL}, "
                    "meta/llama-3.3-70b-instruct, meta/llama-3.1-405b-instruct, deepseek-ai/deepseek-r1)."
                ),
            },
            "temperature": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 2.0,
                "default": 0.7,
            },
            "top_p": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "default": 0.95,
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
            "provider": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=256, vram_mb=0, disk_mb=0)
    retry_policy = RetryPolicy(max_retries=2, backoff_seconds=1.5)

    def _get_api_key(self) -> Optional[str]:
        return os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")

    def _get_base_url(self) -> str:
        url = os.getenv("NVIDIA_NIM_BASE_URL", DEFAULT_NIM_BASE_URL).strip()
        return url.rstrip("/")

    def _is_local_endpoint(self) -> bool:
        base_url = self._get_base_url().lower()
        return "localhost" in base_url or "127.0.0.1" in base_url or "0.0.0.0" in base_url

    def get_status(self) -> ToolStatus:
        # Local self-hosted NIM containers on localhost do not require cloud API keys
        if self._is_local_endpoint():
            return ToolStatus.AVAILABLE
        return ToolStatus.AVAILABLE if self._get_api_key() else ToolStatus.UNAVAILABLE

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        base_url = self._get_base_url()
        is_local = self._is_local_endpoint()
        api_key = self._get_api_key()

        if not is_local and not api_key:
            return ToolResult(
                success=False,
                error=(
                    "NVIDIA_NIM_API_KEY (or NVIDIA_API_KEY) is not configured. "
                    "Obtain a key with free credits from https://build.nvidia.com, or "
                    "point NVIDIA_NIM_BASE_URL to a local NIM container."
                ),
            )

        model = inputs.get("model") or DEFAULT_NIM_MODEL
        temperature = float(inputs.get("temperature", 0.7))
        top_p = float(inputs.get("top_p", 0.95))
        max_tokens = int(inputs.get("max_tokens", 4096))
        messages = inputs.get("messages")

        if not messages:
            prompt = inputs.get("prompt", "").strip()
            if not prompt:
                return ToolResult(
                    success=False,
                    error="Either 'prompt' or 'messages' must be provided to nvidia_nim_llm.",
                )
            messages = []
            sys_prompt = inputs.get("system_prompt")
            if sys_prompt:
                messages.append({"role": "system", "content": sys_prompt})
            messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }

        if "response_format" in inputs:
            payload["response_format"] = inputs["response_format"]

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "CineForge-Studio/1.0",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        endpoint_url = f"{base_url}/chat/completions"

        try:
            resp = requests.post(
                endpoint_url,
                headers=headers,
                json=payload,
                timeout=120,
            )

            if resp.status_code != 200:
                return ToolResult(
                    success=False,
                    error=f"NVIDIA NIM returned HTTP {resp.status_code}: {resp.text[:500]}",
                )

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                return ToolResult(success=False, error="NVIDIA NIM returned an empty choices array.")

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
                    "provider": "nvidia_nim",
                    "base_url": base_url,
                },
            )

        except requests.exceptions.Timeout:
            return ToolResult(
                success=False,
                error=f"NVIDIA NIM request timed out after 120 seconds ({endpoint_url}).",
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                error=f"NVIDIA NIM request exception: {exc}",
            )
