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

t0 = 0.0
t1 = round(t0 + dur_01, 2)
t2 = round(t1 + dur_02, 2)
t3 = round(t2 + dur_03, 2)
t4 = round(t3 + dur_04, 2)
t5 = round(t4 + dur_05, 2)
t6 = round(t5 + dur_06, 2)
t7 = round(t6 + dur_07, 2)

total_dur = t7
print(f"Timeline: 0 -> {t1} -> {t2} -> {t3} -> {t4} -> {t5} -> {t6} -> {t7}s (total: {total_dur}s)")

edit_decisions = {
    'version': '1.0',
    'renderer_family': 'explainer-data',
    'render_runtime': 'remotion',
    'composition_mode': 'templated',
    'cuts': [
        {
            'id': 'cut-01',
            'source': 'assets/images/scene_01.png',
            'in_seconds': t0,
            'out_seconds': t1,
            'layer': 'primary',
            'speed': 1.0,
            'transform': {
                'scale': 1.08,
                'position': 'center',
                'animation': 'ken-burns-slow-zoom'
            },
            'transition_in': 'fade',
            'transition_out': 'dissolve',
            'transition_duration': 0.4,
            'reason': 'Cosmic quantum entanglement establishing hook'
        },
        {
            'id': 'cut-02',
            'source': 'assets/images/scene_02.png',
            'in_seconds': t1,
            'out_seconds': t2,
            'layer': 'primary',
            'speed': 1.0,
            'transform': {
                'scale': 1.06,
                'position': 'center',
                'animation': 'pan-left'
            },
            'transition_in': 'dissolve',
            'transition_out': 'dissolve',
            'transition_duration': 0.4,
            'reason': 'Subatomic entangled particle explanation'
        },
        {
            'id': 'cut-03',
            'source': 'assets/images/scene_03.png',
            'in_seconds': t2,
            'out_seconds': t3,
            'layer': 'primary',
            'speed': 1.0,
            'transform': {
                'scale': 1.05,
                'position': 'center',
                'animation': 'dolly-in'
            },
            'transition_in': 'dissolve',
            'transition_out': 'dissolve',
            'transition_duration': 0.4,
            'reason': 'Albert Einstein dramatic skepticism reveal'
        },
        {
            'id': 'cut-04',
            'source': 'assets/images/scene_04.png',
            'in_seconds': t3,
            'out_seconds': t4,
            'layer': 'primary',
            'speed': 1.0,
            'transform': {
                'scale': 1.07,
                'position': 'center',
                'animation': 'tilt-up'
            },
            'transition_in': 'dissolve',
            'transition_out': 'dissolve',
            'transition_duration': 0.4,
            'reason': '2022 Nobel Prize triumph validation'
        },
        {
            'id': 'cut-05',
            'source': 'assets/images/scene_05.png',
            'in_seconds': t4,
            'out_seconds': t5,
            'layer': 'primary',
            'speed': 1.0,
            'transform': {
                'scale': 1.06,
                'position': 'center',
                'animation': 'pan-right'
            },
            'transition_in': 'dissolve',
            'transition_out': 'dissolve',
            'transition_duration': 0.4,
            'reason': 'Quantum supercomputers and unbreakable cryptography'
        },
        {
            'id': 'cut-06',
            'source': 'assets/images/scene_06.png',
            'in_seconds': t5,
            'out_seconds': t6,
            'layer': 'primary',
            'speed': 1.0,
            'transform': {
                'scale': 1.08,
                'position': 'center',
                'animation': 'zoom-in'
            },
            'transition_in': 'dissolve',
            'transition_out': 'dissolve',
            'transition_duration': 0.4,
            'reason': 'Cosmic mirror reality philosophical climax'
        },
        {
            'id': 'cut-07',
            'source': 'assets/images/scene_07.png',
            'in_seconds': t6,
            'out_seconds': t7,
            'layer': 'primary',
            'speed': 1.0,
            'transform': {
                'scale': 1.05,
                'position': 'center',
                'animation': 'slow-fade-out'
            },
            'transition_in': 'dissolve',
            'transition_out': 'fade',
            'transition_duration': 0.5,
            'reason': 'RahasyaLok branding outro call to action'
        }
    ],
    'audio': {
        'narration': {
            'segments': [
                {'asset_id': 'nar-01', 'start_seconds': t0, 'end_seconds': t1},
                {'asset_id': 'nar-02', 'start_seconds': t1, 'end_seconds': t2},
                {'asset_id': 'nar-03', 'start_seconds': t2, 'end_seconds': t3},
                {'asset_id': 'nar-04', 'start_seconds': t3, 'end_seconds': t4},
                {'asset_id': 'nar-05', 'start_seconds': t4, 'end_seconds': t5},
                {'asset_id': 'nar-06', 'start_seconds': t5, 'end_seconds': t6},
                {'asset_id': 'nar-07', 'start_seconds': t6, 'end_seconds': t7}
            ]
        },
        'music': {
            'asset_id': 'bgm-01',
            'volume': 0.14,
            'fade_in_seconds': 1.0,
            'fade_out_seconds': 2.0,
            'ducking': True
        }
    },
    'subtitles': {
        'enabled': True,
        'style': 'sentence',
        'source': 'assets/subtitles.srt',
        'font': 'Arial',
        'font_size': 48,
        'color': '#FFFFFF',
        'position': 'bottom-center'
    },
    'overlays': []
}

validate_artifact('edit_decisions', edit_decisions)
with open(artifacts_dir / 'edit_decisions.json', 'w', encoding='utf-8') as f:
    json.dump(edit_decisions, f, ensure_ascii=False, indent=2)

write_checkpoint(
    Path('projects'),
    project_id,
    'edit',
    'completed',
    {'edit_decisions': edit_decisions},
    pipeline_type='animated-explainer',
    style_playbook='clean-professional',
    human_approval_required=False,
    human_approved=False
)
print('Edit Decisions validated and checkpointed successfully!')
