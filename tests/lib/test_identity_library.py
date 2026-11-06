"""Tests for the Identity Library (lib/identity_library.py)."""

import json
from pathlib import Path

import pytest

from lib.identity_library import (
    IdentityLibrary,
    IdentitySecurityError,
    VoiceProfile,
    FaceProfile,
    CharacterProfile,
)


@pytest.fixture
def temp_identity_lib(tmp_path: Path) -> IdentityLibrary:
    lib_dir = tmp_path / "sample-files"
    lib = IdentityLibrary(lib_dir)
    lib.ensure_directories()
    return lib


def test_identity_directory_structure(temp_identity_lib: IdentityLibrary):
    assert temp_identity_lib.voices_dir.is_dir()
    assert temp_identity_lib.faces_dir.is_dir()
    assert temp_identity_lib.characters_dir.is_dir()
    assert temp_identity_lib.manifests_dir.is_dir()


def test_path_traversal_protection(temp_identity_lib: IdentityLibrary):
    with pytest.raises(IdentitySecurityError):
        temp_identity_lib._safe_resolve("../../../etc/passwd")

    with pytest.raises(IdentitySecurityError):
        temp_identity_lib._safe_resolve("/etc/shadow")


def test_voice_profile_lifecycle(temp_identity_lib: IdentityLibrary, tmp_path: Path):
    profile = VoiceProfile(
        profile_id="test_speaker",
        name="Test Speaker",
        description="A test speaker voice profile",
        gender="male",
        primary_language="bn-IN",
        supported_languages=["bn-IN", "en-IN"],
        voice_type="narration",
        consent_verified=True,
    )
    temp_identity_lib.save_voice_profile(profile)

    loaded = temp_identity_lib.get_voice_profile("test_speaker")
    assert loaded is not None
    assert loaded.name == "Test Speaker"
    assert loaded.primary_language == "bn-IN"
    assert loaded.consent_verified is True

    # Test listing
    all_voices = temp_identity_lib.list_voice_profiles()
    assert len(all_voices) == 1
    assert all_voices[0].profile_id == "test_speaker"


def test_face_profile_lifecycle(temp_identity_lib: IdentityLibrary):
    profile = FaceProfile(
        character_id="test_character",
        name="Test Character",
        description="A test character profile",
        gender="female",
        ethnicity_or_style="contemporary",
        default_generation_prompt="portrait of test character",
        consent_verified=True,
    )
    temp_identity_lib.save_face_profile(profile)

    loaded = temp_identity_lib.get_face_profile("test_character")
    assert loaded is not None
    assert loaded.name == "Test Character"
    assert loaded.default_generation_prompt == "portrait of test character"

    all_faces = temp_identity_lib.list_face_profiles()
    assert len(all_faces) == 1
    assert all_faces[0].character_id == "test_character"


def test_character_profile_lifecycle(temp_identity_lib: IdentityLibrary):
    char = CharacterProfile(
        character_id="hero_1",
        name="Hero One",
        role="Protagonist",
        voice_profile_id="test_speaker",
        face_profile_id="test_character",
        primary_language="hi-IN",
        consent_verified=True,
    )
    temp_identity_lib.save_character(char)

    chars = temp_identity_lib.list_characters()
    assert len(chars) == 1
    assert chars[0].character_id == "hero_1"
    assert chars[0].voice_profile_id == "test_speaker"
    assert chars[0].face_profile_id == "test_character"


def test_index_generation(temp_identity_lib: IdentityLibrary):
    temp_identity_lib.save_voice_profile(
        VoiceProfile(profile_id="v1", name="Voice 1", primary_language="en-US", consent_verified=True)
    )
    temp_identity_lib.save_face_profile(
        FaceProfile(character_id="f1", name="Face 1", consent_verified=True)
    )
    temp_identity_lib.save_character(
        CharacterProfile(character_id="c1", name="Char 1", voice_profile_id="v1", face_profile_id="f1")
    )

    index = temp_identity_lib.update_index()
    assert "voices" in index
    assert "faces" in index
    assert "characters" in index
    assert len(index["voices"]) == 1
    assert len(index["faces"]) == 1
    assert len(index["characters"]) == 1

    index_file = temp_identity_lib.manifests_dir / "identity-index.json"
    assert index_file.is_file()
    disk_data = json.loads(index_file.read_text(encoding="utf-8"))
    assert disk_data["voices"][0]["profile_id"] == "v1"


def test_project_linking_and_consent(temp_identity_lib: IdentityLibrary, tmp_path: Path):
    project_dir = tmp_path / "projects" / "test-project"
    project_dir.mkdir(parents=True)

    # Unverified voice should raise IdentitySecurityError
    unverified = VoiceProfile(profile_id="unverified", name="Unverified", consent_verified=False)
    temp_identity_lib.save_voice_profile(unverified)

    with pytest.raises(IdentitySecurityError):
        temp_identity_lib.link_to_project(project_dir, voice_id="unverified", require_consent=True)

    # Verified voice should link cleanly
    verified = VoiceProfile(profile_id="verified", name="Verified", consent_verified=True)
    temp_identity_lib.save_voice_profile(verified)

    linked = temp_identity_lib.link_to_project(project_dir, voice_id="verified", require_consent=True)
    assert linked["voice"]["profile_id"] == "verified"
    target_json = project_dir / "assets" / "identities" / "voice" / "verified" / "profile.json"
    assert target_json.is_file()
