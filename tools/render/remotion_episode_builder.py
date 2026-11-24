import json
from pathlib import Path
from typing import Any, List, Dict

class RemotionEpisodeBuilder:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.artifacts_dir = project_dir / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def build(self, scenes: List[Dict[str, Any]], subtitles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build Remotion composition configuration artifacts.
        scenes: list of dicts with 'id', 'source', 'duration', 'motion'
        subtitles: list of dicts with 'text', 'start', 'end'
        """
        
        # 1. Build edit_decisions.json
        cuts = []
        current_time = 0.0
        
        for scene in scenes:
            cut = {
                "id": str(scene['id']),
                "source": str(scene['source']),
                "in_seconds": 0,
                "out_seconds": scene['duration'],
                "transform": {
                    "animation": scene.get('motion', 'ken-burns-slow-zoom')
                }
            }
            cuts.append(cut)
            current_time += scene['duration']
            
        edit_decisions = {
            "version": "1.0",
            "cuts": cuts,
            "render_runtime": "remotion",
            "renderer_family": "explainer-data",
            "composition_mode": "templated",
            "metadata": {
                "compose_target": {"width": 1080, "height": 1920, "fit": "cover"}
            }
        }
        
        # 2. Build asset_manifest.json
        assets = []
        for scene in scenes:
            assets.append({
                "id": str(scene['id']),
                "path": str(scene['source']), 
                "type": "image",
                "duration_seconds": float(scene.get('duration', 0.0)),
                "source_tool": "explainer-builder",
                "scene_id": str(scene['id'])
            })
            
        asset_manifest = {
            "version": "1.0",
            "assets": assets
        }
        
        # 3. Write artifacts
        with open(self.artifacts_dir / "edit_decisions.json", "w", encoding="utf-8") as f:
            json.dump(edit_decisions, f, indent=2)
            
        with open(self.artifacts_dir / "asset_manifest.json", "w", encoding="utf-8") as f:
            json.dump(asset_manifest, f, indent=2)
            
        # 4. Write subtitles.srt
        srt_content = ""
        for i, sub in enumerate(subtitles):
            srt_content += f"{i+1}\n"
            start = self._format_time(sub['start'])
            end = self._format_time(sub['end'])
            srt_content += f"{start} --> {end}\n"
            srt_content += f"{sub['text']}\n\n"
            
        (self.project_dir / "assets" / "subtitles.srt").parent.mkdir(parents=True, exist_ok=True)
        (self.project_dir / "assets" / "subtitles.srt").write_text(srt_content, encoding="utf-8")
        
        return {"edit_decisions": edit_decisions, "asset_manifest": asset_manifest}

    def _format_time(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
