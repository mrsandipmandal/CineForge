"""Tests for CineForge config model."""
import pytest
from lib.config_model import CineForgeConfig, LLMConfig


def test_default_config_loads():
    cfg = CineForgeConfig()
    assert cfg.llm.temperature == 0.7
    assert cfg.llm.max_tokens == 8192


def test_stage_temperature_override():
    llm = LLMConfig(
        temperature=0.7,
        stage_temperature_overrides={"edit": 0.20, "compose": 0.10, "research": 0.85}
    )
    assert llm.temperature_for_stage("edit") == pytest.approx(0.20)
    assert llm.temperature_for_stage("compose") == pytest.approx(0.10)
    assert llm.temperature_for_stage("research") == pytest.approx(0.85)


def test_stage_temperature_fallback():
    llm = LLMConfig(temperature=0.7, stage_temperature_overrides={"edit": 0.2})
    # Unknown stage falls back to global default
    assert llm.temperature_for_stage("unknown_stage") == pytest.approx(0.7)
    assert llm.temperature_for_stage("") == pytest.approx(0.7)


def test_load_from_yaml(tmp_path):
    """Config loads correctly from a YAML file with stage overrides."""
    yaml_content = """
llm:
  provider: anthropic
  temperature: 0.7
  max_tokens: 8192
  stage_temperature_overrides:
    edit: 0.2
    compose: 0.1
budget:
  mode: warn
  total_usd: 10.0
"""
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(yaml_content)
    cfg = CineForgeConfig.load(cfg_file)
    assert cfg.llm.temperature_for_stage("edit") == pytest.approx(0.2)
    assert cfg.llm.temperature_for_stage("compose") == pytest.approx(0.1)
    assert cfg.llm.max_tokens == 8192
