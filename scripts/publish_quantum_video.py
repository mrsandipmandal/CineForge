import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import json
from tools.publishers.export_bundle import ExportBundle
from lib.checkpoint import write_checkpoint
from schemas.artifacts import validate_artifact

project_id = 'rahasyalok-quantum-entanglement'
project_dir = Path('projects') / project_id
artifacts_dir = project_dir / 'artifacts'
renders_dir = project_dir / 'renders'
assets_dir = project_dir / 'assets'

video_path = renders_dir / 'final.mp4'
srt_path = assets_dir / 'subtitles.srt'
thumb_path = Path('C:/Users/mr_sa/.gemini/antigravity/brain/2587e69a-7d04-4052-8bde-361e82536ae7/final_preview_frame_25s.jpg')

bundle_tool = ExportBundle()
result = bundle_tool.execute({
    'video_path': str(video_path),
    'project_name': project_id,
    'title': 'क्वांटम उलझन: ब्रह्मांड का सबसे बड़ा रहस्य! | Quantum Entanglement in Hindi',
    'platform': 'youtube',
    'visibility': 'public',
    'subtitles_path': str(srt_path),
    'thumbnail_path': str(thumb_path) if thumb_path.exists() else None,
    'thumbnail_concept': {
        'concept': 'Deep contrast split featuring glowing entangled quantum particles and Albert Einstein deep in thought with bold Devanagari text.',
        'text_overlay': 'क्वांटम उलझन: सच या भ्रम?',
        'style_notes': 'Ultra-high contrast, cinematic dark aesthetic, gold typography.'
    },
    'description': """क्या दो कण अरबों प्रकाश-वर्ष दूर रहकर भी पलक झपकाते ही एक दूसरे से बात कर सकते हैं? 
यह है विज्ञान की सबसे बड़ी अनसुलझी पहेली — क्वांटम एंटैंगलमेंट (Quantum Entanglement)!
यहाँ तक कि खुद अल्बर्ट आइंस्टीन भी इसे मानने से डरते थे और उन्होंने इसे "Spooky Action at a Distance" कहा था।

अगर एक कण का स्पिन बदलता है, तो दूसरा तुरंत प्रतिक्रिया देता है — प्रकाश की गति से भी तेज़! क्या हमारा पूरा ब्रह्मांड आपस में जुड़ा हुआ है? 

कमेंट में अपनी राय ज़रूर बताइए और ऐसे ही रहस्यों के लिए सब्सक्राइब करें RahasyaLok को!

00:00 - Introduction & The Impossible Connection
00:08 - Quantum Entanglement Explained
00:18 - Einstein's Spooky Action at a Distance
00:28 - Quantum Computing Revolution
00:44 - The Mystery of Reality
00:51 - Comment Your Thoughts & Subscribe

#QuantumEntanglement #ScienceMysteries #RahasyaLok #PhysicsInHindi #YouTubeShorts""",
    'tags': [
        'क्वांटम उलझन',
        'quantum entanglement in hindi',
        'science mysteries in hindi',
        'rahasyalok',
        'einstein spooky action',
        'quantum physics hindi',
        'space science hindi',
        'youtube shorts hindi'
    ],
    'hashtags': [
        '#QuantumEntanglement',
        '#ScienceMysteries',
        '#RahasyaLok',
        '#PhysicsInHindi',
        '#YouTubeShorts'
    ],
    'chapters': [
        {'start_seconds': 0, 'title': 'The Impossible Connection'},
        {'start_seconds': 8, 'title': 'Quantum Entanglement Explained'},
        {'start_seconds': 18, 'title': "Einstein's Spooky Action"},
        {'start_seconds': 28, 'title': 'Quantum Computing Revolution'},
        {'start_seconds': 44, 'title': 'The Mystery of Reality'},
        {'start_seconds': 51, 'title': 'Question & Outro'}
    ]
})

print('ExportBundle result success:', result.success)
if not result.success:
    print('Error:', result.error)
    sys.exit(1)

publish_log = result.data['publish_log']
with open(artifacts_dir / 'publish_log.json', 'w', encoding='utf-8') as f:
    json.dump(publish_log, f, indent=2, ensure_ascii=False)

# Validate artifact against schema
validate_artifact('publish_log', publish_log)
print('Schema validation passed!')

# Checkpoint publish stage
write_checkpoint(
    Path('projects'),
    project_id,
    'publish',
    'completed',
    {'publish_log': publish_log},
    pipeline_type='animated-explainer',
    style_playbook='clean-professional',
    human_approval_required=False,
    human_approved=True
)
print('Publish stage successfully checkpointed!')
