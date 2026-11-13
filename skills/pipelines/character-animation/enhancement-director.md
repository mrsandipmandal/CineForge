# Enhancement Director - Character Animation Pipeline

## When To Use
Run post-compose on rigged 2D/3D character animation to ensure clean alpha blending, crisp vector lines, and audio mix balance.

## Prerequisites
- `render_report` from `compose` stage
- Tools: `video_quality_enhancer`

## Execution Steps
1. Apply `video_quality_enhancer` with `gentle` profile.
2. Cartoon / rigged characters are not realistic human subjects: mark `ai_human_enhancer` as `not_applicable`.
3. Emit schema-valid `enhancement_report`.
