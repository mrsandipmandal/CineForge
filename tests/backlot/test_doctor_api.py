"""Tests for Backlot /api/doctor studio readiness and TTS preview endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import backlot.server as backlot_server
from backlot.server import create_app


def test_backlot_doctor_endpoint() -> None:
    client = TestClient(create_app(), base_url="http://127.0.0.1:4750")
    resp = client.get("/api/doctor")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tools_discovered"] > 50
    assert "binaries" in data
    assert "provider_summary" in data
    assert "workspace_root" in data["paths"]


def test_tts_preview_audio_blocks_traversal_and_symlinks(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = tmp_path / "workspace"
    repo_root = tmp_path / "repo"
    workspace.mkdir()
    repo_root.mkdir()
    outside = tmp_path / "secret.wav"
    outside.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt ")

    good = workspace / "output" / "clip.wav"
    good.parent.mkdir(parents=True)
    good.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt ")

    symlink_escape = workspace / "output" / "escape.wav"
    symlink_escape.symlink_to(outside)

    monkeypatch.setattr(backlot_server, "get_workspace_root", lambda: workspace)
    monkeypatch.setattr(backlot_server, "REPO_ROOT", repo_root)

    client = TestClient(create_app(), base_url="http://127.0.0.1:4750")

    ok = client.get("/api/tts/preview-audio", params={"path": "output/clip.wav"})
    assert ok.status_code == 200
    assert ok.content.startswith(b"RIFF")

    for bad_path in ("../secret.wav", "output/escape.wav", ".", ""):
        res = client.get("/api/tts/preview-audio", params={"path": bad_path})
        assert res.status_code == 403

    missing = client.get("/api/tts/preview-audio", params={"path": "output/missing.wav"})
    assert missing.status_code == 404
