"""Regression tests for honest tool availability reporting."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

from tools.analysis.face_tracker import FaceTracker
from tools.audio.indic_tts import IndicTTS
from tools.audio.piper_tts import PiperTTS
from tools.audio.voxcpm2 import VoxCPM2TTS
from tools.base_tool import ToolStatus
from tools.enhancement.eye_enhance import EyeEnhance
from tools.tool_registry import ToolRegistry
from tools.video.corpus_builder import CorpusBuilder


def test_voxcpm2_unavailable_without_tunnel_or_local_gpu(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VOXCPM2_SERVER_URL", raising=False)
    monkeypatch.setattr("tools.audio.voxcpm2.SESSION_FILE", tmp_path / "missing_session.json")

    tool = VoxCPM2TTS()
    monkeypatch.setattr(tool, "_local_voxcpm_ready", lambda: False)
    assert tool.get_status() == ToolStatus.UNAVAILABLE

    monkeypatch.setenv("VOXCPM2_SERVER_URL", "https://worker.trycloudflare.com")
    assert tool.get_status() == ToolStatus.AVAILABLE


def test_indic_tts_requires_weights_and_avoids_phantom_artifacts(tmp_path: Path, monkeypatch) -> None:
    tool = IndicTTS()
    monkeypatch.setenv("INDIC_MODELS_DIR", str(tmp_path / "no-models"))
    monkeypatch.setattr("tools.audio.indic_tts.INDIC_MODELS_DIR", tmp_path / "no-models")
    monkeypatch.setattr("tools.audio.indic_tts.get_workspace_root", lambda: tmp_path)
    monkeypatch.setattr("tools.audio.indic_tts.get_package_root", lambda: tmp_path)

    orig_find_spec = __import__("importlib.util").util.find_spec

    def fake_find_spec(name: str, *args, **kwargs):
        if name in ("torch", "gradio_client"):
            return None
        return orig_find_spec(name, *args, **kwargs)

    monkeypatch.setattr("importlib.util.find_spec", fake_find_spec)
    assert tool.get_status() == ToolStatus.UNAVAILABLE

    out_wav = tmp_path / "out.wav"
    res = tool.execute({"text": "নমস্কার", "language": "bn-IN", "output_path": str(out_wav)})
    assert res.success is True
    assert res.data["status"] == "ready_for_weights"
    assert res.artifacts == []


def test_piper_tts_resolves_workspace_models(tmp_path: Path, monkeypatch) -> None:
    model_file = tmp_path / "library" / "models" / "piper" / "en_US-lessac-medium.onnx"
    model_file.parent.mkdir(parents=True)
    model_file.write_bytes(b"onnx-stub")

    monkeypatch.setenv("CINEFORGE_HOME", str(tmp_path))
    onnx_path, cfg_path = PiperTTS()._resolve_model_path("en_US-lessac-medium")
    assert onnx_path == model_file
    assert cfg_path == model_file.with_name("en_US-lessac-medium.onnx.json")


def test_corpus_builder_status_and_missing_pkg_diagnostics(monkeypatch) -> None:
    import tools.video.stock_sources as stock_sources

    monkeypatch.setattr(stock_sources, "available_sources", lambda: [])
    assert CorpusBuilder().get_status() == ToolStatus.UNAVAILABLE

    orig_find_spec = __import__("importlib.util").util.find_spec
    monkeypatch.setattr(
        "importlib.util.find_spec",
        lambda name, *args, **kwargs: None if name == "cv2" else orig_find_spec(name, *args, **kwargs),
    )
    reg = ToolRegistry()
    avail = reg.describe_tool_availability(CorpusBuilder(), status=ToolStatus.DEGRADED)
    assert avail["category"] == "missing_pkg"
    assert "opencv-python" in avail["reason"]


def test_eye_enhance_and_face_tracker_status_honesty(monkeypatch) -> None:
    eye = EyeEnhance()
    monkeypatch.setattr(eye, "_has_mediapipe", lambda: False)
    monkeypatch.setattr(eye, "_has_opencv", lambda: False)
    with patch.object(shutil, "which", return_value="/usr/bin/ffmpeg"):
        assert eye.get_status() == ToolStatus.DEGRADED
    with patch.object(shutil, "which", return_value=None):
        assert eye.get_status() == ToolStatus.UNAVAILABLE

    ft = FaceTracker()
    assert "python:cv2" in ft.dependencies
    monkeypatch.setattr(ft, "_has_mediapipe", lambda: False)
    monkeypatch.setattr(ft, "_has_opencv", lambda: False)
    assert ft.get_status() == ToolStatus.UNAVAILABLE
    monkeypatch.setattr(ft, "_has_opencv", lambda: True)
    assert ft.get_status() == ToolStatus.DEGRADED


def test_registry_describe_tool_availability(monkeypatch) -> None:
    reg = ToolRegistry()
    avail = reg.describe_tool_availability(VoxCPM2TTS(), status=ToolStatus.UNAVAILABLE)
    assert avail["category"] == "missing_env"
    assert "VOXCPM2_SERVER_URL" in avail["reason"]


def test_mediapipe_check_rejects_modern_mediapipe_without_solutions(monkeypatch) -> None:
    import sys
    import types

    fake_mp = types.ModuleType("mediapipe")  # 1.x tasks-only package lacks .solutions
    monkeypatch.setitem(sys.modules, "mediapipe", fake_mp)
    assert EyeEnhance()._has_mediapipe() is False
    assert FaceTracker()._has_mediapipe() is False
