# Enhancement Director - Avatar Spokesperson Pipeline

## When To Use
Run post-compose on presenter/avatar outputs to clean up edge artifacts, blend background layers, and polish eye/face clarity.

## Prerequisites
- `render_report` from `compose` stage
- Tools: `video_quality_enhancer`, `ai_human_enhancer`

## Execution Steps
1. Apply `video_quality_enhancer` with `gentle` profile.
2. Apply `ai_human_enhancer` with `natural` profile.
3. Emit schema-valid `enhancement_report`.
