import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import json
import subprocess
from lib.checkpoint import write_checkpoint
from schemas.artifacts import validate_artifact

project_id = 'rahasyalok-quantum-entanglement'
artifacts_dir = Path('projects') / project_id / 'artifacts'
assets_dir = Path('projects') / project_id / 'assets'

def get_duration(p):
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True, check=True
    )
    return round(float(res.stdout.strip()), 2)

dur_01 = get_duration(assets_dir / 'audio' / 'sec_01.mp3')
dur_02 = get_duration(assets_dir / 'audio' / 'sec_02.mp3')
dur_03 = get_duration(assets_dir / 'audio' / 'sec_03.mp3')
dur_04 = get_duration(assets_dir / 'audio' / 'sec_04.mp3')
dur_05 = get_duration(assets_dir / 'audio' / 'sec_05.mp3')
dur_06 = get_duration(assets_dir / 'audio' / 'sec_06.mp3')
dur_07 = get_duration(assets_dir / 'audio' / 'sec_07.mp3')
dur_mix = get_duration(assets_dir / 'audio' / 'final_mix.mp3')
dur_bgm = get_duration(assets_dir / 'music' / 'bgm.mp3')

asset_manifest = {
    'version': '1.0',
    'total_cost_usd': 0.0,
    'assets': [
        {
            'id': 'img-01',
            'type': 'image',
            'path': 'assets/images/scene_01.png',
            'source_tool': 'image_selector',
            'scene_id': 'scene-01',
            'prompt': 'A cinematic 9:16 vertical image of deep outer space with two glowing quantum particles connected by an energetic beam.',
            'resolution': '1080x1920',
            'format': 'png',
            'cost_usd': 0.0,
            'provider': 'image-generator'
        },
        {
            'id': 'img-02',
            'type': 'image',
            'path': 'assets/images/scene_02.png',
            'source_tool': 'image_selector',
            'scene_id': 'scene-02',
            'prompt': 'Cinematic 9:16 vertical macro shot of two subatomic spinning photon particles entangled together with interference patterns.',
            'resolution': '1080x1920',
            'format': 'png',
            'cost_usd': 0.0,
            'provider': 'image-generator'
        },
        {
            'id': 'img-03',
            'type': 'image',
            'path': 'assets/images/scene_03.png',
            'source_tool': 'image_selector',
            'scene_id': 'scene-03',
            'prompt': 'Dramatic cinematic 9:16 portrait of Albert Einstein in deep contemplation with chalkboard relativity equations.',
            'resolution': '1080x1920',
            'format': 'png',
            'cost_usd': 0.0,
            'provider': 'image-generator'
        },
        {
            'id': 'img-04',
            'type': 'image',
            'path': 'assets/images/scene_04.png',
            'source_tool': 'image_selector',
            'scene_id': 'scene-04',
            'prompt': 'JWST Giant Golden hexagonal optics mirror and laser physics laboratory.',
            'resolution': '1080x1920',
            'format': 'png',
            'cost_usd': 0.0,
            'provider': 'nasa'
        },
        {
            'id': 'img-05',
            'type': 'image',
            'path': 'assets/images/scene_05.png',
            'source_tool': 'image_selector',
            'scene_id': 'scene-05',
            'prompt': 'NASA Advanced Supercomputing quantum computing facility.',
            'resolution': '1080x1920',
            'format': 'png',
            'cost_usd': 0.0,
            'provider': 'nasa'
        },
        {
            'id': 'img-06',
            'type': 'image',
            'path': 'assets/images/scene_06.png',
            'source_tool': 'image_selector',
            'scene_id': 'scene-06',
            'prompt': 'Hubble colliding galaxy deep field space horizon.',
            'resolution': '1080x1920',
            'format': 'png',
            'cost_usd': 0.0,
            'provider': 'nasa'
        },
        {
            'id': 'img-07',
            'type': 'image',
            'path': 'assets/images/scene_07.png',
            'source_tool': 'image_selector',
            'scene_id': 'scene-07',
            'prompt': 'Cosmic celestial space nebula vortex.',
            'resolution': '1080x1920',
            'format': 'png',
            'cost_usd': 0.0,
            'provider': 'nasa'
        },
        {
            'id': 'nar-01',
            'type': 'narration',
            'path': 'assets/audio/sec_01.mp3',
            'source_tool': 'tts_selector',
            'scene_id': 'scene-01',
            'duration_seconds': dur_01,
            'cost_usd': 0.0,
            'provider': 'edge_tts',
            'voice_performance': {
                'source_section_id': 'sec_01',
                'delivery_cues_applied': True,
                'provider_text_used': True,
                'sample_approved': True
            }
        },
        {
            'id': 'nar-02',
            'type': 'narration',
            'path': 'assets/audio/sec_02.mp3',
            'source_tool': 'tts_selector',
            'scene_id': 'scene-02',
            'duration_seconds': dur_02,
            'cost_usd': 0.0,
            'provider': 'edge_tts',
            'voice_performance': {
                'source_section_id': 'sec_02',
                'delivery_cues_applied': True,
                'provider_text_used': True,
                'sample_approved': True
            }
        },
        {
            'id': 'nar-03',
            'type': 'narration',
            'path': 'assets/audio/sec_03.mp3',
            'source_tool': 'tts_selector',
            'scene_id': 'scene-03',
            'duration_seconds': dur_03,
            'cost_usd': 0.0,
            'provider': 'edge_tts',
            'voice_performance': {
                'source_section_id': 'sec_03',
                'delivery_cues_applied': True,
                'provider_text_used': True,
                'sample_approved': True
            }
        },
        {
            'id': 'nar-04',
            'type': 'narration',
            'path': 'assets/audio/sec_04.mp3',
            'source_tool': 'tts_selector',
            'scene_id': 'scene-04',
            'duration_seconds': dur_04,
            'cost_usd': 0.0,
            'provider': 'edge_tts',
            'voice_performance': {
                'source_section_id': 'sec_04',
                'delivery_cues_applied': True,
                'provider_text_used': True,
                'sample_approved': True
            }
        },
        {
            'id': 'nar-05',
            'type': 'narration',
            'path': 'assets/audio/sec_05.mp3',
            'source_tool': 'tts_selector',
            'scene_id': 'scene-05',
            'duration_seconds': dur_05,
            'cost_usd': 0.0,
            'provider': 'edge_tts',
            'voice_performance': {
                'source_section_id': 'sec_05',
                'delivery_cues_applied': True,
                'provider_text_used': True,
                'sample_approved': True
            }
        },
        {
            'id': 'nar-06',
            'type': 'narration',
            'path': 'assets/audio/sec_06.mp3',
            'source_tool': 'tts_selector',
            'scene_id': 'scene-06',
            'duration_seconds': dur_06,
            'cost_usd': 0.0,
            'provider': 'edge_tts',
            'voice_performance': {
                'source_section_id': 'sec_06',
                'delivery_cues_applied': True,
                'provider_text_used': True,
                'sample_approved': True
            }
        },
        {
            'id': 'nar-07',
            'type': 'narration',
            'path': 'assets/audio/sec_07.mp3',
            'source_tool': 'tts_selector',
            'scene_id': 'scene-07',
            'duration_seconds': dur_07,
            'cost_usd': 0.0,
            'provider': 'edge_tts',
            'voice_performance': {
                'source_section_id': 'sec_07',
                'delivery_cues_applied': True,
                'provider_text_used': True,
                'sample_approved': True
            }
        },
        {
            'id': 'bgm-01',
            'type': 'music',
            'path': 'assets/music/bgm.mp3',
            'source_tool': 'music_gen',
            'scene_id': 'scene-01',
            'duration_seconds': dur_bgm,
            'cost_usd': 0.0,
            'provider': 'ffmpeg'
        },
        {
            'id': 'mix-01',
            'type': 'audio',
            'path': 'assets/audio/final_mix.mp3',
            'source_tool': 'audio_mixer',
            'scene_id': 'scene-01',
            'duration_seconds': dur_mix,
            'cost_usd': 0.0,
            'provider': 'ffmpeg'
        },
        {
            'id': 'sub-01',
            'type': 'subtitle',
            'path': 'assets/subtitles.srt',
            'source_tool': 'subtitle_gen',
            'scene_id': 'scene-01',
            'cost_usd': 0.0,
            'provider': 'cineforge'
        }
    ]
}

validate_artifact('asset_manifest', asset_manifest)
with open(artifacts_dir / 'asset_manifest.json', 'w', encoding='utf-8') as f:
    json.dump(asset_manifest, f, ensure_ascii=False, indent=2)

write_checkpoint(
    Path('projects'),
    project_id,
    'assets',
    'completed',
    {'asset_manifest': asset_manifest},
    pipeline_type='animated-explainer',
    style_playbook='clean-professional',
    human_approval_required=True,
    human_approved=True
)
print('Asset Manifest validated and checkpointed successfully!')
