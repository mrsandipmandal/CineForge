"""Tests for VoiceIdentity tool and TTSSelector voice profile integration."""

from pathlib import Path
import pytest

from lib.identity_library import IdentityLibrary, VoiceProfile
from tools.audio.voice_identity import VoiceIdentity
from tools.audio.tts_selector import TTSSelector
from tools.base_tool import ToolStatus


@pytest.fixture
def identity_env(tmp_path: Path):
    sample_dir = tmp_path / "sample-files"
    lib = IdentityLibrary(sample_dir)
    lib.ensure_directories()

    # Create Bengali voice profile
    bengali_voice = VoiceProfile(
        profile_id="sourav_bengali",
        name="Sourav",
        description="Authentic Bengali narrator",
        gender="male",
        primary_language="bn-IN",
        supported_languages=["bn-IN"],
        voice_type="narration",
        consent_verified=True,
        pitch_semitones=-1.0,
        default_speaking_rate=0.95,
    )
    lib.save_voice_profile(bengali_voice)

    # Create dummy sample
    sample_file = lib.voices_dir / "sourav_bengali" / "samples" / "sample1.wav"
    sample_file.write_bytes(b"RIFF" + b"\x00" * 100)

    # Create Hindi voice profile
    hindi_voice = VoiceProfile(
        profile_id="priya_hindi",
        name="Priya",
        description="Expressive Hindi narrator",
        gender="female",
        primary_language="hi-IN",
        supported_languages=["hi-IN", "en-IN"],
        voice_type="documentary",
        consent_verified=False,
    )
    lib.save_voice_profile(hindi_voice)

    return sample_dir


def test_voice_identity_list(identity_env: Path):
    tool = VoiceIdentity()
    res = tool.execute({"operation": "list", "sample_files_dir": str(identity_env)})
    assert res.success is True
    assert res.data["count"] == 2

    # Language filter
    res_bn = tool.execute({"operation": "list", "language": "bn-IN", "sample_files_dir": str(identity_env)})
    assert res_bn.success is True
    assert res_bn.data["count"] == 1
    assert res_bn.data["profiles"][0]["profile_id"] == "sourav_bengali"


def test_voice_identity_inspect_and_validate(identity_env: Path):
    tool = VoiceIdentity()
    res = tool.execute({"operation": "inspect", "profile_id": "sourav_bengali", "sample_files_dir": str(identity_env)})
    assert res.success is True
    assert res.data["profile"]["name"] == "Sourav"

    val_res = tool.execute({"operation": "validate", "profile_id": "sourav_bengali", "sample_files_dir": str(identity_env)})
    assert val_res.success is True
    assert val_res.data["consent_verified"] is True


def test_voice_identity_consent_gate(identity_env: Path):
    tool = VoiceIdentity()
    # Priya has consent_verified=False
    ref_res = tool.execute({"operation": "prepare_reference", "profile_id": "priya_hindi", "sample_files_dir": str(identity_env)})
    assert ref_res.success is False
    assert "Consent not verified" in ref_res.error

    # Verify consent
    consent_res = tool.execute({
        "operation": "verify_consent",
        "profile_id": "priya_hindi",
        "owner": "test_owner",
        "sample_files_dir": str(identity_env),
    })
    assert consent_res.success is True
    assert consent_res.data["consent_verified"] is True


def test_voice_routing_bengali(identity_env: Path):
    tool = VoiceIdentity()
    # Bengali standard TTS
    route_tts = tool.execute({"operation": "route_voice", "language": "bn-IN", "require_cloning": False})
    assert route_tts.success is True
    assert route_tts.data["recommended_tool"] in ["azure_tts", "google_tts"]
    assert "bn-IN" in route_tts.data["language"]

    # Bengali voice cloning
    route_clone = tool.execute({"operation": "route_voice", "language": "bn-IN", "require_cloning": True})
    assert route_clone.success is True
    assert route_clone.data["recommended_tool"] in ["fish_audio_tts", "elevenlabs_tts"]


def test_voice_routing_hindi():
    tool = VoiceIdentity()
    route = tool.execute({"operation": "route_voice", "language": "hi-IN", "require_cloning": False})
    assert route.success is True
    assert "hi-IN" in route.data["language"]
    assert route.data["recommended_tool"] in ["azure_tts", "google_tts"]


def test_tts_selector_with_voice_profile(identity_env: Path, monkeypatch):
    # Test that TTSSelector adapts inputs when voice_profile_id is passed
    selector = TTSSelector()
    inputs = {
        "text": "নমস্কার, এটি একটি পরীক্ষা।",
        "voice_profile_id": "sourav_bengali",
        "operation": "rank",
    }
    # Rank operation doesn't call external API
    res = selector.execute(inputs)
    assert res.success is True
    assert "rankings" in res.data
