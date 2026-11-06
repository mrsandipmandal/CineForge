"""Tests for Backlot identity studio API endpoints."""

from fastapi.testclient import TestClient
import pytest

from backlot.server import app


@pytest.fixture
def client():
    return TestClient(app, base_url="http://127.0.0.1")


def test_identity_voices_endpoint(client):
    res = client.get("/api/identity/voices")
    assert res.status_code == 200
    voices = res.json()
    assert isinstance(voices, list)
    assert len(voices) >= 3
    profile_ids = [v["profile_id"] for v in voices]
    assert "dr_elena_vance" in profile_ids
    assert "aarti_patel" in profile_ids
    assert "anirban_roy" in profile_ids


def test_identity_faces_endpoint(client):
    res = client.get("/api/identity/faces")
    assert res.status_code == 200
    faces = res.json()
    assert isinstance(faces, list)
    assert len(faces) >= 2
    char_ids = [f["character_id"] for f in faces]
    assert "elena_vance" in char_ids
    assert "aarti_patel" in char_ids


def test_identity_characters_endpoint(client):
    res = client.get("/api/identity/characters")
    assert res.status_code == 200
    chars = res.json()
    assert isinstance(chars, list)
    assert len(chars) >= 2


def test_providers_summary_endpoint(client):
    res = client.get("/api/providers/summary")
    assert res.status_code == 200
    data = res.json()
    assert "composition_runtimes" in data
    assert "capabilities" in data
    assert "setup_offers" in data


def test_identity_media_path_traversal_protection(client):
    # Path traversal with /.. gets rejected either via routing 404 or security check 403
    res = client.get("/identity-media/../../../../etc/passwd")
    assert res.status_code in [400, 403, 404]

    # Subpath traversal that reaches endpoint handler
    res_subpath = client.get("/identity-media/voices/../../../../etc/passwd")
    assert res_subpath.status_code in [400, 403, 404]

    # Non-existent safe path returns 404
    res_notfound = client.get("/identity-media/voices/non_existent.wav")
    assert res_notfound.status_code == 404
