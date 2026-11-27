"""Tests for ClipCache stale-lock recovery (tools/video/clip_cache.py)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from tools.video.clip_cache import ClipCache


def test_stale_lock_is_removed_on_construction(tmp_path):
    """A lock file older than 600 seconds must be deleted when ClipCache is created."""
    lock_path = tmp_path / "cache_manifest.lock"
    lock_path.write_bytes(b"")  # Create the lock

    # Back-date the mtime by 700 seconds (> 600 s threshold).
    stale_mtime = time.time() - 700
    import os
    os.utime(str(lock_path), (stale_mtime, stale_mtime))

    assert lock_path.exists(), "Lock should exist before ClipCache construction."
    # Constructing ClipCache should clear the stale lock.
    ClipCache(cache_dir=tmp_path)
    assert not lock_path.exists(), "Stale lock should have been removed by ClipCache.__init__."


def test_fresh_lock_is_not_removed_on_construction(tmp_path):
    """A lock file created recently (< 600 s) must NOT be deleted."""
    lock_path = tmp_path / "cache_manifest.lock"
    lock_path.write_bytes(b"")
    # Fresh lock — mtime is now (< 600 s ago).

    ClipCache(cache_dir=tmp_path)
    # Fresh lock should survive construction.
    assert lock_path.exists(), "A fresh lock must not be removed by ClipCache.__init__."


def test_missing_lock_does_not_raise(tmp_path):
    """Constructing ClipCache when no lock file exists must not raise."""
    lock_path = tmp_path / "cache_manifest.lock"
    assert not lock_path.exists()
    # Should not raise.
    cache = ClipCache(cache_dir=tmp_path)
    assert cache.lock_path == lock_path


def test_stale_lock_does_not_block_ingest(tmp_path):
    """After stale-lock removal, a simple cache ingest/try_link round-trip must succeed."""
    lock_path = tmp_path / "cache_manifest.lock"
    lock_path.write_bytes(b"")
    stale_mtime = time.time() - 700
    import os
    os.utime(str(lock_path), (stale_mtime, stale_mtime))

    cache = ClipCache(cache_dir=tmp_path, max_total_bytes=50 * 1024 * 1024)
    dummy = tmp_path / "dummy_clip.mp4"
    dummy.write_bytes(b"\x00" * 2048)  # 2 KB — well above _MIN_USABLE_BYTES

    ok = cache.ingest("clip-stale-test", dummy, metadata={"source": "test"})
    assert ok is True
    dest = tmp_path / "linked_clip.mp4"
    assert cache.try_link("clip-stale-test", dest) is True
    assert dest.exists()
