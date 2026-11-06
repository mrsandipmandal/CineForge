"""Voice Identity Management Tool.

Discovers, inspects, validates, and prepares reusable voice profiles from
`sample-files/voices/` for text-to-speech and voice cloning pipelines.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from lib.identity_library import (
    IdentityLibrary,
    IdentitySecurityError,
    VoiceProfile,
    SUPPORTED_AUDIO_EXT,
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


class VoiceIdentity(BaseTool):
    name = "voice_identity"
    version = "1.0.0"
    tier = ToolTier.VOICE
    capability = "voice_identity"
    provider = "cineforge"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = []
    install_instructions = "No external dependencies required for local voice identity management."
    agent_skills = ["elevenlabs", "text-to-speech", "azure-text-to-speech", "fish-audio-tts"]

    capabilities = [
        "voice_discovery",
        "voice_profiling",
        "voice_validation",
        "consent_verification",
        "voice_routing",
    ]
    supports = {
        "voice_cloning": True,
        "multilingual": True,
        "bengali": True,
        "hindi": True,
        "english": True,
        "offline": True,
        "consent_gated": True,
    }
    best_for = [
        "discovering reusable voice profiles from sample-files/voices/",
        "verifying voice ownership and consent before cloning",
        "routing multilingual scripts (Bengali, Hindi, English) to capable TTS providers",
        "preparing audio reference samples for voice cloning",
    ]
    not_good_for = [
        "raw audio synthesis (delegates to concrete TTS providers)",
    ]

    input_schema = {
        "type": "object",
        "required": ["operation"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["list", "inspect", "validate", "verify_consent", "create_or_update", "route_voice", "prepare_reference"],
                "description": "Voice identity management operation to execute.",
            },
            "profile_id": {
                "type": "string",
                "description": "Unique identifier of the voice profile.",
            },
            "language": {
                "type": "string",
                "description": "Target language BCP-47 code (e.g. bn-IN, hi-IN, en-US).",
            },
            "require_cloning": {
                "type": "boolean",
                "default": False,
                "description": "Whether the voice requires true reference audio voice cloning.",
            },
            "voice_data": {
                "type": "object",
                "description": "Metadata dictionary for create_or_update operation.",
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
            "profiles": {"type": "array"},
            "profile": {"type": "object"},
            "route": {"type": "object"},
            "validation": {"type": "object"},
        },
    }

    def _get_library(self, inputs: dict[str, Any]) -> IdentityLibrary:
        sample_dir = inputs.get("sample_files_dir")
        root = Path(sample_dir) if sample_dir else None
        return IdentityLibrary(root)

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        operation = inputs.get("operation", "list")
        lib = self._get_library(inputs)

        try:
            if operation == "list":
                profiles = [p.to_dict() for p in lib.list_voice_profiles()]
                lang_filter = inputs.get("language")
                if lang_filter:
                    profiles = [
                        p for p in profiles
                        if lang_filter in p.get("supported_languages", [])
                        or lang_filter.split("-")[0] in [l.split("-")[0] for l in p.get("supported_languages", [])]
                    ]
                return ToolResult(
                    success=True,
                    data={"profiles": profiles, "count": len(profiles)},
                )

            elif operation == "inspect":
                pid = inputs.get("profile_id")
                if not pid:
                    return ToolResult(success=False, error="Missing required parameter: profile_id")
                profile = lib.get_voice_profile(pid)
                if not profile:
                    return ToolResult(success=False, error=f"Voice profile '{pid}' not found in {lib.voices_dir}")
                return ToolResult(
                    success=True,
                    data={"profile": profile.to_dict()},
                )

            elif operation == "validate":
                pid = inputs.get("profile_id")
                if not pid:
                    return ToolResult(success=False, error="Missing required parameter: profile_id")
                profile = lib.get_voice_profile(pid)
                if not profile:
                    return ToolResult(success=False, error=f"Voice profile '{pid}' not found")

                issues = []
                if not profile.samples:
                    issues.append("No audio samples found in samples/ directory.")
                total_duration = sum(s.duration_seconds for s in profile.samples)
                if profile.samples and total_duration < 3.0:
                    issues.append(f"Sample audio duration ({total_duration:.1f}s) is short; at least 5-10s recommended for cloning.")
                if not profile.consent_verified:
                    issues.append("Consent not verified: User authorization required before cloning.")

                return ToolResult(
                    success=True,
                    data={
                        "profile_id": pid,
                        "valid": len(issues) == 0,
                        "issues": issues,
                        "samples_count": len(profile.samples),
                        "total_duration_seconds": total_duration,
                        "consent_verified": profile.consent_verified,
                    },
                )

            elif operation == "verify_consent":
                pid = inputs.get("profile_id")
                if not pid:
                    return ToolResult(success=False, error="Missing required parameter: profile_id")
                profile = lib.get_voice_profile(pid)
                if not profile:
                    return ToolResult(success=False, error=f"Voice profile '{pid}' not found")

                profile.consent_verified = True
                profile.owner = inputs.get("owner", profile.owner)
                profile.allow_external_upload = inputs.get("allow_external_upload", True)
                lib.save_voice_profile(profile)
                lib.update_index()

                return ToolResult(
                    success=True,
                    data={
                        "profile_id": pid,
                        "consent_verified": True,
                        "allow_external_upload": profile.allow_external_upload,
                        "message": f"Consent verified for voice profile '{pid}'. Voice cloning authorized.",
                    },
                )

            elif operation == "create_or_update":
                pid = inputs.get("profile_id")
                data = inputs.get("voice_data", {})
                if not pid and "profile_id" in data:
                    pid = data["profile_id"]
                if not pid:
                    return ToolResult(success=False, error="Missing required profile_id")

                existing = lib.get_voice_profile(pid)
                profile = VoiceProfile(
                    profile_id=pid,
                    name=data.get("name", existing.name if existing else pid.replace("_", " ").title()),
                    description=data.get("description", existing.description if existing else ""),
                    gender=data.get("gender", existing.gender if existing else "neutral"),
                    primary_language=data.get("primary_language", existing.primary_language if existing else "en-US"),
                    supported_languages=data.get("supported_languages", existing.supported_languages if existing else ["en-US"]),
                    voice_type=data.get("voice_type", existing.voice_type if existing else "narration"),
                    recommended_providers=data.get("recommended_providers", existing.recommended_providers if existing else []),
                    pitch_semitones=float(data.get("pitch_semitones", existing.pitch_semitones if existing else 0.0)),
                    default_speaking_rate=float(data.get("default_speaking_rate", existing.default_speaking_rate if existing else 1.0)),
                    consent_verified=bool(data.get("consent_verified", existing.consent_verified if existing else False)),
                    owner=data.get("owner", existing.owner if existing else "local_user"),
                    allow_external_upload=bool(data.get("allow_external_upload", existing.allow_external_upload if existing else False)),
                )
                lib.save_voice_profile(profile)
                lib.update_index()

                return ToolResult(
                    success=True,
                    data={"profile": profile.to_dict()},
                )

            elif operation == "route_voice":
                language = inputs.get("language", "en-US")
                require_cloning = inputs.get("require_cloning", False)
                pid = inputs.get("profile_id")

                selected_profile: Optional[VoiceProfile] = None
                if pid:
                    selected_profile = lib.get_voice_profile(pid)

                # Match profile by language if not specified
                if not selected_profile:
                    for p in lib.list_voice_profiles():
                        if language in p.supported_languages or language.split("-")[0] in [l.split("-")[0] for l in p.supported_languages]:
                            selected_profile = p
                            break

                # Resolve recommended provider
                route = self._resolve_routing(language, require_cloning, selected_profile)
                return ToolResult(
                    success=True,
                    data=route,
                )

            elif operation == "prepare_reference":
                pid = inputs.get("profile_id")
                if not pid:
                    return ToolResult(success=False, error="Missing required parameter: profile_id")
                profile = lib.get_voice_profile(pid)
                if not profile:
                    return ToolResult(success=False, error=f"Voice profile '{pid}' not found")
                if not profile.consent_verified:
                    return ToolResult(
                        success=False,
                        error=f"Consent not verified for voice profile '{pid}'. Cannot prepare reference audio for cloning without consent.",
                    )
                if not profile.samples:
                    return ToolResult(
                        success=False,
                        error=f"No audio samples available in voice profile '{pid}'. Please add reference audio to {pid}/samples/.",
                    )

                # Pick the longest or best sample
                best_sample = max(profile.samples, key=lambda s: s.duration_seconds)
                full_sample_path = (lib.root_dir / best_sample.relative_path).resolve()

                return ToolResult(
                    success=True,
                    data={
                        "profile_id": pid,
                        "reference_audio_path": str(full_sample_path),
                        "duration_seconds": best_sample.duration_seconds,
                        "sample_rate": best_sample.sample_rate,
                        "format": best_sample.format,
                        "consent_verified": True,
                    },
                    artifacts=[str(full_sample_path)],
                )

            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")

        except Exception as exc:
            return ToolResult(success=False, error=f"VoiceIdentity error: {exc}")

    def _resolve_routing(
        self,
        language: str,
        require_cloning: bool,
        profile: Optional[VoiceProfile],
    ) -> dict[str, Any]:
        """Determine the optimal TTS provider and settings for a language and profile."""
        lang_lower = language.lower()
        is_bengali = "bn" in lang_lower
        is_hindi = "hi" in lang_lower

        if is_bengali:
            if require_cloning:
                # Bengali voice cloning requires models that support Bengali acoustic conditioning
                return {
                    "language": "bn-IN",
                    "requires_cloning": True,
                    "recommended_tool": "fish_audio_tts",
                    "recommended_model": "s2.1-pro",
                    "fallback_tool": "elevenlabs_tts",
                    "fallback_model": "eleven_multilingual_v2",
                    "pitch": profile.pitch_semitones if profile else 0.0,
                    "speed": profile.default_speaking_rate if profile else 1.0,
                    "notes": "Native Bengali pronunciation and script preserved via Fish Audio S2.1 or ElevenLabs Multilingual v2.",
                }
            else:
                # Bengali standard TTS
                return {
                    "language": "bn-IN",
                    "requires_cloning": False,
                    "recommended_tool": "azure_tts",
                    "recommended_voice": "bn-IN-BashkarNeural",
                    "fallback_tool": "google_tts",
                    "fallback_voice": "bn-IN-Standard-A",
                    "notes": "High-fidelity native Bengali neural synthesis.",
                }

        elif is_hindi:
            if require_cloning:
                return {
                    "language": "hi-IN",
                    "requires_cloning": True,
                    "recommended_tool": "elevenlabs_tts",
                    "recommended_model": "eleven_multilingual_v2",
                    "fallback_tool": "fish_audio_tts",
                    "notes": "Hindi voice cloning via ElevenLabs Multilingual v2 or Fish Audio.",
                }
            else:
                return {
                    "language": "hi-IN",
                    "requires_cloning": False,
                    "recommended_tool": "azure_tts",
                    "recommended_voice": "hi-IN-MadhurNeural",
                    "fallback_tool": "google_tts",
                    "fallback_voice": "hi-IN-Neural2-A",
                    "notes": "Native Hindi neural synthesis.",
                }

        else:
            # Default / English
            if require_cloning:
                return {
                    "language": language or "en-US",
                    "requires_cloning": True,
                    "recommended_tool": "elevenlabs_tts",
                    "recommended_model": "eleven_multilingual_v2",
                    "fallback_tool": "fish_audio_tts",
                    "notes": "English voice cloning via ElevenLabs.",
                }
            else:
                return {
                    "language": language or "en-US",
                    "requires_cloning": False,
                    "recommended_tool": "elevenlabs_tts",
                    "fallback_tool": "azure_tts",
                    "notes": "Standard English narration.",
                }
