import json
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib.image_config import CONFIG_FILE

@pytest.fixture
def client(tmp_path):
    # Isolate config file
    old_config_file = CONFIG_FILE
    # Use a tmp path
    config_file = tmp_path / "image_settings.json"
    
    import lib.image_config
    lib.image_config.CONFIG_FILE = config_file
    
    # Create app
    app = create_app()
    # Add base_url to satisfy TrustedHostMiddleware
    client = TestClient(app, base_url="http://localhost")
    yield client
    
    lib.image_config.CONFIG_FILE = old_config_file

def test_get_image_settings_schema(client):
    # 1. GET /api/settings/image
    resp = client.get("/api/settings/image")
    assert resp.status_code == 200
    data = resp.json()
    assert "primary_provider" in data
    assert data["primary_provider_key"] == "google_imagen"
    assert isinstance(data["provider_priority"], list)
    assert isinstance(data["enabled_providers"], dict)
    assert isinstance(data["auto_fallback"], bool)
    assert isinstance(data["manual_mode"], bool)
    assert isinstance(data["providers"], list)
    assert isinstance(data["discovered_providers"], list)
    assert isinstance(data["discovered_tools"], list)

    # Aliases
    assert client.get("/api/image/config").status_code == 200
    assert client.get("/api/image/status").status_code == 200

def test_post_image_settings_updates_priority_and_persists(client):
    new_priority = ["fal_flux", "google_imagen", "bfl", "replicate"]
    resp = client.post("/api/settings/image", json={"provider_priority": new_priority})
    assert resp.status_code == 200
    assert resp.json()["provider_priority"] == new_priority
    
    # Verify persistence
    assert client.get("/api/settings/image").json()["provider_priority"] == new_priority

def test_post_image_settings_toggle_enabled(client):
    new_enabled = {"google_imagen": False, "fal_flux": True, "replicate": True}
    resp = client.post("/api/settings/image", json={"enabled_providers": new_enabled})
    assert resp.status_code == 200
    assert resp.json()["enabled_providers"]["google_imagen"] is False
    
    # Verify persistence
    assert client.get("/api/settings/image").json()["enabled_providers"]["google_imagen"] is False

def test_post_image_settings_malformed_json_400(client):
    resp = client.post("/api/settings/image", content=b"{invalid-json", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400
    assert "Invalid JSON body" in resp.json()["detail"]

def test_post_image_settings_non_dict_body_400(client):
    resp = client.post("/api/settings/image", json=["google_imagen", "fal_flux"])
    assert resp.status_code == 400
    assert "Expected a JSON object" in resp.json()["detail"]

def test_post_image_settings_invalid_priority_type_422(client):
    resp = client.post("/api/settings/image", json={"provider_priority": "not-a-list"})
    assert resp.status_code == 422
    
    resp = client.post("/api/settings/image", json={"provider_priority": [1, 2, 3]})
    assert resp.status_code == 422
    
    resp = client.post("/api/settings/image", json={"provider_priority": ["fal_flux", "   "]})
    assert resp.status_code == 422

def test_post_image_settings_invalid_enabled_type_422(client):
    resp = client.post("/api/settings/image", json={"enabled_providers": "not-a-dict"})
    assert resp.status_code == 422
    
    resp = client.post("/api/settings/image", json={"enabled_providers": {"google_imagen": "true"}})
    assert resp.status_code == 422

def test_post_image_settings_invalid_boolean_flags_422(client):
    resp = client.post("/api/settings/image", json={"auto_fallback": "false"})
    assert resp.status_code == 422
    
    resp = client.post("/api/settings/image", json={"manual_mode": 123})
    assert resp.status_code == 422
    
    resp = client.post("/api/settings/image", json={"primary_provider": 999})
    assert resp.status_code == 422
