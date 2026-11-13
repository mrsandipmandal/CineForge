# Enhancement Director - Cinematic Pipeline

## When To Use
Run post-compose and pre-publish to apply technical video quality enhancement and eligible AI human enhancement to the composed render.

## Prerequisites
- Composed render artifact: `render_report` from `compose` stage
- Tools: `video_quality_enhancer`, `ai_human_enhancer`, `upscale`, `face_enhance`, `color_grade`

## Execution Steps
1. **Probe and Evaluate Composed Render**:
   - Inspect resolution, framerate, duration, and audio streams.
2. **Apply Video Quality Enhancer**:
   - Choose profile: `cinematic` (recommended for mood and contrast) or `balanced`.
   - Never overwrite the original composed render. Output to `renders/final_enhanced.mp4`.
3. **Apply AI Human Enhancer** (Conditional):
   - If human subjects are present in the footage, apply `cinematic` or `natural` profile.
   - If no human subjects are detected, tool automatically records `not_applicable` and preserves footage without altering it.
4. **Emit Enhancement Report**:
   - Save schema-valid `enhancement_report` artifact to project `artifacts/` directory.
   - Verify that output media is decodable and audio synchronization is preserved.
