"""Tests for media profile helpers."""
import pytest
from lib.media_profiles import get_lufs_target, get_crf_for_profile, get_profile, ALL_PROFILES


def test_youtube_lufs_target():
    assert get_lufs_target("youtube_landscape") == -14.0
    assert get_lufs_target("youtube_4k") == -14.0
    assert get_lufs_target("youtube_shorts") == -14.0


def test_cinematic_lufs_broadcast():
    assert get_lufs_target("cinematic") == -23.0


def test_linkedin_lufs():
    assert get_lufs_target("linkedin") == -16.0


def test_unknown_profile_lufs_fallback():
    assert get_lufs_target("unknown_platform") == -16.0


def test_custom_fallback():
    assert get_lufs_target("nonexistent", default=-18.0) == -18.0


def test_crf_youtube():
    crf = get_crf_for_profile("youtube_landscape")
    assert crf == 18  # YouTube profile has crf=18


def test_crf_generic_hd():
    crf = get_crf_for_profile("generic_hd")
    assert crf == 23


def test_crf_unknown_fallback():
    crf = get_crf_for_profile("nonexistent_profile")
    assert crf == 23  # falls back to global default


def test_all_profiles_have_lufs_entries():
    """Every registered profile should have a LUFS entry."""
    from lib.media_profiles import PLATFORM_LUFS
    missing = [name for name in ALL_PROFILES if name not in PLATFORM_LUFS]
    assert not missing, f"Profiles missing LUFS entries: {missing}"
