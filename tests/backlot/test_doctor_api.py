"""Tests for Backlot /api/doctor studio readiness endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

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
