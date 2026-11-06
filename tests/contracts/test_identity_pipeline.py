"""End-to-End Pipeline Contract Tests for Identity-Aware Workflows."""

from pathlib import Path
import pytest

from lib.checkpoint import init_project, write_checkpoint, read_checkpoint
from lib.identity_library import (
    IdentityLibrary,
    VoiceProfile,
    FaceProfile,
    CharacterProfile,
    IdentitySecurityError,
)
from schemas.artifacts import validate_artifact
from tools.audio.voice_identity import VoiceIdentity
from tools.avatar.character_identity import CharacterIdentity
from tests.contracts.test_phase0_contracts import sample_artifact


@pytest.fixture
def studio_env(tmp_path: Path):
    sample_dir = tmp_path / "sample-files"
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True)

    lib = IdentityLibrary(sample_dir)
    lib.ensure_directories()

    # Voice Profile: Bengali
    lib.save_voice_profile(VoiceProfile(
        profile_id="sourav_bn",
        name="Sourav",
        primary_language="bn-IN",
        supported_languages=["bn-IN"],
        voice_type="narration",
        consent_verified=True,
    ))

    # Voice Profile: Hindi (Unverified)
    lib.save_voice_profile(VoiceProfile(
        profile_id="aarti_hi",
        name="Aarti",
        primary_language="hi-IN",
        supported_languages=["hi-IN"],
        voice_type="documentary",
        consent_verified=False,
    ))

    # Face Profile
    face = FaceProfile(
        character_id="hero_face",
        name="Hero",
        default_generation_prompt="close up portrait of a protagonist",
        consent_verified=True,
    )
    lib.save_face_profile(face)
    ref_img = lib.faces_dir / "hero_face" / "references" / "front_neutral.png"
    ref_img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    # Character Profile
    lib.save_character(CharacterProfile(
        character_id="hero_char",
        name="Hero Presenter",
        voice_profile_id="sourav_bn",
        face_profile_id="hero_face",
        primary_language="bn-IN",
        consent_verified=True,
    ))

    lib.update_index()
    return {"sample_dir": sample_dir, "projects_dir": projects_dir, "lib": lib}


def test_voice_discovery_and_metadata(studio_env: dict):
    voice_tool = VoiceIdentity()
    res = voice_tool.execute({"operation": "list", "sample_files_dir": str(studio_env["sample_dir"])})
    assert res.success is True
    assert res.data["count"] == 2

    # Metadata inspection
    inspect_res = voice_tool.execute({
        "operation": "inspect",
        "profile_id": "sourav_bn",
        "sample_files_dir": str(studio_env["sample_dir"]),
    })
    assert inspect_res.success is True
    assert inspect_res.data["profile"]["primary_language"] == "bn-IN"


def test_consent_gating_on_unverified_voice(studio_env: dict):
    voice_tool = VoiceIdentity()
    res = voice_tool.execute({
        "operation": "prepare_reference",
        "profile_id": "aarti_hi",
        "sample_files_dir": str(studio_env["sample_dir"]),
    })
    assert res.success is False
    assert "Consent not verified" in res.error


def test_bengali_routing_precision(studio_env: dict):
    voice_tool = VoiceIdentity()
    route = voice_tool.execute({
        "operation": "route_voice",
        "language": "bn-IN",
        "require_cloning": False,
        "sample_files_dir": str(studio_env["sample_dir"]),
    })
    assert route.success is True
    assert route.data["recommended_tool"] in ["azure_tts", "google_tts"]
    assert "bn-IN" in route.data["language"]


def test_scene_plan_identity_binding_and_validation(studio_env: dict):
    # Construct a scene_plan containing identity references
    scene_plan = sample_artifact("scene_plan")
    scene_plan["scenes"][0]["voice_profile_id"] = "sourav_bn"
    scene_plan["scenes"][0]["character_id"] = "hero_char"
    scene_plan["scenes"][0]["identity"] = {
        "voice_profile_id": "sourav_bn",
        "character_id": "hero_char",
        "audio_strategy": "voice_clone",
        "visual_strategy": "reference_conditioned",
    }

    # Validate against JSON schema
    validate_artifact("scene_plan", scene_plan)


def test_asset_manifest_identity_provenance_validation(studio_env: dict):
    # Construct an asset_manifest with identity provenance
    asset_manifest = sample_artifact("asset_manifest")
    asset_manifest["assets"][0]["voice_profile_id"] = "sourav_bn"
    asset_manifest["assets"][0]["character_id"] = "hero_char"
    asset_manifest["assets"][0]["consent_verified"] = True
    asset_manifest["assets"][0]["reference_media_used"] = ["sample-files/faces/hero_face/references/front_neutral.png"]

    validate_artifact("asset_manifest", asset_manifest)


def test_checkpoint_roundtrip_with_identity(studio_env: dict):
    root = studio_env["projects_dir"]
    project_id = "test-identity-project"
    init_project(project_id, title="Identity Test", pipeline_type="animated-explainer", pipeline_dir=root)

    # Complete predecessors required by prerequisite enforcement
    for stage_name, art_name in [
        ("research", "research_brief"),
        ("proposal", "proposal_packet"),
        ("script", "script"),
    ]:
        write_checkpoint(
            pipeline_dir=root,
            project_id=project_id,
            stage=stage_name,
            status="completed",
            artifacts={art_name: sample_artifact(art_name)},
            human_approved=True,
            pipeline_type="animated-explainer",
        )

    scene_plan = sample_artifact("scene_plan")
    scene_plan["scenes"][0]["voice_profile_id"] = "sourav_bn"

    # Write gated checkpoint
    write_checkpoint(
        pipeline_dir=root,
        project_id=project_id,
        stage="scene_plan",
        status="completed",
        artifacts={"scene_plan": scene_plan},
        human_approved=True,
        pipeline_type="animated-explainer",
    )

    loaded = read_checkpoint(pipeline_dir=root, project_id=project_id, stage="scene_plan")
    assert loaded["status"] == "completed"
    assert loaded["artifacts"]["scene_plan"]["scenes"][0]["voice_profile_id"] == "sourav_bn"
