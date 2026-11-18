# Project: CineForge Production Improvements
# Scope: All Requirements (R1-R4)

## Architecture
- **Backlot UI/API**: Backlot server (`backlot/server.py`) manages configurations; frontend (`board.js`) provides interactive tabs.
- **Remotion Pipeline**: `remotion_episode_builder.py` maps inputs to Remotion config; `generate_remotion_episode.py` executes assembly.
- **Mythological Shorts Pipeline**: Validated manifest `pipeline_defs/mythological_shorts.yaml` enforcing strict authenticity (Vedic attire, Sanskrit, Sanjay narration) via schema-supported metadata.
- **Image Fallback Guard**: `lib/image_config.py` delegates OOM-prone generations to `local_diffusion.py` optimized for RTX 3050 4GB (attention/VAE slicing, CPU offload, dimension clamping).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | R1 | Backlot Image Priority & Provider Control UI | M1 | Survey |
| 2 | R2 | Automated 9:16 Vertical Remotion Episode Builder | M2 | Survey |
| 3 | R3 | Mythological Shorts Pipeline Definition | M3 | Survey |
| 4 | R4 | Low-VRAM Offline Diffusion Fallback Guard | M4 | Survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1 | Backlot API & UI Implementation | none | PLANNED |
| 2 | M2 | Remotion Episode Builder Implementation | none | PLANNED |
| 3 | M3 | Mythological Shorts Pipeline Definition | none | PLANNED |
| 4 | M4 | Low-VRAM Diffusion Guard Implementation | none | PLANNED |
| 5 | M5 | Final Verification & Integration | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### Backlot UI ↔ Server API
- `GET /api/settings/image`: returns full image provider status & config.
- `POST /api/settings/image`: accepts `{provider_priority, enabled_providers, auto_fallback, manual_mode, primary_provider}`.

### Remotion Builder ↔ Video Compose
- Input: `timestamps`, `scenes` (with image/audio assets), `subtitles`.
- Output: Remotion composition config (9:16 vertical).

### Image Guard ↔ Image Selector
- Fallback flow: `ImageSelector` -> `lib/image_config.py` (check availability) -> `tools/graphics/local_diffusion.py` (generate fallback).
