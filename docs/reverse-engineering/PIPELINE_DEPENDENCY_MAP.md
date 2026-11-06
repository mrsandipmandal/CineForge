# OpenMontage Matrix — Pipeline Dependency Map

**Date:** 2026-11-06  
**Audited Pipelines:** 13 declarative manifests in `pipeline_defs/`  

---

## 1. Pipeline Catalog & Characteristics

| Pipeline Manifest | Category | Purpose | Total Stages | Default Budget | Approval Gates | Supported Playbooks |
|---|---|---|---|---|---|---|
| `animated-explainer.yaml` | `generated` | Topic-to-video AI explainer | 8 | $2.00 | proposal, script, scene_plan, assets, publish | clean-professional, flat-motion-graphics, premium-minimalist |
| `cinematic.yaml` | `cinematic` | Teaser, trailer, narrative edit | 8 | $5.00 | proposal, script, scene_plan, assets, publish | cinematic-epic, noir, cyberpunk, premium-minimalist |
| `character-animation.yaml` | `animation` | Rigged cartoon & SVG character action | 10 | $1.00 | character_design, rig_plan, scene_plan, assets, compose | flat-motion-graphics, ink-sketch, retro-cartoon |
| `avatar-spokesperson.yaml` | `talking_head` | Presenter-led digital twin video | 7 | $3.00 | proposal, script, scene_plan, assets, publish | clean-professional, corporate-presentation |
| `talking-head.yaml` | `talking_head` | Footage-led speaker editing | 7 | $0.50 | source_review, script, scene_plan, assets, publish | clean-professional, podcast-visual |
| `screen-demo.yaml` | `screen_recording` | App walkthrough / terminal demo | 7 | $0.50 | proposal, script, scene_plan, assets, publish | minimalist-diagram, clean-professional |
| `hybrid.yaml` | `hybrid` | Footage + AI generation blend | 8 | $3.00 | proposal, script, scene_plan, assets, publish | clean-professional, documentary-montage |
| `localization-dub.yaml` | `custom` | Subtitle, dubbing, and re-voicing | 6 | $2.00 | source_review, translation, assets, compose | multi-lingual profiles |
| `podcast-repurpose.yaml` | `hybrid` | Multi-clip extraction & highlights | 7 | $1.00 | source_review, clip_selection, edit, compose | social-reel, viral-hook |
| `clip-factory.yaml` | `custom` | Batch vertical clips from long source | 6 | $1.00 | source_review, batch_plan, edit, publish | tiktok-fast, youtube-shorts |
| `documentary-montage.yaml`| `cinematic` | Historical / montage narrative | 8 | $4.00 | proposal, script, scene_plan, assets, edit, publish | archival-film, vintage-documentary |
| `animation.yaml` | `animation` | Kinetic typography & motion graphics | 8 | $1.50 | proposal, script, scene_plan, assets, publish | flat-motion-graphics, ink-sketch |
| `framework-smoke.yaml` | `test` | Two-stage pipeline verification | 2 | $0.00 | none (automated) | test-playbook |

---

## 2. Canonical Stage-to-Artifact Flow

```
Stage: research        ──► Artifact: research_brief.json
                           │
Stage: proposal/idea   ──► Artifact: brief.json or proposal_packet.json
                           │
Stage: script          ──► Artifact: script.json
                           │
Stage: scene_plan      ──► Artifact: scene_plan.json
                           │   (Contains: scenes[], shot_type, duration, voice_id, character_id)
                           │
Stage: assets          ──► Artifact: asset_manifest.json
                           │   (Contains: assets[], path, prompt, provider, model, seed, identity_ref)
                           │
Stage: edit            ──► Artifact: edit_decisions.json
                           │   (Contains: cuts[], transitions[], subtitles, music_track, render_runtime)
                           │
Stage: compose         ──► Artifact: render_report.json + renders/final.mp4
                           │
Stage: publish         ──► Artifact: publish_log.json
```

---

## 3. Identity Reference Flow in the Pipeline

With the OpenMontage Matrix identity architecture, voice and face identities flow deterministically through the canonical artifacts:

```
[sample-files/ identity library]
   │
   ├─► Voice Profile: "dr_elena_vance" (Audio samples + bn/hi/en language metadata)
   └─► Face Profile:  "elena_vance" (Front, side, expression reference images)
           │
           ▼
[Stage 1: Proposal / Script]
   - Records voice_profile_id and character_profile_id in proposal_packet.json
           │
           ▼
[Stage 3: Scene Plan]
   - Scene items reference explicit identity pointers:
     {
       "scene_id": "scene-01",
       "voice_profile": "dr_elena_vance",
       "character_profile": "elena_vance",
       "audio_strategy": "voice_clone",
       "visual_strategy": "reference_conditioned"
     }
           │
           ▼
[Stage 4: Asset Generation]
   - TTS selector passes reference audio to cloning providers (e.g. Fish Audio / ElevenLabs).
   - Video generator passes reference photos to image-conditioned models (Seedance, Kling, Wan).
   - Generates assets into `projects/<id>/assets/audio/` and `projects/<id>/assets/video/`.
   - Records identity provenance in `asset_manifest.json`.
           │
           ▼
[Stage 5 & 6: Edit & Compose]
   - Assembles identity-consistent shots into final video deliverable.
```
