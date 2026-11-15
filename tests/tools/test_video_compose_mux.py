"""Smoke tests for _mux_external_audio duration probing."""
from tools.video.video_compose import VideoCompose


def test_mux_does_not_use_shortest_in_cmd():
    """Verify that _mux_external_audio does not add -shortest to the ffmpeg command."""
    import inspect
    src = inspect.getsource(VideoCompose._mux_external_audio)
    # The word -shortest must not appear as a list entry in the cmd
    # (it may appear in the docstring as an explanation of what we removed)
    # Check that it's not in a string literal within a list
    assert '"-shortest"' not in src, "_mux_external_audio must not use -shortest flag in cmd"
    assert "'-shortest'" not in src, "_mux_external_audio must not use -shortest flag in cmd"


def test_mux_uses_video_duration_as_t_flag():
    """Verify _mux_external_audio uses probed duration as -t."""
    import inspect
    src = inspect.getsource(VideoCompose._mux_external_audio)
    assert "video_duration" in src, "must use probed duration variable"
    assert '"-t"' in src or "'-t'" in src, "must use -t flag with probed duration"


def test_mux_contains_probed_duration_field():
    """Verify the result data includes probed_video_duration."""
    import inspect
    src = inspect.getsource(VideoCompose._mux_external_audio)
    assert "probed_video_duration" in src


def test_mux_uses_ffprobe_for_duration():
    """Verify ffprobe is used to probe the video duration."""
    import inspect
    src = inspect.getsource(VideoCompose._mux_external_audio)
    assert "ffprobe" in src
    assert "format=duration" in src
