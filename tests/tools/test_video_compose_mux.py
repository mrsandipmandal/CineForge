"""Tests for _mux_external_audio — verifies -shortest is not used."""
import inspect
from tools.video.video_compose import VideoCompose


def test_mux_does_not_use_shortest():
    """-shortest must be absent; probed duration must be used instead."""
    src = inspect.getsource(VideoCompose._mux_external_audio)
    assert "-shortest" not in src, "_mux_external_audio must not use -shortest"
    assert "video_duration" in src, "must probe and use video_duration as -t"


def test_mux_method_importable():
    vc = VideoCompose()
    assert callable(vc._mux_external_audio)
