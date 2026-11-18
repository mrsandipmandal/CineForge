import json
from pathlib import Path
from tools.video.video_compose import VideoCompose
from tools.render.remotion_episode_builder import RemotionEpisodeBuilder

def generate(project_id: str, scenes: list, subtitles: list, audio_path: str):
    project_dir = Path("projects") / project_id
    builder = RemotionEpisodeBuilder(project_dir)
    
    # 1. Build artifacts
    builder.build(scenes, subtitles)
    
    # 2. Assemble artifacts for VideoCompose
    artifacts_dir = project_dir / "artifacts"
    with open(artifacts_dir / "edit_decisions.json") as f:
        edit_decisions = json.load(f)
    with open(artifacts_dir / "asset_manifest.json") as f:
        asset_manifest = json.load(f)
        
    # Optional artifacts - generating minimal ones
    proposal_packet = {"version": "1.0", "production_plan": {"render_runtime": "remotion"}}
    scene_plan = {"version": "1.0", "scenes": []}
    
    # 3. Render
    vc = VideoCompose()
    
    print(f"DEBUG: edit_decisions type: {type(edit_decisions)}")
    print(f"DEBUG: asset_manifest type: {type(asset_manifest)}")

    render_res = vc.execute({
        'operation': 'render',
        'edit_decisions': edit_decisions,
        'asset_manifest': asset_manifest,
        'proposal_packet': proposal_packet,
        'audio_path': audio_path,
        'output_path': str(project_dir / "renders" / "final.mp4"),
        'profile': 'tiktok' # TikTok is vertical
    })
    
    if render_res.success:
        print("Render successful:", render_res.data['output'])
    else:
        print("Render failed:", render_res.error)

if __name__ == "__main__":
    # Test/Example usage
    scenes = [
        {"id": "1", "source": "assets/scene1.jpg", "duration": 3.0, "motion": "ken-burns-slow-zoom"},
        {"id": "2", "source": "assets/scene2.jpg", "duration": 3.0, "motion": "ken-burns-slow-zoom"}
    ]
    subtitles = [
        {"text": "Hello world", "start": 0.0, "end": 3.0},
        {"text": "Welcome to CineForge", "start": 3.0, "end": 6.0}
    ]
    generate("test-render-episode", scenes, subtitles, "assets/audio.mp3")
