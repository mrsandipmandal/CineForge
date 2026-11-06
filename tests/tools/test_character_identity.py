"""Tests for CharacterIdentity tool."""

from pathlib import Path
import pytest

from lib.identity_library import IdentityLibrary, FaceProfile, CharacterProfile
from tools.avatar.character_identity import CharacterIdentity


@pytest.fixture
def character_env(tmp_path: Path):
    sample_dir = tmp_path / "sample-files"
    lib = IdentityLibrary(sample_dir)
    lib.ensure_directories()

    face = FaceProfile(
        character_id="dr_elena",
        name="Dr. Elena",
        description="Lead scientist",
        default_generation_prompt="portrait of a woman scientist with glasses",
        negative_prompt="blurry, distorted",
        consent_verified=True,
    )
    lib.save_face_profile(face)

    # Add dummy front image
    ref_dir = lib.faces_dir / "dr_elena" / "references"
    front_img = ref_dir / "front_neutral.png"
    front_img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    char = CharacterProfile(
        character_id="dr_elena",
        name="Dr. Elena",
        role="Lead Host",
        voice_profile_id="dr_elena_vance",
        face_profile_id="dr_elena",
        primary_language="en-US",
        consent_verified=True,
    )
    lib.save_character(char)

    return sample_dir


def test_list_and_inspect_characters(character_env: Path):
    tool = CharacterIdentity()
    res = tool.execute({"operation": "list_characters", "sample_files_dir": str(character_env)})
    assert res.success is True
    assert res.data["count"] == 1
    assert res.data["characters"][0]["character_id"] == "dr_elena"

    res_inspect = tool.execute({
        "operation": "inspect_character",
        "character_id": "dr_elena",
        "sample_files_dir": str(character_env),
    })
    assert res_inspect.success is True
    assert res_inspect.data["character"]["name"] == "Dr. Elena"
    assert res_inspect.data["face_profile"]["character_id"] == "dr_elena"


def test_conditioning_bundle_generation(character_env: Path):
    tool = CharacterIdentity()

    # Generic bundle
    res = tool.execute({
        "operation": "get_conditioning_bundle",
        "character_id": "dr_elena",
        "target_provider": "generic",
        "sample_files_dir": str(character_env),
    })
    assert res.success is True
    bundle = res.data["bundle"]
    assert bundle["character_name"] == "Dr. Elena"
    assert bundle["front_image"] is not None
    assert bundle["prompt_descriptor"] == "portrait of a woman scientist with glasses"

    # Seedance bundle
    res_seedance = tool.execute({
        "operation": "get_conditioning_bundle",
        "character_id": "dr_elena",
        "target_provider": "seedance",
        "sample_files_dir": str(character_env),
    })
    assert res_seedance.success is True
    assert "seedance_conditioning" in res_seedance.data["bundle"]

    # TalkingHead bundle
    res_th = tool.execute({
        "operation": "get_conditioning_bundle",
        "character_id": "dr_elena",
        "target_provider": "talking_head",
        "sample_files_dir": str(character_env),
    })
    assert res_th.success is True
    assert "talking_head_conditioning" in res_th.data["bundle"]
    assert res_th.data["bundle"]["talking_head_conditioning"]["preprocess"] == "crop"


def test_consent_verification_workflow(character_env: Path):
    tool = CharacterIdentity()
    lib = IdentityLibrary(character_env)

    # Create unverified face
    lib.save_face_profile(FaceProfile(character_id="actor_unverified", name="Actor", consent_verified=False))

    inspect_res = tool.execute({
        "operation": "inspect_face",
        "character_id": "actor_unverified",
        "sample_files_dir": str(character_env),
    })
    assert inspect_res.data["face"]["consent_verified"] is False

    # Verify consent
    consent_res = tool.execute({
        "operation": "verify_consent",
        "character_id": "actor_unverified",
        "owner": "production_lead",
        "allow_external_upload": True,
        "sample_files_dir": str(character_env),
    })
    assert consent_res.success is True
    assert consent_res.data["consent_verified"] is True
