"""Identity Library — Local-First Voice and Face Management.

Provides scanning, validation, metadata extraction, duplicate detection,
thumbnail generation, and safe resolution of reusable voice and character
identities located in `sample-files/`.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from lib.paths import REPO_ROOT

DEFAULT_SAMPLE_DIR = REPO_ROOT / "sample-files"
SUPPORTED_AUDIO_EXT = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
SUPPORTED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
MAX_SAMPLE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit per sample file


class IdentitySecurityError(PermissionError):
    """Raised when an operation violates sandbox boundaries or consent rules."""


@dataclass
class AudioSampleMeta:
    filename: str
    relative_path: str
    file_size: int
    sha256: str
    duration_seconds: float = 0.0
    sample_rate: int = 0
    channels: int = 1
    format: str = ""
    valid: bool = True
    error: Optional[str] = None


@dataclass
class VoiceProfile:
    profile_id: str
    name: str
    description: str = ""
    gender: str = "neutral"
    primary_language: str = "en-US"
    supported_languages: list[str] = field(default_factory=lambda: ["en-US"])
    voice_type: str = "narration"
    recommended_providers: list[str] = field(default_factory=list)
    pitch_semitones: float = 0.0
    default_speaking_rate: float = 1.0
    consent_verified: bool = False
    owner: str = "local_user"
    allow_external_upload: bool = False
    samples: list[AudioSampleMeta] = field(default_factory=list)
    created_at: str = ""
    metadata_path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


@dataclass
class ImageReferenceMeta:
    filename: str
    relative_path: str
    file_size: int
    sha256: str
    role: str = "front"  # front, left_quarter, right_quarter, expression, reference
    width: int = 0
    height: int = 0
    format: str = ""
    thumbnail_path: Optional[str] = None
    valid: bool = True
    error: Optional[str] = None


@dataclass
class FaceProfile:
    character_id: str
    name: str
    description: str = ""
    gender: str = "neutral"
    ethnicity_or_style: str = "contemporary"
    default_generation_prompt: str = ""
    negative_prompt: str = ""
    consent_verified: bool = False
    owner: str = "local_user"
    allow_external_upload: bool = False
    references: list[ImageReferenceMeta] = field(default_factory=list)
    reference_views: dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    metadata_path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


@dataclass
class CharacterProfile:
    character_id: str
    name: str
    role: str = ""
    voice_profile_id: Optional[str] = None
    face_profile_id: Optional[str] = None
    bio: str = ""
    primary_language: str = "en-US"
    avatar_strategy: str = "talking_head"
    tags: list[str] = field(default_factory=list)
    consent_verified: bool = False
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IdentityLibrary:
    """Manager and scanner for the local sample-files identity library."""

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = (root_dir or DEFAULT_SAMPLE_DIR).resolve()
        self.voices_dir = self.root_dir / "voices"
        self.faces_dir = self.root_dir / "faces"
        self.characters_dir = self.root_dir / "characters"
        self.manifests_dir = self.root_dir / "manifests"

    def ensure_directories(self) -> None:
        """Create sample-files directory structure if absent."""
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        self.faces_dir.mkdir(parents=True, exist_ok=True)
        self.characters_dir.mkdir(parents=True, exist_ok=True)
        self.manifests_dir.mkdir(parents=True, exist_ok=True)

    def _safe_resolve(self, relative_path: str | Path) -> Path:
        """Sanitize path to ensure it cannot escape root_dir sandbox."""
        resolved = (self.root_dir / relative_path).resolve()
        try:
            resolved.relative_to(self.root_dir)
        except ValueError:
            raise IdentitySecurityError(
                f"Path traversal detected: {relative_path} escapes identity root {self.root_dir}"
            )
        return resolved

    @staticmethod
    def _compute_sha256(file_path: Path) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def probe_audio(self, file_path: Path) -> AudioSampleMeta:
        """Extract duration, sample rate, channels, and hash from an audio file."""
        stat = file_path.stat()
        file_size = stat.st_size
        sha256 = self._compute_sha256(file_path)
        rel = file_path.resolve().relative_to(self.root_dir).as_posix()

        if file_size > MAX_SAMPLE_SIZE_BYTES:
            return AudioSampleMeta(
                filename=file_path.name,
                relative_path=rel,
                file_size=file_size,
                sha256=sha256,
                valid=False,
                error=f"File exceeds maximum allowed size ({file_size} > {MAX_SAMPLE_SIZE_BYTES})",
            )

        duration = 0.0
        sample_rate = 0
        channels = 1
        fmt = file_path.suffix.lstrip(".").lower()

        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "stream=channels,sample_rate,duration:format=duration,format_name",
                "-of", "json",
                str(file_path),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                info = json.loads(res.stdout)
                streams = info.get("streams", [])
                if streams:
                    s = streams[0]
                    channels = int(s.get("channels") or 1)
                    sample_rate = int(s.get("sample_rate") or 0)
                    duration = float(s.get("duration") or info.get("format", {}).get("duration") or 0.0)
                else:
                    duration = float(info.get("format", {}).get("duration") or 0.0)
                fmt = info.get("format", {}).get("format_name", fmt).split(",")[0]
        except Exception as e:
            # Fallback for systems without ffprobe or probe failure
            pass

        if duration == 0.0:
            if fmt == "wav":
                try:
                    import wave
                    with wave.open(str(file_path), "rb") as wf:
                        channels = wf.getnchannels()
                        sample_rate = wf.getframerate()
                        frames = wf.getnframes()
                        if sample_rate > 0:
                            duration = frames / float(sample_rate)
                except Exception:
                    pass
            elif fmt == "mp3":
                try:
                    with open(file_path, "rb") as mf:
                        data = mf.read(4096)
                    offset = 0
                    if data.startswith(b"ID3"):
                        tag_size = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
                        offset = 10 + tag_size
                    with open(file_path, "rb") as mf:
                        mf.seek(offset)
                        hdr = mf.read(4)
                        if len(hdr) == 4 and hdr[0] == 0xFF and (hdr[1] & 0xE0) == 0xE0:
                            bitrate_idx = (hdr[2] >> 4) & 0xF
                            sr_idx = (hdr[2] >> 2) & 0x3
                            bitrates_v1_l3 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
                            rates = [44100, 48000, 32000]
                            if bitrate_idx < len(bitrates_v1_l3) and sr_idx < len(rates):
                                br = bitrates_v1_l3[bitrate_idx] * 1000
                                sample_rate = rates[sr_idx]
                                audio_bytes = file_size - offset
                                if br > 0:
                                    duration = (audio_bytes * 8.0) / br
                    if duration == 0.0:
                        duration = round(file_size / 16000.0, 2)
                        sample_rate = 44100
                except Exception:
                    pass

        return AudioSampleMeta(
            filename=file_path.name,
            relative_path=rel,
            file_size=file_size,
            sha256=sha256,
            duration_seconds=round(duration, 3),
            sample_rate=sample_rate,
            channels=channels,
            format=fmt,
            valid=True,
        )

    def probe_image(self, file_path: Path, character_dir: Optional[Path] = None) -> ImageReferenceMeta:
        """Extract resolution, format, hash and generate thumbnail."""
        stat = file_path.stat()
        file_size = stat.st_size
        sha256 = self._compute_sha256(file_path)
        rel = file_path.resolve().relative_to(self.root_dir).as_posix()

        if file_size > MAX_SAMPLE_SIZE_BYTES:
            return ImageReferenceMeta(
                filename=file_path.name,
                relative_path=rel,
                file_size=file_size,
                sha256=sha256,
                valid=False,
                error=f"File exceeds maximum allowed size ({file_size} > {MAX_SAMPLE_SIZE_BYTES})",
            )

        width = 0
        height = 0
        fmt = file_path.suffix.lstrip(".").lower()

        try:
            from PIL import Image
            with Image.open(file_path) as img:
                width, height = img.size
                fmt = img.format.lower() if img.format else fmt
        except Exception:
            try:
                cmd = [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height,codec_name",
                    "-of", "json",
                    str(file_path),
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if res.returncode == 0:
                    info = json.loads(res.stdout)
                    streams = info.get("streams", [])
                    if streams:
                        width = int(streams[0].get("width") or 0)
                        height = int(streams[0].get("height") or 0)
            except Exception:
                pass

        # Thumbnail generation
        thumb_rel: Optional[str] = None
        if character_dir and width > 0:
            thumb_dir = character_dir / "thumbnails"
            thumb_dir.mkdir(parents=True, exist_ok=True)
            thumb_target = thumb_dir / f"{file_path.stem}_thumb.jpg"
            if not thumb_target.is_file():
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        img = img.convert("RGB")
                        img.thumbnail((320, 320))
                        img.save(thumb_target, "JPEG", quality=85)
                except Exception:
                    pass
            if thumb_target.is_file():
                thumb_rel = thumb_target.resolve().relative_to(self.root_dir).as_posix()

        # Infer role from filename
        name_lower = file_path.stem.lower()
        role = "reference"
        if "front" in name_lower:
            role = "front"
        elif "left" in name_lower:
            role = "left_quarter"
        elif "right" in name_lower:
            role = "right_quarter"
        elif "express" in name_lower or "smile" in name_lower:
            role = "expression"

        return ImageReferenceMeta(
            filename=file_path.name,
            relative_path=rel,
            file_size=file_size,
            sha256=sha256,
            role=role,
            width=width,
            height=height,
            format=fmt,
            thumbnail_path=thumb_rel,
            valid=True,
        )

    # -----------------------------------------------------------------------
    # Voice Operations
    # -----------------------------------------------------------------------

    def list_voice_profiles(self) -> list[VoiceProfile]:
        """Scan voices/ and return all discovered VoiceProfiles."""
        self.ensure_directories()
        profiles = []
        for entry in sorted(self.voices_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith((".", "_")):
                continue
            profile = self.get_voice_profile(entry.name)
            if profile:
                profiles.append(profile)
        return profiles

    def get_voice_profile(self, profile_id: str) -> Optional[VoiceProfile]:
        """Load a specific voice profile by profile_id."""
        profile_dir = self.voices_dir / profile_id
        if not profile_dir.is_dir():
            return None

        meta_file = profile_dir / "metadata.json"
        raw_meta: dict[str, Any] = {}
        if meta_file.is_file():
            try:
                with open(meta_file, encoding="utf-8") as f:
                    raw_meta = json.load(f)
            except Exception:
                pass

        samples_dir = profile_dir / "samples"
        samples = []
        if samples_dir.is_dir():
            for sample_file in sorted(samples_dir.iterdir()):
                if sample_file.is_file() and sample_file.suffix.lower() in SUPPORTED_AUDIO_EXT:
                    samples.append(self.probe_audio(sample_file))

        return VoiceProfile(
            profile_id=profile_id,
            name=raw_meta.get("name", profile_id.replace("_", " ").title()),
            description=raw_meta.get("description", ""),
            gender=raw_meta.get("gender", "neutral"),
            primary_language=raw_meta.get("primary_language", "en-US"),
            supported_languages=raw_meta.get("supported_languages", [raw_meta.get("primary_language", "en-US")]),
            voice_type=raw_meta.get("voice_type", "narration"),
            recommended_providers=raw_meta.get("recommended_providers", []),
            pitch_semitones=float(raw_meta.get("pitch_semitones", 0.0)),
            default_speaking_rate=float(raw_meta.get("default_speaking_rate", 1.0)),
            consent_verified=bool(raw_meta.get("consent_verified", False)),
            owner=raw_meta.get("owner", "local_user"),
            allow_external_upload=bool(raw_meta.get("allow_external_upload", False)),
            samples=samples,
            created_at=raw_meta.get("created_at", datetime.now(timezone.utc).isoformat()),
            metadata_path=(meta_file.relative_to(self.root_dir).as_posix() if meta_file.is_file() else None),
        )

    def save_voice_profile(self, profile: VoiceProfile) -> None:
        """Persist metadata for a voice profile."""
        profile_dir = self.voices_dir / profile.profile_id
        profile_dir.mkdir(parents=True, exist_ok=True)
        (profile_dir / "samples").mkdir(parents=True, exist_ok=True)

        meta = {
            "profile_id": profile.profile_id,
            "name": profile.name,
            "description": profile.description,
            "gender": profile.gender,
            "primary_language": profile.primary_language,
            "supported_languages": profile.supported_languages,
            "voice_type": profile.voice_type,
            "recommended_providers": profile.recommended_providers,
            "pitch_semitones": profile.pitch_semitones,
            "default_speaking_rate": profile.default_speaking_rate,
            "consent_verified": profile.consent_verified,
            "owner": profile.owner,
            "allow_external_upload": profile.allow_external_upload,
            "created_at": profile.created_at or datetime.now(timezone.utc).isoformat(),
        }
        with open(profile_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    # -----------------------------------------------------------------------
    # Face & Character Operations
    # -----------------------------------------------------------------------

    def list_face_profiles(self) -> list[FaceProfile]:
        """Scan faces/ and return all discovered FaceProfiles."""
        self.ensure_directories()
        profiles = []
        for entry in sorted(self.faces_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith((".", "_")):
                continue
            profile = self.get_face_profile(entry.name)
            if profile:
                profiles.append(profile)
        return profiles

    def get_face_profile(self, character_id: str) -> Optional[FaceProfile]:
        """Load a specific face profile by character_id."""
        char_dir = self.faces_dir / character_id
        if not char_dir.is_dir():
            return None

        meta_file = char_dir / "metadata.json"
        raw_meta: dict[str, Any] = {}
        if meta_file.is_file():
            try:
                with open(meta_file, encoding="utf-8") as f:
                    raw_meta = json.load(f)
            except Exception:
                pass

        ref_dir = char_dir / "references"
        references = []
        if ref_dir.is_dir():
            for ref_file in sorted(ref_dir.iterdir()):
                if ref_file.is_file() and ref_file.suffix.lower() in SUPPORTED_IMAGE_EXT:
                    references.append(self.probe_image(ref_file, character_dir=char_dir))

        return FaceProfile(
            character_id=character_id,
            name=raw_meta.get("name", character_id.replace("_", " ").title()),
            description=raw_meta.get("description", ""),
            gender=raw_meta.get("gender", "neutral"),
            ethnicity_or_style=raw_meta.get("ethnicity_or_style", "contemporary"),
            default_generation_prompt=raw_meta.get("default_generation_prompt", ""),
            negative_prompt=raw_meta.get("negative_prompt", ""),
            consent_verified=bool(raw_meta.get("consent_verified", False)),
            owner=raw_meta.get("owner", "local_user"),
            allow_external_upload=bool(raw_meta.get("allow_external_upload", False)),
            references=references,
            reference_views=raw_meta.get("reference_views", {}),
            created_at=raw_meta.get("created_at", datetime.now(timezone.utc).isoformat()),
            metadata_path=(meta_file.relative_to(self.root_dir).as_posix() if meta_file.is_file() else None),
        )

    def save_face_profile(self, profile: FaceProfile) -> None:
        """Persist metadata for a face profile."""
        char_dir = self.faces_dir / profile.character_id
        char_dir.mkdir(parents=True, exist_ok=True)
        (char_dir / "references").mkdir(parents=True, exist_ok=True)
        (char_dir / "thumbnails").mkdir(parents=True, exist_ok=True)

        meta = {
            "character_id": profile.character_id,
            "name": profile.name,
            "description": profile.description,
            "gender": profile.gender,
            "ethnicity_or_style": profile.ethnicity_or_style,
            "default_generation_prompt": profile.default_generation_prompt,
            "negative_prompt": profile.negative_prompt,
            "reference_views": profile.reference_views,
            "consent_verified": profile.consent_verified,
            "owner": profile.owner,
            "allow_external_upload": profile.allow_external_upload,
            "created_at": profile.created_at or datetime.now(timezone.utc).isoformat(),
        }
        with open(char_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    # -----------------------------------------------------------------------
    # Unified Characters
    # -----------------------------------------------------------------------

    def list_characters(self) -> list[CharacterProfile]:
        """Return all unified character profiles in characters/."""
        self.ensure_directories()
        chars = []
        for file in sorted(self.characters_dir.glob("*.json")):
            try:
                with open(file, encoding="utf-8") as f:
                    data = json.load(f)
                chars.append(
                    CharacterProfile(
                        character_id=data.get("character_id", file.stem),
                        name=data.get("name", file.stem.title()),
                        role=data.get("role", ""),
                        voice_profile_id=data.get("voice_profile_id"),
                        face_profile_id=data.get("face_profile_id"),
                        bio=data.get("bio", ""),
                        primary_language=data.get("primary_language", "en-US"),
                        avatar_strategy=data.get("avatar_strategy", "talking_head"),
                        tags=data.get("tags", []),
                        consent_verified=bool(data.get("consent_verified", False)),
                        created_at=data.get("created_at", ""),
                    )
                )
            except Exception:
                continue
        return chars

    def save_character(self, char: CharacterProfile) -> None:
        self.characters_dir.mkdir(parents=True, exist_ok=True)
        out_file = self.characters_dir / f"{char.character_id}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(char.to_dict(), f, indent=2)

    # -----------------------------------------------------------------------
    # Catalog Index Manifest
    # -----------------------------------------------------------------------

    def update_index(self) -> dict[str, Any]:
        """Re-scan all identity components and write manifests/identity-index.json."""
        self.ensure_directories()
        voices = self.list_voice_profiles()
        faces = self.list_face_profiles()
        characters = self.list_characters()

        index_data = {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "voices": [
                {
                    "profile_id": v.profile_id,
                    "name": v.name,
                    "primary_language": v.primary_language,
                    "supported_languages": v.supported_languages,
                    "voice_type": v.voice_type,
                    "samples_count": len(v.samples),
                    "consent_verified": v.consent_verified,
                }
                for v in voices
            ],
            "faces": [
                {
                    "character_id": f.character_id,
                    "name": f.name,
                    "references_count": len(f.references),
                    "consent_verified": f.consent_verified,
                }
                for f in faces
            ],
            "characters": [c.to_dict() for c in characters],
        }

        index_file = self.manifests_dir / "identity-index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2)

        return index_data

    # -----------------------------------------------------------------------
    # Project-Local Identity Resolution
    # -----------------------------------------------------------------------

    def link_to_project(
        self,
        project_dir: Path,
        voice_id: Optional[str] = None,
        character_id: Optional[str] = None,
        require_consent: bool = True,
    ) -> dict[str, Any]:
        """Export identity references into projects/<id>/assets/identities/."""
        project_dir = Path(project_dir).resolve()
        ident_dir = project_dir / "assets" / "identities"
        ident_dir.mkdir(parents=True, exist_ok=True)

        res: dict[str, Any] = {"voice": None, "face": None, "character": None}

        if voice_id:
            voice = self.get_voice_profile(voice_id)
            if not voice:
                raise ValueError(f"Voice profile not found: {voice_id}")
            if require_consent and not voice.consent_verified:
                raise IdentitySecurityError(
                    f"Consent not verified for voice profile {voice_id}. Authorization required."
                )
            v_dir = ident_dir / "voice" / voice.profile_id
            v_dir.mkdir(parents=True, exist_ok=True)
            with open(v_dir / "profile.json", "w", encoding="utf-8") as f:
                json.dump(voice.to_dict(), f, indent=2)
            res["voice"] = voice.to_dict()

        if character_id:
            face = self.get_face_profile(character_id)
            if face:
                if require_consent and not face.consent_verified:
                    raise IdentitySecurityError(
                        f"Consent not verified for character profile {character_id}. Authorization required."
                    )
                f_dir = ident_dir / "face" / face.character_id
                f_dir.mkdir(parents=True, exist_ok=True)
                with open(f_dir / "profile.json", "w", encoding="utf-8") as f:
                    json.dump(face.to_dict(), f, indent=2)
                res["face"] = face.to_dict()

        return res
