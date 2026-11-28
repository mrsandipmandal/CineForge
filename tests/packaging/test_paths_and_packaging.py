"""Tests for PACKAGE_ROOT vs WORKSPACE_ROOT separation and workspace initialization."""

from __future__ import annotations

import os
from pathlib import Path

from cineforge_cli.core import write_env_keys
from lib.paths import (
    ensure_workspace_initialized,
    get_agent_skills_dir,
    get_package_root,
    get_pipeline_defs_dir,
    get_projects_dir,
    get_schemas_dir,
    get_skills_dir,
    get_styles_dir,
    get_workspace_root,
)


def test_package_assets_resolve_from_repo() -> None:
    pkg = get_package_root()
    assert (pkg / "AGENT_GUIDE.md").is_file()
    assert get_pipeline_defs_dir().is_dir()
    assert get_schemas_dir().is_dir()
    assert get_styles_dir().is_dir()
    assert get_skills_dir().is_dir()
    assert get_agent_skills_dir().is_dir()


def test_workspace_override_via_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CINEFORGE_HOME", str(tmp_path / "custom-ws"))
    monkeypatch.delenv("CINEFORGE_PROJECTS_DIR", raising=False)
    ws = get_workspace_root()
    assert ws == (tmp_path / "custom-ws").resolve()
    assert get_projects_dir() == ws / "projects"


def test_workspace_marker_detected_in_cwd(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CINEFORGE_HOME", raising=False)
    monkeypatch.delenv("CINEFORGE_WORKSPACE", raising=False)
    monkeypatch.delenv("CINEFORGE_PROJECTS_DIR", raising=False)

    ws = ensure_workspace_initialized(tmp_path / "studio-dir")
    assert (ws / ".cineforge").is_dir()
    assert (ws / "projects").is_dir()
    assert (ws / "music_library").is_dir()
    assert (ws / "config.yaml").is_file()
    assert (ws / ".env").is_file()

    sub = ws / "nested" / "folder"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    assert get_workspace_root() == ws


def test_workspace_falls_back_to_home_cineforge(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CINEFORGE_HOME", raising=False)
    monkeypatch.delenv("CINEFORGE_WORKSPACE", raising=False)
    monkeypatch.delenv("CINEFORGE_PROJECTS_DIR", raising=False)

    fake_home = tmp_path / "fake-home"
    outside_dir = tmp_path / "outside"
    fake_home.mkdir()
    outside_dir.mkdir()

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    monkeypatch.chdir(outside_dir)
    assert get_workspace_root() == (fake_home / ".cineforge").resolve()


def test_home_with_dot_cineforge_does_not_hijack_workspace_root(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CINEFORGE_HOME", raising=False)
    monkeypatch.delenv("CINEFORGE_WORKSPACE", raising=False)
    monkeypatch.delenv("CINEFORGE_PROJECTS_DIR", raising=False)

    fake_home = tmp_path / "fake-home"
    (fake_home / ".cineforge").mkdir(parents=True)
    subdir = fake_home / "Downloads"
    subdir.mkdir()

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    for cwd in (fake_home, subdir):
        monkeypatch.chdir(cwd)
        assert get_workspace_root() == (fake_home / ".cineforge").resolve()


def test_env_loader_ignores_blank_assignments_in_cascade(monkeypatch, tmp_path: Path) -> None:
    from lib.env_loader import load_env

    monkeypatch.delenv("FAL_KEY", raising=False)
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)

    first_env = tmp_path / "ws" / ".env"
    second_env = tmp_path / "pkg" / ".env"
    first_env.parent.mkdir(parents=True)
    second_env.parent.mkdir(parents=True)

    first_env.write_text("FAL_KEY=\nPEXELS_API_KEY=\"\"\n", encoding="utf-8")
    second_env.write_text("FAL_KEY=fal_from_pkg\nPEXELS_API_KEY=px_from_pkg\n", encoding="utf-8")

    monkeypatch.setattr("lib.env_loader.get_env_search_paths", lambda: [first_env, second_env])
    load_env()

    assert os.environ.get("FAL_KEY") == "fal_from_pkg"
    assert os.environ.get("PEXELS_API_KEY") == "px_from_pkg"


def test_music_library_falls_back_to_package_when_workspace_empty(monkeypatch, tmp_path: Path) -> None:
    from lib.paths import ensure_workspace_initialized, get_music_library_dir

    ws = ensure_workspace_initialized(tmp_path / "ws")
    assert (ws / "music_library").is_dir()
    pkg = tmp_path / "pkg"
    (pkg / "music_library").mkdir(parents=True)
    (pkg / "music_library" / "theme.mp3").write_bytes(b"ID3test")

    monkeypatch.setenv("CINEFORGE_HOME", str(ws))
    monkeypatch.setattr("lib.paths.get_package_root", lambda: pkg)
    assert get_music_library_dir() == pkg / "music_library"

    (ws / "music_library" / "custom.wav").write_bytes(b"RIFFtest")
    assert get_music_library_dir() == ws / "music_library"


def test_write_env_keys_preserves_existing_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\nEXISTING=keep_me\nFAL_KEY=\n", encoding="utf-8")
    write_env_keys(env_file, {"FAL_KEY": "fal_test_123", "SARVAM_API_KEY": "srv_456"})

    text = env_file.read_text(encoding="utf-8")
    assert "# comment" in text
    assert "EXISTING=keep_me" in text
    assert "FAL_KEY=fal_test_123" in text
    assert "SARVAM_API_KEY=srv_456" in text


def test_write_env_keys_uncomments_and_deduplicates(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# alias header\n"
        "# GEMINI_API_KEY=            # Alias for GOOGLE_API_KEY\n"
        "FAL_KEY=old_one\n"
        "FAL_KEY=old_two\n"
        "# TTS_OFFLINE=true\n",
        encoding="utf-8",
    )
    write_env_keys(
        env_file,
        {
            "GEMINI_API_KEY": "AIzaUncommented123",
            "FAL_KEY": "fal_fresh_999",
            "TTS_OFFLINE": "false",
        },
    )

    text = env_file.read_text(encoding="utf-8")
    assert "# alias header" in text
    assert "GEMINI_API_KEY=AIzaUncommented123" in text
    assert "# GEMINI_API_KEY=" not in text
    assert text.count("FAL_KEY=") == 1
    assert "FAL_KEY=fal_fresh_999" in text
    assert "TTS_OFFLINE=false" in text
    assert "# TTS_OFFLINE=" not in text
