# Enhancement Director - Talking Head Pipeline

## When To Use
Run post-compose on speaker-led footage to enhance voice clarity, natural skin smoothing, eye sharpness, and lighting balance.

## Prerequisites
- `render_report` from `compose` stage
- Tools: `video_quality_enhancer`, `ai_human_enhancer`, `face_enhance`, `eye_enhance`

## Execution Steps
1. Apply `video_quality_enhancer` with `balanced` profile for camera noise cleanup and contrast.
2. Apply `ai_human_enhancer` with `natural` or `detail_recovery` profile. Verify authentic skin texture and identity retention.
3. Emit schema-valid `enhancement_report`.
