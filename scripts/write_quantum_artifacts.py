import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import json
from lib.checkpoint import write_checkpoint
from schemas.artifacts import validate_artifact

project_id = 'rahasyalok-quantum-entanglement'
artifacts_dir = Path('projects') / project_id / 'artifacts'
artifacts_dir.mkdir(parents=True, exist_ok=True)

# 1. Proposal Packet
proposal_packet = {
    'version': '1.0',
    'concept_options': [
        {
            'id': 'c1',
            'title': 'क्वांटम उलझन — दो कण, एक रहस्य!',
            'hook': 'कल्पना कीजिए... दो कण। एक यहाँ, एक अरबों प्रकाश-वर्ष दूर। और फिर भी एक पल में जुड़े!',
            'narrative_structure': 'myth_busting',
            'visual_approach': 'Dark cosmic visuals, glowing quantum particle pairs, Einstein historic reveal, and quantum computing aesthetic.',
            'suggested_playbook': 'clean-professional',
            'target_audience': 'Indian YouTube Shorts viewers interested in science, mysteries, and mind-bending physics.',
            'target_platform': 'youtube',
            'target_duration_seconds': 52,
            'key_points': [
                'Quantum entanglement binds particles instantaneously across any distance.',
                'Einstein called it Spooky action at a distance and doubted it.',
                'The 2022 Nobel Prize proved it is real, powering future quantum computers.'
            ],
            'core_message': 'Quantum physics defies common sense, but it is the proven reality powering our technological future.',
            'cta': 'आपको क्या लगता है — क्या Quantum Entanglement से Time Travel possible होगा? Comment में बताइए!',
            'tone': 'Awe-inspiring, mysterious, authoritative, engaging',
            'grounded_in': ['2022 Physics Nobel Prize', 'Einstein Spooky Action'],
            'why_this_works': 'Combines curiosity hook, historical icon doubt (Einstein), and tangible future tech in 52 seconds.'
        },
        {
            'id': 'c2',
            'title': 'ब्लैक होल का रहस्य — क्या होता है अंदर?',
            'hook': 'अगर आप ब्लैक होल में गिर जाएं... तो क्या होगा आपके साथ?',
            'narrative_structure': 'journey',
            'visual_approach': 'Accretion disk, event horizon gravitational lensing, deep void.',
            'suggested_playbook': 'clean-professional',
            'target_audience': 'General space science enthusiasts.',
            'target_platform': 'youtube',
            'target_duration_seconds': 55,
            'key_points': [
                'Event horizon marks the point of no return for light itself.',
                'Spaghettification stretches matter infinitely before the singularity.',
                'Time slows down drastically relative to outside observers.'
            ],
            'core_message': 'Black holes challenge the laws of general relativity and quantum mechanics.',
            'cta': 'क्या ब्लैक होल दूसरे ब्रह्मांड का दरवाज़ा है? कमेंट में बताइए!',
            'tone': 'Dramatic, terrifying, cosmic awe',
            'grounded_in': ['Event Horizon Telescope', 'General Relativity'],
            'why_this_works': 'Classic viral science topic with strong visual impact.'
        },
        {
            'id': 'c3',
            'title': 'समय यात्रा — विज्ञान या कल्पना?',
            'hook': 'वैज्ञानिकों के अनुसार भविष्य में जाना possible है — लेकिन एक शर्त पर!',
            'narrative_structure': 'debate',
            'visual_approach': 'Warped spacetime grid, high speed spacecraft, clocks ticking at different rates.',
            'suggested_playbook': 'clean-professional',
            'target_audience': 'Futurism and physics questioners.',
            'target_platform': 'youtube',
            'target_duration_seconds': 50,
            'key_points': [
                'Time dilation is proven: GPS satellites run faster than earth clocks.',
                'Traveling near the speed of light allows forward time travel.',
                'Backward time travel creates paradoxes that may violate causality.'
            ],
            'core_message': 'Forward time travel is scientifically real through relativity.',
            'cta': 'अगर आपको मौका मिले, तो आप भूतकाल में जाएंगे या भविष्य में?',
            'tone': 'Thought-provoking, fast-paced',
            'grounded_in': ['Special Relativity', 'GPS relativistic corrections'],
            'why_this_works': 'Engaging dilemma that drives high comment section activity.'
        }
    ],
    'selected_concept': {
        'concept_id': 'c1',
        'rationale': 'User explicitly chose Quantum Entanglement concept for the RahasyaLok science edition.'
    },
    'production_plan': {
        'pipeline': 'animated-explainer',
        'playbook': 'clean-professional',
        'stages': [
            {
                'stage': 'script',
                'tools': [],
                'approach': 'Write 7-section Hindi script covering hook, setup, Einstein doubt, 2022 Nobel proof, quantum computers, climax and CTA.',
                'fallback_if_unavailable': 'Standard script format.'
            },
            {
                'stage': 'scene_plan',
                'tools': [],
                'approach': 'Plan 7 distinct 9:16 vertical scenes matching the 0-52s timeline with single caption specification (no double caption).',
                'fallback_if_unavailable': 'Standard cut mapping.'
            },
            {
                'stage': 'assets',
                'tools': [
                    {
                        'tool_name': 'tts_selector',
                        'role': 'Generate deep authoritative Hindi male narration',
                        'provider': 'edge_tts',
                        'available': True,
                        'estimated_cost_usd': 0.0,
                        'why_this_provider': 'Broadcast-quality Hindi voice with Sandip profile tuning, high fidelity and zero billing friction.'
                    },
                    {
                        'tool_name': 'image_selector',
                        'role': 'Generate 7 ultra-cinematic 9:16 visuals',
                        'provider': 'fal.ai',
                        'available': True,
                        'estimated_cost_usd': 0.0,
                        'why_this_provider': 'High aesthetic space, particle, and tech rendering.'
                    },
                    {
                        'tool_name': 'music_gen',
                        'role': 'Cinematic suspense ambient BGM',
                        'provider': 'ffmpeg',
                        'available': True,
                        'estimated_cost_usd': 0.0,
                        'why_this_provider': 'Custom multi-frequency tension drone with binaural dark atmosphere.'
                    }
                ],
                'approach': 'Synthesize voiceover, generate 7 vertical images, mix audio.',
                'fallback_if_unavailable': 'Edge TTS and FFmpeg fallback.'
            },
            {
                'stage': 'edit',
                'tools': [],
                'approach': 'Compute precise cut timings, audio ducking, single caption burn configuration.',
                'fallback_if_unavailable': 'Standard cut alignment.'
            },
            {
                'stage': 'compose',
                'tools': [
                    {
                        'tool_name': 'video_compose',
                        'role': 'Remotion vertical composition render',
                        'provider': 'remotion',
                        'available': True,
                        'estimated_cost_usd': 0.0,
                        'why_this_provider': '1080x1920 MP4 export with smooth transitions.'
                    }
                ],
                'approach': 'Render full 1080x1920 vertical video via Remotion and burn single subtitle track with FFmpeg.',
                'fallback_if_unavailable': 'FFmpeg Ken Burns composition fallback.'
            }
        ],
        'quality_tradeoffs': [
            {
                'tradeoff': 'Atelier Remotion with single-track subtitle burn vs dual overlay',
                'recommendation': 'Use single-track FFmpeg subtitle burn to eliminate the duplicate captions observed in previous render.',
                'quality_impact': 'Clean, professional single-track subtitles perfectly legible on mobile.'
            }
        ],
        'alternative_paths': [
            {
                'description': 'Standard Production Path (Remotion + EdgeTTS + FFmpeg BGM)',
                'total_cost_usd': 0.0,
                'quality_level': 'standard',
                'what_changes': 'Zero billing barriers, instant execution.'
            }
        ],
        'delivery_promise': {
            'promise_type': 'motion_led',
            'motion_required': False,
            'tone_mode': 'cinematic',
            'quality_floor': 'broadcast',
            'approved_fallback': None
        },
        'renderer_family': 'explainer-data',
        'render_runtime': 'remotion',
        'composition_mode': 'atelier',
        'art_direction': 'Dark cosmic navy (#070B19), quantum glowing cyan (#00F0FF), gold accent (#FFD700), and deep space violet.',
        'taste_profile': {
            'design_read': 'High-end science documentary aesthetic for YouTube Shorts. Awe-inspiring, futuristic, rigorous yet accessible.',
            'visual_variance': 6,
            'motion_intensity': 4,
            'information_density': 5,
            'palette_discipline': 'Cosmic dark navy, glowing cyan, electric purple, antique gold, stark white',
            'layout_variation': 'Dynamic camera framing (cosmic WS, micro quantum MS, historical sepia reveal, futuristic tech CU)',
            'reference_strategy': 'Respectful scientific representation',
            'anti_patterns': [
                'No cartoonish graphics',
                'No double captions or overlapping text',
                'No cluttered HUD overlays'
            ],
            'quality_gates': [
                '1080x1920 9:16 vertical formatting',
                'Single subtitle track with zero duplication',
                'Narration 12-14dB above background ambience'
            ]
        },
        'music_source': {
            'source_type': 'ai_generated',
            'provider': 'ffmpeg',
            'mood_direction': 'Deep cosmic drone with subtle sub-bass pulses and eerie scientific mystery undertones.',
            'estimated_cost_usd': 0.0
        },
        'voice_selection': {
            'provider': 'edge_tts',
            'voice_id': 'hi-IN-MadhurNeural',
            'rationale': 'Matches Sandip broadcast Hindi profile, mature, authoritative, crystal clear pronunciation.',
            'estimated_cost_usd': 0.0,
            'delivery_style': 'Deep, authoritative science documentary narration with contemplative pauses.',
            'pacing_policy': '125-135 words per minute with 0.4-0.6s pauses between narrative beats.',
            'sample_approval_required': False
        }
    },
    'cost_estimate': {
        'total_estimated_usd': 0.0,
        'line_items': [
            {'tool': 'tts_selector', 'operation': 'Hindi Voiceover (138 words)', 'quantity': 1, 'estimated_usd': 0.0, 'notes': 'EdgeTTS Madhur Neural'},
            {'tool': 'image_selector', 'operation': 'Cinematic 9:16 Visuals (7 scenes)', 'quantity': 7, 'estimated_usd': 0.0, 'notes': 'Visual generator'},
            {'tool': 'music_gen', 'operation': 'Cosmic Ambient BGM (60s)', 'quantity': 1, 'estimated_usd': 0.0, 'notes': 'FFmpeg synthesized drone'},
            {'tool': 'video_compose', 'operation': 'Remotion Composition & Single Subtitle Burn', 'quantity': 1, 'estimated_usd': 0.0, 'notes': 'Local Remotion execution'}
        ],
        'budget_verdict': 'within_budget',
        'savings_options': []
    },
    'approval': {
        'status': 'approved',
        'user_notes': 'Approved by user via chat',
        'approved_budget_usd': 0.0
    }
}

validate_artifact('proposal_packet', proposal_packet)
with open(artifacts_dir / 'proposal_packet.json', 'w', encoding='utf-8') as f:
    json.dump(proposal_packet, f, ensure_ascii=False, indent=2)

write_checkpoint(
    Path('projects'),
    project_id,
    'proposal',
    'completed',
    {'proposal_packet': proposal_packet},
    pipeline_type='animated-explainer',
    style_playbook='clean-professional',
    human_approval_required=True,
    human_approved=True
)
print('Proposal checkpoint validated and written!')

# 2. Script
script = {
    'version': '1.0',
    'title': 'क्वांटम उलझन — दो कण, एक रहस्य!',
    'total_duration_seconds': 52.0,
    'voice_performance': {
        'performance_intent': 'Deep, authoritative, and awe-inspiring Hindi science documentary narration.',
        'pacing_profile': 'cinematic',
        'energy_curve': 'Mysterious opening, dramatic Einstein reveal, energetic Nobel validation, contemplative finish.',
        'pause_policy': '0.3 to 0.6s pauses at dramatic turns.',
        'sample_section_id': 'sec_01',
        'provider_notes': {
            'edge_tts': 'hi-IN-MadhurNeural tuned to Sandip broadcast cadence.'
        }
    },
    'sections': [
        {
            'id': 'sec_01',
            'label': 'Hook - Cosmic Connection',
            'text': 'कल्पना कीजिए... दो कण। एक यहाँ, एक अरबों प्रकाश-वर्ष दूर। और फिर भी... एक पल में एक-दूसरे से जुड़े।',
            'start_seconds': 0.0,
            'end_seconds': 5.0,
            'speaker_directions': 'Slow, mysterious opening with deliberate pauses.',
            'delivery_cues': {
                'pace': 'slow',
                'energy': 'suspenseful',
                'emphasis_words': ['एक पल में', 'प्रकाश-वर्ष'],
                'pause_after_seconds': 0.5,
                'provider_text': 'कल्पना कीजिए... दो कण। एक यहाँ, एक अरबों प्रकाश-वर्ष दूर। और फिर भी... एक पल में एक-दूसरे से जुड़े।'
            },
            'enhancement_cues': [
                {
                    'type': 'overlay',
                    'description': 'Glowing title reveal: क्वांटम उलझन',
                    'timestamp_seconds': 1.0
                }
            ],
            'source_ref': 'Quantum entanglement principle'
        },
        {
            'id': 'sec_02',
            'label': 'Setup - The Mystery',
            'text': 'यह विज्ञान की सबसे बड़ी पहेली है — क्वांटम एंटैंगलमेंट। जब दो कण आपस में उलझ जाते हैं, तो वे हमेशा के लिए एक हो जाते हैं। दोनों के बीच चाहे जितनी भी दूरी हो।',
            'start_seconds': 5.0,
            'end_seconds': 13.0,
            'speaker_directions': 'Measured, authoritative cadence.',
            'delivery_cues': {
                'pace': 'measured',
                'energy': 'curious',
                'emphasis_words': ['क्वांटम एंटैंगलमेंट', 'हमेशा के लिए एक'],
                'pause_after_seconds': 0.4,
                'provider_text': 'यह विज्ञान की सबसे बड़ी पहेली है — क्वांटम एंटैंगलमेंट। जब दो कण आपस में उलझ जाते हैं, तो वे हमेशा के लिए एक हो जाते हैं। दोनों के बीच चाहे जितनी भी दूरी हो।'
            },
            'enhancement_cues': [
                {
                    'type': 'overlay',
                    'description': 'Text reveal: QUANTUM ENTANGLEMENT',
                    'timestamp_seconds': 6.0
                }
            ],
            'source_ref': 'Quantum mechanics foundations'
        },
        {
            'id': 'sec_03',
            'label': 'Build 1 - Einstein Spooky Action',
            'text': 'यहाँ तक कि खुद आइंस्टीन इस बात को मानने से डरते थे। उन्होंने इसे कहा — Spooky Action at a Distance! मतलब — दूर से होने वाली डरावनी हरकत। उन्हें लगा, यह impossible है।',
            'start_seconds': 13.0,
            'end_seconds': 24.0,
            'speaker_directions': 'Dramatic tension rise, distinct emphasis on Einstein and Spooky Action.',
            'delivery_cues': {
                'pace': 'measured',
                'energy': 'dramatic',
                'emphasis_words': ['आइंस्टीन', 'Spooky Action', 'impossible'],
                'pause_after_seconds': 0.5,
                'provider_text': 'यहाँ तक कि खुद आइंस्टीन इस बात को मानने से डरते थे। उन्होंने इसे कहा — Spooky Action at a Distance! मतलब — दूर से होने वाली डरावनी हरकत। उन्हें लगा, यह impossible है।'
            },
            'enhancement_cues': [
                {
                    'type': 'overlay',
                    'description': 'Text reveal: आइंस्टीन भी हैरान थे!',
                    'timestamp_seconds': 15.0
                }
            ],
            'source_ref': 'Einstein EPR Paradox 1935'
        },
        {
            'id': 'sec_04',
            'label': 'Build 2 - The Nobel Proof',
            'text': 'लेकिन 2022 में तीन वैज्ञानिकों ने यह साबित कर दिया — यह सच है! और उन्हें मिला Physics का Nobel Prize। आइंस्टीन गलत थे।',
            'start_seconds': 24.0,
            'end_seconds': 34.0,
            'speaker_directions': 'Energetic, revelatory delivery.',
            'delivery_cues': {
                'pace': 'brisk',
                'energy': 'triumphant',
                'emphasis_words': ['साबित', 'Nobel Prize', 'गलत थे'],
                'pause_after_seconds': 0.4,
                'provider_text': 'लेकिन 2022 में तीन वैज्ञानिकों ने यह साबित कर दिया — यह सच है! और उन्हें मिला Physics का Nobel Prize। आइंस्टीन गलत थे।'
            },
            'enhancement_cues': [
                {
                    'type': 'overlay',
                    'description': 'Badge: 2022 Physics Nobel Prize',
                    'timestamp_seconds': 26.0
                }
            ],
            'source_ref': 'Nobel Prize in Physics 2022'
        },
        {
            'id': 'sec_05',
            'label': 'Build 3 - Future Tech',
            'text': 'और आज? इसी तकनीक से बन रहे हैं Quantum Computers — जो साधारण कंप्यूटर से लाखों गुना तेज़ होंगे। और Quantum Cryptography — जिसे कोई भी hack नहीं कर सकता।',
            'start_seconds': 34.0,
            'end_seconds': 43.0,
            'speaker_directions': 'Inspiring, futuristic, building pace.',
            'delivery_cues': {
                'pace': 'brisk',
                'energy': 'confident',
                'emphasis_words': ['Quantum Computers', 'लाखों गुना तेज़', 'hack नहीं कर सकता'],
                'pause_after_seconds': 0.4,
                'provider_text': 'और आज? इसी तकनीक से बन रहे हैं Quantum Computers — जो साधारण कंप्यूटर से लाखों गुना तेज़ होंगे। और Quantum Cryptography — जिसे कोई भी hack नहीं कर सकता।'
            },
            'enhancement_cues': [
                {
                    'type': 'overlay',
                    'description': 'Text: भविष्य की तकनीक',
                    'timestamp_seconds': 36.0
                }
            ],
            'source_ref': 'Quantum Information Applications'
        },
        {
            'id': 'sec_06',
            'label': 'Climax - Physics or Magic',
            'text': 'तो सोचिए — दो कण, अरबों किलोमीटर दूर, एक पल में एक-दूसरे को महसूस करते हैं। यह Physics है... या जादू?',
            'start_seconds': 43.0,
            'end_seconds': 49.0,
            'speaker_directions': 'Contemplative, wonder-struck tone with long pause before "या जादू?".',
            'delivery_cues': {
                'pace': 'slow',
                'energy': 'awe',
                'emphasis_words': ['एक पल में', 'जादू'],
                'pause_after_seconds': 0.5,
                'provider_text': 'तो सोचिए — दो कण, अरबों किलोमीटर दूर, एक पल में एक-दूसरे को महसूस करते हैं। यह Physics है... या जादू?'
            },
            'enhancement_cues': [
                {
                    'type': 'overlay',
                    'description': 'Text: Physics या जादू?',
                    'timestamp_seconds': 45.0
                }
            ],
            'source_ref': 'Quantum philosophical dilemma'
        },
        {
            'id': 'sec_07',
            'label': 'Landing - Question CTA',
            'text': 'आपको क्या लगता है — क्या Quantum Entanglement से कभी Time Travel possible होगा? Comment में बताइए!',
            'start_seconds': 49.0,
            'end_seconds': 52.0,
            'speaker_directions': 'Warm, engaging call to action.',
            'delivery_cues': {
                'pace': 'conversational',
                'energy': 'engaging',
                'emphasis_words': ['Time Travel', 'Comment में'],
                'pause_after_seconds': 0.3,
                'provider_text': 'आपको क्या लगता है — क्या Quantum Entanglement से कभी Time Travel possible होगा? Comment में बताइए!'
            },
            'enhancement_cues': [
                {
                    'type': 'overlay',
                    'description': 'Channel logo branding: RAHASYALOK',
                    'timestamp_seconds': 50.0
                }
            ],
            'source_ref': 'Viewer engagement CTA'
        }
    ]
}

validate_artifact('script', script)
with open(artifacts_dir / 'script.json', 'w', encoding='utf-8') as f:
    json.dump(script, f, ensure_ascii=False, indent=2)

write_checkpoint(
    Path('projects'),
    project_id,
    'script',
    'completed',
    {'script': script},
    pipeline_type='animated-explainer',
    style_playbook='clean-professional',
    human_approval_required=True,
    human_approved=True
)
print('Script checkpoint validated and written!')

# 3. Scene Plan
scene_plan = {
    'version': '1.0',
    'style_playbook': 'clean-professional',
    'scenes': [
        {
            'id': 'scene-01',
            'type': 'generated',
            'description': 'Cosmic deep space visual with two glowing entangled particles connected by an ethereal pulsing quantum thread of cyan and violet light.',
            'start_seconds': 0.0,
            'end_seconds': 5.0,
            'script_section_id': 'sec_01',
            'framing': 'extreme_wide cosmic space shot',
            'movement': 'slow camera dolly push-in',
            'transition_in': 'fade',
            'transition_out': 'crossfade',
            'overlay_notes': 'क्वांटम उलझन',
            'shot_language': {
                'shot_size': 'extreme_wide',
                'camera_movement': 'dolly_in',
                'lens_mm': 24,
                'lighting_key': 'low_key',
                'depth_of_field': 'deep',
                'color_temperature': 'cool'
            },
            'shot_intent': 'Hook the viewer with a breathtaking cosmic view of quantum entanglement.',
            'narrative_role': 'establish_context',
            'information_role': 'Visualizes instantaneous connection across cosmic distances.',
            'hero_moment': True,
            'texture_keywords': ['cosmic_dust', 'quantum_glow', 'cyan_sparkles'],
            'required_assets': [
                {
                    'type': 'image',
                    'description': 'A cinematic 9:16 vertical image of deep outer space with two glowing quantum particles connected by an ethereal shimmering cyan and gold energetic beam, starry nebula background, 8k resolution photorealistic.',
                    'source': 'generate'
                }
            ]
        },
        {
            'id': 'scene-02',
            'type': 'generated',
            'description': 'Microscopic quantum particle visualization, two luminous spinning energy orbs with intricate magnetic field lines intertwining.',
            'start_seconds': 5.0,
            'end_seconds': 13.0,
            'script_section_id': 'sec_02',
            'framing': 'macro close-up',
            'movement': 'rotational orbital camera move',
            'transition_in': 'crossfade',
            'transition_out': 'crossfade',
            'overlay_notes': 'QUANTUM ENTANGLEMENT',
            'shot_language': {
                'shot_size': 'close_up',
                'camera_movement': 'pan_right',
                'lens_mm': 50,
                'lighting_key': 'volumetric',
                'depth_of_field': 'shallow',
                'color_temperature': 'neutral'
            },
            'shot_intent': 'Explain the concept of quantum connection at subatomic scale.',
            'narrative_role': 'introduce_subject',
            'information_role': 'Shows the particle pairing mechanism.',
            'hero_moment': False,
            'texture_keywords': ['subatomic_particles', 'energy_waves', 'bioluminescent_glow'],
            'required_assets': [
                {
                    'type': 'image',
                    'description': 'Cinematic 9:16 vertical render of two subatomic spinning photon particles entangled together with glowing cyan and gold interference wave patterns, dark scientific laboratory background, ultra detailed.',
                    'source': 'generate'
                }
            ]
        },
        {
            'id': 'scene-03',
            'type': 'generated',
            'description': 'Dramatic portrait of Albert Einstein in thought, overlaid with vintage physics chalkboard equations and ethereal glowing quantum question marks.',
            'start_seconds': 13.0,
            'end_seconds': 24.0,
            'script_section_id': 'sec_03',
            'framing': 'medium shot',
            'movement': 'slow push-in with subtle lightning flicker',
            'transition_in': 'crossfade',
            'transition_out': 'crossfade',
            'overlay_notes': 'आइंस्टीन भी हैरान थे!',
            'shot_language': {
                'shot_size': 'medium',
                'camera_movement': 'dolly_in',
                'lens_mm': 85,
                'lighting_key': 'tungsten_warm',
                'depth_of_field': 'medium',
                'color_temperature': 'warm'
            },
            'shot_intent': 'Highlight historical conflict between Einstein and quantum mechanics.',
            'narrative_role': 'build_tension',
            'information_role': 'Illustrates Einstein skepticism regarding spooky action at a distance.',
            'hero_moment': True,
            'texture_keywords': ['sepia_tones', 'chalkboard_equations', 'dramatic_shadows'],
            'required_assets': [
                {
                    'type': 'image',
                    'description': 'A dramatic cinematic 9:16 portrait of Albert Einstein in deep contemplation, dark studio lighting, chalk formulas of relativity behind him with subtle glowing mysterious quantum symbols floating in the air, masterpiece.',
                    'source': 'generate'
                }
            ]
        },
        {
            'id': 'scene-04',
            'type': 'generated',
            'description': 'Nobel prize medal in physics radiating golden light with high-tech laser optic experiment laboratory in background.',
            'start_seconds': 24.0,
            'end_seconds': 34.0,
            'script_section_id': 'sec_04',
            'framing': 'medium wide',
            'movement': 'dynamic upward tilt',
            'transition_in': 'crossfade',
            'transition_out': 'crossfade',
            'overlay_notes': '2022 Physics Nobel Prize',
            'shot_language': {
                'shot_size': 'medium',
                'camera_movement': 'tilt_up',
                'lens_mm': 35,
                'lighting_key': 'golden_hour',
                'depth_of_field': 'medium',
                'color_temperature': 'warm'
            },
            'shot_intent': 'Deliver the triumphant scientific validation of the 2022 Nobel Prize.',
            'narrative_role': 'evidence',
            'information_role': 'Confirms that quantum entanglement was conclusively proved by Aspect, Clauser, and Zeilinger.',
            'hero_moment': True,
            'texture_keywords': ['gold_metal', 'optical_lasers', 'modern_lab'],
            'required_assets': [
                {
                    'type': 'image',
                    'description': 'Cinematic 9:16 vertical shot of a prestigious gleaming gold Nobel Prize physics medal in the foreground, with futuristic optical quantum laser beams and mirrors in a dark advanced physics lab background, 8k.',
                    'source': 'generate'
                }
            ]
        },
        {
            'id': 'scene-05',
            'type': 'generated',
            'description': 'Futuristic golden quantum computer chandelier processor glowing with cryogenic blue mists and cybernetic data streams.',
            'start_seconds': 34.0,
            'end_seconds': 43.0,
            'script_section_id': 'sec_05',
            'framing': 'wide shot',
            'movement': 'slow descending crane camera move',
            'transition_in': 'crossfade',
            'transition_out': 'crossfade',
            'overlay_notes': 'भविष्य की तकनीक',
            'shot_language': {
                'shot_size': 'wide',
                'camera_movement': 'crane_down',
                'lens_mm': 24,
                'lighting_key': 'neon',
                'depth_of_field': 'deep',
                'color_temperature': 'cool'
            },
            'shot_intent': 'Connect theoretical physics to practical world-changing technology.',
            'narrative_role': 'deliver_payload',
            'information_role': 'Demonstrates quantum computing and impenetrable cryptography.',
            'hero_moment': False,
            'texture_keywords': ['golden_cryostat', 'blue_nitrogen_frost', 'fiber_optics'],
            'required_assets': [
                {
                    'type': 'image',
                    'description': 'Cinematic 9:16 vertical photograph of an ornate golden quantum computer chandelier suspended in a dark high-tech server room with glowing blue holographic circuits and cryogenic frost vapors, ultra-realistic.',
                    'source': 'generate'
                }
            ]
        },
        {
            'id': 'scene-06',
            'type': 'generated',
            'description': 'Mind-bending split screen or reflection showing cosmic galaxy on one side and an identical quantum mirror image on the other, pulsing in unison.',
            'start_seconds': 43.0,
            'end_seconds': 49.0,
            'script_section_id': 'sec_06',
            'framing': 'wide symmetrical composition',
            'movement': 'hypnotic slow zoom in',
            'transition_in': 'crossfade',
            'transition_out': 'crossfade',
            'overlay_notes': 'Physics या जादू?',
            'shot_language': {
                'shot_size': 'wide',
                'camera_movement': 'zoom_in',
                'lens_mm': 35,
                'lighting_key': 'volumetric',
                'depth_of_field': 'deep',
                'color_temperature': 'mixed'
            },
            'shot_intent': 'Create maximum awe and philosophical wonder.',
            'narrative_role': 'emotional_beat',
            'information_role': 'Poses the core dilemma between physical reality and apparent magic.',
            'hero_moment': True,
            'texture_keywords': ['mirror_symmetry', 'cosmic_nebulae', 'quantum_sync'],
            'required_assets': [
                {
                    'type': 'image',
                    'description': 'Surreal cinematic 9:16 vertical visual of a cosmic mirror horizon where two identical glowing glowing orb worlds in opposite galaxies pulse with synchronized golden light rings, mystical science fiction aesthetic, 8k.',
                    'source': 'generate'
                }
            ]
        },
        {
            'id': 'scene-07',
            'type': 'generated',
            'description': 'Deep space backdrop with dark celestial vortex, fading into golden RahasyaLok logo aesthetic.',
            'start_seconds': 49.0,
            'end_seconds': 52.0,
            'script_section_id': 'sec_07',
            'framing': 'medium wide',
            'movement': 'slow outward drift and fade',
            'transition_in': 'crossfade',
            'transition_out': 'fade_to_black',
            'overlay_notes': 'RAHASYALOK | रहस्यों की दुनिया',
            'shot_language': {
                'shot_size': 'medium_wide',
                'camera_movement': 'dolly_out',
                'lens_mm': 50,
                'lighting_key': 'low_key',
                'depth_of_field': 'deep',
                'color_temperature': 'cool'
            },
            'shot_intent': 'Drive viewer comments and brand retention.',
            'narrative_role': 'call_to_action',
            'information_role': 'Prompts user to share thoughts on time travel.',
            'hero_moment': False,
            'texture_keywords': ['celestial_vortex', 'gold_particles', 'dark_space'],
            'required_assets': [
                {
                    'type': 'image',
                    'description': 'Mysterious cinematic 9:16 vertical view of a celestial space vortex with swirling deep blue and golden stellar dust, clean elegant composition suitable for YouTube Short outro branding, photorealistic.',
                    'source': 'generate'
                }
            ]
        }
    ]
}

validate_artifact('scene_plan', scene_plan)
with open(artifacts_dir / 'scene_plan.json', 'w', encoding='utf-8') as f:
    json.dump(scene_plan, f, ensure_ascii=False, indent=2)

write_checkpoint(
    Path('projects'),
    project_id,
    'scene_plan',
    'completed',
    {'scene_plan': scene_plan},
    pipeline_type='animated-explainer',
    style_playbook='clean-professional',
    human_approval_required=True,
    human_approved=True
)
print('Scene Plan checkpoint validated and written!')
