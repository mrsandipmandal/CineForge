# OpenMontage Matrix — UI Architecture & Matrix Transformation Plan

**Date:** 2026-11-06  
**Component:** Backlot Living Storyboard & Production Board  
**Stack:** FastAPI (Python), Vanilla ES Modules, CSS Custom Properties, SSE (`EventSource`)  

---

## 1. Existing Backlot Frontend Architecture

The Backlot UI is intentionally dependency-free (no React, Vue, or Webpack bundle step required at runtime). It executes directly in modern web browsers:

```
backlot/
├── server.py              # FastAPI server (SSE publisher, thumb generator, media streaming)
├── state.py               # State aggregation engine (reads checkpoints, manifests, assets)
└── ui/
    ├── board.html         # Project board SPA shell (<div id="app">, <div id="modal">, <audio id="player">)
    ├── board.js           # Main production board rendering logic (48KB ES module)
    ├── board.css          # Design system, layout, and visual styles (48KB CSS)
    ├── index.html         # Project Library shell
    ├── library.js         # Library view renderer (fetches /api/projects)
    └── lib.js             # Utility functions (formatting, debounce, SSE connection)
```

### Key UI Features Already Implemented:
- **Header Slate:** Project clapper, title, stage rail, live progress indicator, audio playback toolbar.
- **Stage Rail:** Interactive stage status indicators (`pending`, `in_progress`, `awaiting_human`, `completed`, `failed`, `gate_skipped`).
- **Main Views:**
  - *Filmstrip*: Join of `scene_plan` × `script` × `asset_manifest` displaying shot cards with thumbnails, narration, and status.
  - *Screenplay*: Clean formatted script view with dialogue and scene headings.
  - *Decisions Rail*: Chronological, append-only log of model, voice, runtime, and approval decisions.
  - *Spend & Cost Meter*: Real-time budget progress bar showing reserved vs actual USD costs.
  - *Activity Stream*: Tool telemetry (`events.jsonl`) showing active tool calls, execution durations, and errors.
  - *Replay Run*: Scrubbable time-travel playback of the production lifecycle from start to finish.

---

## 2. Matrix Studio Transformation Specification

The user requires transforming the Backlot visual identity into a **professional Matrix Green-on-Black / Terminal / Cinematic Production Control Room**:

### Design Tokens:

```css
:root {
  --matrix-bg: #050805;
  --matrix-surface: #0A100C;
  --matrix-panel: #0D1510;
  --matrix-border: #193523;
  --matrix-border-bright: #275938;
  --matrix-green: #00FF66;
  --matrix-green-soft: #42FF9A;
  --matrix-green-glow: rgba(0, 255, 102, 0.25);
  --matrix-text: #C4E8CC;
  --matrix-muted: #668772;
  --matrix-warning: #FFB547;
  --matrix-error: #FF4545;

  --font-mono: "JetBrains Mono", "IBM Plex Mono", "Courier New", monospace;
  --font-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
```

### Key Architectural Upgrades:

1. **Navigation Bar & Multi-View Switcher:**
   - Tabs: `CONTROL ROOM`, `STORYBOARD`, `VOICE LAB`, `FACE LAB`, `ASSETS`, `DECISIONS`, `PROVIDERS`, `SETTINGS`.
2. **Voice Lab Panel:**
   - Visual catalog of voice profiles in `sample-files/voices/`.
   - Audio waveform preview, language badges (`bn-IN`, `hi-IN`, `en-US`), cloning status, and test synthesis preview.
3. **Face Lab Panel:**
   - Character cards from `sample-files/faces/` and `sample-files/characters/`.
   - Reference photo gallery (front, side, expression), consistency anchors, and talking-head preview modal.
4. **Cinematic Matrix Terminal Visuals:**
   - Matrix digital rain canvas background (subtle, paused when inactive, respecting `prefers-reduced-motion: reduce`).
   - Blinking green terminal cursor on active status badges and search inputs.
   - Restrained high-tech scanlines overlay (`pointer-events: none`).
   - Clean, high-contrast monospace typography.
