# Enhancement Director - Animated Explainer Pipeline

## When To Use
Run post-compose to ensure high-definition clarity, diagram line sharpness, and audio-video integrity before publishing.

## Prerequisites
- `render_report` from `compose` stage
- Tools: `video_quality_enhancer`

## Execution Steps
1. Apply `video_quality_enhancer` with `gentle` or `balanced` profile.
2. AI Human Enhancer: mark `not_applicable` for graphic explainers.
3. Emit schema-valid `enhancement_report`.
