"""Unit and contract tests for NVIDIA NIM LLM provider tool.

Ensures offline test isolation by mocking network calls.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.base_tool import BaseTool, ToolRuntime, ToolStability, ToolStatus, ToolTier
from tools.text.nvidia_nim_llm import (
    DEFAULT_NIM_BASE_URL,
    DEFAULT_NIM_MODEL,
    NvidiaNimLLM,
)


class _FakeResponse:
    def __init__(self, json_data=None, status_code=200, text=""):
        self._json = json_data or {}
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._json


class TestNvidiaNimContract:
    def test_class_hierarchy_and_attributes(self):
        assert issubclass(NvidiaNimLLM, BaseTool)
        tool = NvidiaNimLLM()
        assert tool.name == "nvidia_nim_llm"
        assert tool.tier == ToolTier.GENERATE
        assert tool.capability == "llm"
        assert tool.provider == "nvidia_nim"
        assert tool.stability == ToolStability.PRODUCTION
        assert tool.runtime == ToolRuntime.HYBRID
        assert tool.fallback == "openrouter_llm"
        assert "openrouter_llm" in tool.fallback_tools
        assert "nvidia-nim" in tool.agent_skills

    def test_schema_structure(self):
        tool = NvidiaNimLLM()
        schema = tool.input_schema
        assert schema["type"] == "object"
        assert "prompt" in schema["properties"]
        assert "messages" in schema["properties"]
        assert "model" in schema["properties"]
        assert "temperature" in schema["properties"]
        assert "response_format" in schema["properties"]
        assert schema["properties"]["model"]["default"] == DEFAULT_NIM_MODEL

    def test_capabilities_and_supports(self):
        tool = NvidiaNimLLM()
        assert "scriptwriting" in tool.capabilities
        assert "nemotron_reasoning" in tool.capabilities
        assert tool.supports.get("nemotron") is True
        assert tool.supports.get("bengali") is True
        assert tool.supports.get("local_self_hosted") is True


class TestNvidiaNimStatus:
    def test_status_when_no_credentials(self, monkeypatch):
        tool = NvidiaNimLLM()
        monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
        monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
        monkeypatch.delenv("NVIDIA_NIM_BASE_URL", raising=False)
        assert tool.get_status() == ToolStatus.UNAVAILABLE

    def test_status_with_nvidia_nim_api_key(self, monkeypatch):
        tool = NvidiaNimLLM()
        monkeypatch.setenv("NVIDIA_NIM_API_KEY", "mock-test-key")
        monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
        assert tool.get_status() == ToolStatus.AVAILABLE

    def test_status_with_nvidia_api_key_fallback(self, monkeypatch):
        tool = NvidiaNimLLM()
        monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
        monkeypatch.setenv("NVIDIA_API_KEY", "mock-fallback-key")
        assert tool.get_status() == ToolStatus.AVAILABLE

    def test_status_with_local_endpoint(self, monkeypatch):
        tool = NvidiaNimLLM()
        monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
        monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
        monkeypatch.setenv("NVIDIA_NIM_BASE_URL", "http://localhost:8000/v1")
        assert tool.get_status() == ToolStatus.AVAILABLE


class TestNvidiaNimExecution:
    def test_execute_missing_credentials(self, monkeypatch):
        tool = NvidiaNimLLM()
        monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
        monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
        monkeypatch.delenv("NVIDIA_NIM_BASE_URL", raising=False)

        res = tool.execute({"prompt": "Hello"})
        assert res.success is False
        assert "NVIDIA_NIM_API_KEY" in res.error

    def test_execute_missing_prompt_and_messages(self, monkeypatch):
        tool = NvidiaNimLLM()
        monkeypatch.setenv("NVIDIA_NIM_API_KEY", "mock-test-key")

        res = tool.execute({})
        assert res.success is False
        assert "Either 'prompt' or 'messages' must be provided" in res.error

    def test_execute_mock_prompt_success(self, monkeypatch):
        tool = NvidiaNimLLM()
        monkeypatch.setenv("NVIDIA_NIM_API_KEY", "mock-test-key")

        captured_request = {}

        def mock_post(url, headers=None, json=None, timeout=None):
            captured_request["url"] = url
            captured_request["headers"] = headers
            captured_request["json"] = json
            return _FakeResponse(
                json_data={
                    "model": DEFAULT_NIM_MODEL,
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "Cinematic script content generated by Nemotron.",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 20, "completion_tokens": 50, "total_tokens": 70},
                },
                status_code=200,
            )

        monkeypatch.setattr(requests, "post", mock_post)

        res = tool.execute({
            "prompt": "Write a 30s teaser script",
            "system_prompt": "You are a movie director.",
            "temperature": 0.8,
        })

        assert res.success is True
        assert res.data["content"] == "Cinematic script content generated by Nemotron."
        assert res.data["model"] == DEFAULT_NIM_MODEL
        assert res.data["provider"] == "nvidia_nim"
        assert res.data["usage"]["total_tokens"] == 70

        # Verify request structure
        assert captured_request["url"] == f"{DEFAULT_NIM_BASE_URL}/chat/completions"
        assert "Bearer mock-test-key" in captured_request["headers"]["Authorization"]
        assert len(captured_request["json"]["messages"]) == 2
        assert captured_request["json"]["messages"][0]["role"] == "system"
        assert captured_request["json"]["messages"][1]["role"] == "user"

    def test_execute_mock_messages_and_response_format(self, monkeypatch):
        tool = NvidiaNimLLM()
        monkeypatch.setenv("NVIDIA_NIM_API_KEY", "mock-test-key")

        captured_payload = {}

        def mock_post(url, headers=None, json=None, timeout=None):
            captured_payload.update(json)
            return _FakeResponse(
                json_data={
                    "model": "meta/llama-3.1-405b-instruct",
                    "choices": [
                        {
                            "message": {"content": '{"scenes": [{"id": 1}]}'},
                            "finish_reason": "stop",
                        }
                    ],
                },
                status_code=200,
            )

        monkeypatch.setattr(requests, "post", mock_post)

        res = tool.execute({
            "messages": [{"role": "user", "content": "Return json scene plan"}],
            "model": "meta/llama-3.1-405b-instruct",
            "response_format": {"type": "json_object"},
        })

        assert res.success is True
        assert res.data["content"] == '{"scenes": [{"id": 1}]}'
        assert res.data["model"] == "meta/llama-3.1-405b-instruct"
        assert captured_payload["response_format"] == {"type": "json_object"}

    def test_execute_local_nim_container_override(self, monkeypatch):
        tool = NvidiaNimLLM()
        monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
        monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
        monkeypatch.setenv("NVIDIA_NIM_BASE_URL", "http://localhost:8000/v1")

        captured_url = None

        def mock_post(url, headers=None, json=None, timeout=None):
            nonlocal captured_url
            captured_url = url
            return _FakeResponse(
                json_data={
                    "choices": [{"message": {"content": "Local RTX GPU response"}}],
                },
                status_code=200,
            )

        monkeypatch.setattr(requests, "post", mock_post)

        res = tool.execute({"prompt": "Hello local NIM"})
        assert res.success is True
        assert res.data["content"] == "Local RTX GPU response"
        assert captured_url == "http://localhost:8000/v1/chat/completions"

    def test_execute_http_error(self, monkeypatch):
        tool = NvidiaNimLLM()
        monkeypatch.setenv("NVIDIA_NIM_API_KEY", "mock-test-key")

        def mock_post(url, headers=None, json=None, timeout=None):
            return _FakeResponse(status_code=401, text="Unauthorized: invalid api key")

        monkeypatch.setattr(requests, "post", mock_post)

        res = tool.execute({"prompt": "Hello"})
        assert res.success is False
        assert "HTTP 401" in res.error

    def test_execute_timeout_handling(self, monkeypatch):
        tool = NvidiaNimLLM()
        monkeypatch.setenv("NVIDIA_NIM_API_KEY", "mock-test-key")

        def mock_post(url, headers=None, json=None, timeout=None):
            raise requests.exceptions.Timeout("Connection timed out")

        monkeypatch.setattr(requests, "post", mock_post)

        res = tool.execute({"prompt": "Hello"})
        assert res.success is False
        assert "timed out after 120 seconds" in res.error
