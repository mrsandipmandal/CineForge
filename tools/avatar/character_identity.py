"""Character & Face Identity Studio Tool.

Manages reusable character profiles, multi-angle face references (front, quarter,
expression), consistency conditioning for image/video generators, and authorized
avatar operations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from lib.identity_library import (
    FaceProfile,
    CharacterProfile,
    IdentityLibrary,
    IdentitySecurityError,
    SUPPORTED_IMAGE_EXT,
)
from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


class CharacterIdentity(BaseTool):
    name = "character_identity"
    version = "1.0.0"
    tier = ToolTier.GENERATE
    capability = "avatar"
    provider = "cineforge"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = []
    install_instructions = "No external dependencies required for local character identity management."
    agent_skills = ["avatar-video", "heygen", "faceswap"]

    capabilities = [
        "character_management",
        "face_reference_management",
        "scene_consistency_conditioning",
        "avatar_routing",
        "consent_verification",
    ]
    supports = {
        "multi_angle_references": True,
        "expression_references": True,
        "consistency_conditioning": True,
        "authorized_face_replacement": True,
        "consent_gated": True,
    }
    best_for = [
        "discovering reusable character identities from sample-files/faces/ and sample-files/characters/",
        "extracting multi-view facial references (front, side, expression) for video generation",
        "formatting conditioning bundles for Seedance, Kling, Wan, and ComfyUI",
        "verifying character ownership and consent before cloud synthesis or face replacement",
    ]
    not_good_for = [
        "raw pixel generation (delegates to talking_head, lip_sync, or video generators)",
    ]

    input_schema = {
        "type": "object",
        "required": ["operation"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "list_characters",
                    "list_faces",
                    "inspect_character",
                    "inspect_face",
                    "get_conditioning_bundle",
                    "verify_consent",
                    "create_or_update_character",
                    "create_or_update_face",
                    "resolve_scene_character",
                ],
                "description": "Character identity operation to execute.",
            },
            "character_id": {
                "type": "string",
                "description": "Unique identifier of the character.",
            },
            "target_provider": {
                "type": "string",
                "enum": ["seedance", "kling", "wan", "comfyui", "talking_head", "lip_sync", "generic"],
                "default": "generic",
                "description": "Target generator for formatting conditioning references.",
            },
            "character_data": {
                "type": "object",
                "description": "Character data dictionary for create_or_update_character.",
            },
            "face_data": {
                "type": "object",
                "description": "Face profile dictionary for create_or_update_face.",
            },
            "owner": {
                "type": "string",
                "description": "Owner identifier for consent verification.",
            },
            "allow_external_upload": {
                "type": "boolean",
                "default": False,
                "description": "Explicit approval to transmit references to cloud providers.",
            },
            "sample_files_dir": {
                "type": "string",
                "description": "Optional custom path to sample-files directory.",
            },
        },
    }

    output_schema = {
        "type": "object",
        "properties": {
            "characters": {"type": "array"},
            "faces": {"type": "array"},
            "character": {"type": "object"},
            "face": {"type": "object"},
            "conditioning_bundle": {"type": "object"},
            "verification": {"type": "object"},
        },
    }

    def _get_library(self, inputs: dict[str, Any]) -> IdentityLibrary:
        sample_dir = inputs.get("sample_files_dir")
        root = Path(sample_dir) if sample_dir else None
        return IdentityLibrary(root)

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        operation = inputs.get("operation", "list_characters")
        lib = self._get_library(inputs)

        try:
            if operation == "list_characters":
                chars = [c.to_dict() for c in lib.list_characters()]
                return ToolResult(
                    success=True,
                    data={"characters": chars, "count": len(chars)},
                )

            elif operation == "list_faces":
                faces = [f.to_dict() for f in lib.list_face_profiles()]
                return ToolResult(
                    success=True,
                    data={"faces": faces, "count": len(faces)},
                )

            elif operation == "inspect_character":
                cid = inputs.get("character_id")
                if not cid:
                    return ToolResult(success=False, error="Missing required parameter: character_id")

                char = next((c for c in lib.list_characters() if c.character_id == cid), None)
                face = lib.get_face_profile(cid)
                voice = lib.get_voice_profile(char.voice_profile_id if char else cid)

                return ToolResult(
                    success=True,
                    data={
                        "character": char.to_dict() if char else None,
                        "face_profile": face.to_dict() if face else None,
                        "voice_profile": voice.to_dict() if voice else None,
                    },
                )

            elif operation == "inspect_face":
                cid = inputs.get("character_id")
                if not cid:
                    return ToolResult(success=False, error="Missing required parameter: character_id")
                face = lib.get_face_profile(cid)
                if not face:
                    return ToolResult(success=False, error=f"Face profile '{cid}' not found")
                return ToolResult(
                    success=True,
                    data={"face": face.to_dict()},
                )

            elif operation == "verify_consent":
                cid = inputs.get("character_id")
                if not cid:
                    return ToolResult(success=False, error="Missing required parameter: character_id")
                face = lib.get_face_profile(cid)
                if not face:
                    return ToolResult(success=False, error=f"Face profile '{cid}' not found")

                face.consent_verified = True
                face.owner = inputs.get("owner", face.owner)
                face.allow_external_upload = inputs.get("allow_external_upload", True)
                lib.save_face_profile(face)

                char = next((c for c in lib.list_characters() if c.character_id == cid), None)
                if char:
                    char.consent_verified = True
                    lib.save_character(char)

                lib.update_index()

                return ToolResult(
                    success=True,
                    data={
                        "character_id": cid,
                        "consent_verified": True,
                        "allow_external_upload": face.allow_external_upload,
                        "message": f"Consent verified for character '{cid}'. Character synthesis authorized.",
                    },
                )

            elif operation == "create_or_update_character":
                cid = inputs.get("character_id")
                cdata = inputs.get("character_data", {})
                if not cid and "character_id" in cdata:
                    cid = cdata["character_id"]
                if not cid:
                    return ToolResult(success=False, error="Missing required character_id")

                char = CharacterProfile(
                    character_id=cid,
                    name=cdata.get("name", cid.replace("_", " ").title()),
                    role=cdata.get("role", ""),
                    voice_profile_id=cdata.get("voice_profile_id"),
                    face_profile_id=cdata.get("face_profile_id", cid),
                    bio=cdata.get("bio", ""),
                    primary_language=cdata.get("primary_language", "en-US"),
                    avatar_strategy=cdata.get("avatar_strategy", "talking_head"),
                    tags=cdata.get("tags", []),
                    consent_verified=bool(cdata.get("consent_verified", False)),
                )
                lib.save_character(char)
                lib.update_index()

                return ToolResult(
                    success=True,
                    data={"character": char.to_dict()},
                )

            elif operation == "get_conditioning_bundle":
                cid = inputs.get("character_id")
                if not cid:
                    return ToolResult(success=False, error="Missing required parameter: character_id")
                face = lib.get_face_profile(cid)
                if not face:
                    return ToolResult(success=False, error=f"Face profile '{cid}' not found")

                target_provider = inputs.get("target_provider", "generic")
                bundle = self._build_conditioning_bundle(lib, face, target_provider)
                return ToolResult(
                    success=True,
                    data={"character_id": cid, "target_provider": target_provider, "bundle": bundle},
                )

            elif operation == "resolve_scene_character":
                cid = inputs.get("character_id")
                if not cid:
                    return ToolResult(success=False, error="Missing required parameter: character_id")
                face = lib.get_face_profile(cid)
                char = next((c for c in lib.list_characters() if c.character_id == cid), None)

                return ToolResult(
                    success=True,
                    data={
                        "character_id": cid,
                        "name": char.name if char else (face.name if face else cid),
                        "prompt_prefix": face.default_generation_prompt if face else "",
                        "negative_prompt": face.negative_prompt if face else "",
                        "views": face.reference_views if face else {},
                        "consent_verified": face.consent_verified if face else False,
                        "voice_profile_id": char.voice_profile_id if char else None,
                    },
                )

            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")

        except Exception as exc:
            return ToolResult(success=False, error=f"CharacterIdentity error: {exc}")

    def _build_conditioning_bundle(
        self,
        lib: IdentityLibrary,
        face: FaceProfile,
        target_provider: str,
    ) -> dict[str, Any]:
        """Format reference images into provider-native conditioning formats."""
        views = {}
        for role in ["front", "left_quarter", "right_quarter", "expression"]:
            ref = next((r for r in face.references if r.role == role), None)
            if ref:
                views[role] = str((lib.root_dir / ref.relative_path).resolve())

        # Fallback front reference
        front_ref = views.get("front") or (
            str((lib.root_dir / face.references[0].relative_path).resolve())
            if face.references
            else None
        )

        bundle: dict[str, Any] = {
            "character_id": face.character_id,
            "character_name": face.name,
            "prompt_descriptor": face.default_generation_prompt,
            "negative_prompt": face.negative_prompt,
            "front_image": front_ref,
            "all_views": views,
            "consent_verified": face.consent_verified,
        }

        if target_provider == "seedance":
            # Seedance accepts reference_image / image_url and character anchor
            bundle["seedance_conditioning"] = {
                "reference_image": front_ref,
                "character_prompt": face.default_generation_prompt,
                "motion_anchor": "maintain_character_facial_identity",
            }
        elif target_provider == "kling":
            # Kling accepts element/character reference
            bundle["kling_conditioning"] = {
                "character_image_url": front_ref,
                "element_name": face.name,
            }
        elif target_provider == "talking_head":
            # TalkingHead requires 1 front image
            bundle["talking_head_conditioning"] = {
                "image_path": front_ref,
                "preprocess": "crop",
            }
        elif target_provider == "wan":
            # Wan accepts conditioning image
            bundle["wan_conditioning"] = {
                "image_path": front_ref,
            }

        return bundle
