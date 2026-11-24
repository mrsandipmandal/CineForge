import json
import pytest
from pathlib import Path
from tools.render.remotion_episode_builder import RemotionEpisodeBuilder

def test_remotion_episode_builder_generates_files(tmp_path):
    project_dir = tmp_path
    (project_dir / "assets").mkdir()
    
    # Create dummy scene files
    (project_dir / "assets" / "scene1.jpg").write_text("dummy")
    
    builder = RemotionEpisodeBuilder(project_dir)
    scenes = [
        {"id": "1", "source": project_dir / "assets" / "scene1.jpg", "duration": 3.0, "motion": "ken-burns-slow-zoom"}
    ]
    subtitles = [
        {"text": "Hello", "start": 0.0, "end": 3.0}
    ]
    
    result = builder.build(scenes, subtitles)
    
    assert (project_dir / "artifacts" / "edit_decisions.json").exists()
    assert (project_dir / "artifacts" / "asset_manifest.json").exists()
    assert (project_dir / "assets" / "subtitles.srt").exists()
    
    edit_decisions = json.load(open(project_dir / "artifacts" / "edit_decisions.json"))
    assert edit_decisions["cuts"][0]["transform"]["animation"] == "ken-burns-slow-zoom"
