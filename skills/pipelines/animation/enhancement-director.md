# Enhancement Director - Animation Pipeline

## When To Use
Run post-compose and pre-publish to apply crisp line detail, subtle contrast enhancement, and output encode optimization to animated pieces.

## Prerequisites
- Composed render artifact: `render_report` from `compose` stage
- Tools: `video_quality_enhancer`, `ai_human_enhancer`

## Execution Steps
1. **Probe Composed Render**:
   - Inspect resolution, framerate, duration, and audio stream.
2. **Apply Video Quality Enhancer**:
   - For animation, use `gentle` or `balanced` to preserve vector crispness without introduces halos.
   - Output to `renders/final_enhanced.mp4`.
3. **AI Human Enhancer**:
   - Stylized 2D/3D characters are not photorealistic humans.
   - Unless photorealistic human reference is used, mark `not_applicable`.
4. **Emit Enhancement Report**:
   - Emit schema-valid `enhancement_report` artifact.
