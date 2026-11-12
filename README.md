<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/cineforge-dark.svg">
    <img src="assets/cineforge-light.svg" alt="CineForge mascot" width="220">
  </picture>
</p>

<p align="center"><sub><em>Monty the Clapper — the official mascot of CineForge</em></sub></p>

<h1 align="center">CineForge Matrix Studio</h1>

<p align="center"><strong>Autonomous AI Film & Video Production System</strong></p>
<p align="center"><em>Turn your AI assistant into an end-to-end film studio: research, scripting, character consistency, voice cloning, motion editing, and final composition.</em></p>

<p align="center">
  <a href="#quick-start--installation">Quick Start</a> &nbsp;·&nbsp;
  <a href="#matrix-studio-control-room">Matrix Control Room</a> &nbsp;·&nbsp;
  <a href="#core-capabilities--use-cases">Use Cases</a> &nbsp;·&nbsp;
  <a href="#science-explainer-shorts--multi-language-autonomous-production">Science Explainer</a> &nbsp;·&nbsp;
  <a href="#production-pipelines">Pipelines</a> &nbsp;·&nbsp;
  <a href="#architecture--design-principles">Architecture</a> &nbsp;·&nbsp;
  <a href="docs/SCIENCE_EXPLAINER.md">Explainer Guide</a> &nbsp;·&nbsp;
  <a href="docs/PROVIDERS.md">Providers</a> &nbsp;·&nbsp;
  <a href="docs/IDENTITY_LIBRARY.md">Identity Library</a> &nbsp;·&nbsp;
  <a href="docs/VOICE_IDENTITY.md">Voice Studio</a> &nbsp;·&nbsp;
  <a href="docs/FACE_IDENTITY.md">Face Studio</a> &nbsp;·&nbsp;
  <a href="AGENT_GUIDE.md">Agent Guide</a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-00ff66.svg?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/remotion-4.0-E50914?style=flat-square" alt="Remotion">
  <img src="https://img.shields.io/badge/ffmpeg-8.0-007808?style=flat-square" alt="FFmpeg">
  <img src="https://img.shields.io/badge/security-CodeQL%20%E2%9C%93-brightgreen?style=flat-square" alt="CodeQL">
</p>

<p align="center"><strong>Connect & Community</strong></p>

<p align="center">
  <a href="https://www.youtube.com/@CineForgeLab"><img src="https://img.shields.io/badge/YouTube-%40CineForgeLab-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="YouTube"></a>
  <a href="https://x.com/mr_sandipmandal"><img src="https://img.shields.io/badge/X-%40mr__sandipmandal-111111?style=for-the-badge&logo=x&logoColor=white" alt="X"></a>
  <a href="https://github.com/mrsandipmandal/CineForge/discussions"><img src="https://img.shields.io/badge/Community-GitHub%20Discussions-0b1220?style=for-the-badge&logo=github&logoColor=white" alt="GitHub Discussions"></a>
</p>

---

## Production Studio Showcase

CineForge is an agent-first production system where plain language instructions drive verified, multi-stage pipelines. Below are sample animated and motion productions generated through CineForge:

### 1. Futuristic Mars Colonization 2099 (মঙ্গল গ্রহের মানব সভ্যতা)
Full animated sci-fi production featuring procedural 1080p Martian landscapes, geodesic biodomes, subterranean lava-tube transit, Sarvam AI native West Bengal Bengali (`bn-IN`) voice narration, and cinematic Ken-Burns motion choreography:

<div align="center">
  <video src="assets/futuristic-mars-colony.mp4" poster="assets/futuristic-mars-colony-poster.png" width="100%" controls autoplay loop muted></video>
  <p><sub><em>Rendered with CineForge Animated Explainer pipeline (1080p, 30fps) — Audio mix with Sarvam AI <code>bn-IN</code> TTS and ambient sci-fi synthesizer bed.</em></sub></p>
</div>

### 2. Matrix Studio Motion Title & Kinetic Typography
<div align="center">
  <video src="assets/cineforge-demo.mp4" poster="assets/cineforge-demo-poster.png" width="100%" controls autoplay loop muted></video>
  <p><sub><em>Rendered with CineForge Remotion engine (1080p, 30fps) — typography, layout, timing, and audio muxing generated via pipeline.</em></sub></p>
</div>

---

## Matrix Studio Control Room

**Backlot Matrix Edition** (`http://127.0.0.1:4750/`) provides real-time telemetry, visual approval gates, asset contact sheets, and persistent identity registries in a cyberpunk green-on-black terminal UI (`#030804` background, `#00ff66` phosphor green accents, CRT scanlines, and animated digital rain).

### 1. Live Project Control Room (`/p/futuristic-mars-colony`)
Monitors pipeline stages in real time. Shows automated and human approval checkpoints, duration metrics, and complete stage state tracking across research, script, assets, edit, and composition:

<p align="center">
  <img src="assets/matrix-studio-mars-board.png" alt="CineForge Matrix Studio Live Board - Mars 2099" width="960">
</p>

### 2. Visual Storyboard & Shot Planner (`/p/{project_id}#storyboard`)
Inspect generated visual scene plates, camera motion choreography (push-in, pan, dolly), subtitle timing, and prompt directions:

<p align="center">
  <img src="assets/matrix-studio-mars-storyboard.png" alt="CineForge Storyboard and Scene Plan" width="960">
</p>

### 3. Studio Multi-Project Dashboard (`/`)
Live bird's-eye view across all projects in the pipeline, tracking generation spend, render count, and stage progress:

<p align="center">
  <img src="assets/matrix-studio-dashboard.png" alt="CineForge Studio Multi-Project Dashboard" width="960">
</p>

---

## Core Capabilities & Use Cases

CineForge differs fundamentally from ordinary "single-prompt prompt-to-video" tools. It mirrors a professional production studio:

### 1. Reference-Driven Video Production
Paste any YouTube video, Short, TikTok, or Instagram Reel:
```text
"Here is a YouTube Short I love. Analyze its structure, pacing, and hooks, and make an original 60-second version about quantum computing."
```
The agent executes `video_analyzer`, extracts the transcript, breaks down scene pacing, and proposes **2-3 differentiated creative treatments** with clear cost projections.

### 2. Multi-Angle Character & Face Consistency
Create reusable characters in `sample-files/characters/` with multi-view portraits (`front`, `left_quarter`, `right_quarter`, `expression`). The system injects conditioning bundles into video models (Kling, Seedance, Wan2.1) so the same character appears consistently across different scenes, camera angles, and projects.

### 3. Multilingual Voice Studio & Offline Fallback (Bengali bn-IN, Hindi, English, Spanish, Arabic & More)
Native multi-language voice identity management with intelligent hardware profiling:
- **West Bengal Bengali (`bn-IN`)**: Sarvam AI (`bulbul:v3`), AI4Bharat IndicTTS (IIT Madras), and neural Edge TTS (`bn-IN-BashkarNeural`, `bn-IN-TanishaaNeural`) preserving authentic Indian Bengali phonetics, syntax, and cultural cadence.
- **Global Neural Voice Fleet (`edge_tts`)**: Instant zero-cost access to 400+ neural voices across 70+ languages (English, Hindi, Spanish, French, German, Japanese, Arabic) with micro-pitch and rate calibration.
- **Offline Hardware Routing**: Automated PC VRAM & core detection (`local_hardware_probe.py`) routes automatically between fast offline Piper TTS, medium IndicTTS, and high-fidelity IndicF5 based on local capacity.
- **Groq LPU Acceleration**: Sub-second scriptwriting and Whisper Large v3 audio transcription at 300+ tokens/sec.
- **OpenRouter Multi-Model Gateway**: Zero-cost access to state-of-the-art open weights (DeepSeek R1, Llama 3.3, Qwen) and xAI Grok.
- Supports reference-audio voice cloning (ElevenLabs, Fish Audio, IndicF5, Coqui XTTS) with mandatory actor consent verification (`consent_verified: true`).

### 4. Zero-Cost Real-Footage Documentaries
CineForge can build real documentaries without paying for generative video models:
- Searches and downloads high-resolution open archival footage from **Archive.org**, **NASA**, and **Wikimedia Commons**.
- Indexes footage with CLIP semantic embeddings and cuts a synchronized motion timeline with **Piper TTS** (offline local voice) and **FFmpeg**.

### 5. Automated Social Clip Factory
Feed in an hour-long podcast, interview, or lecture. The agent transcribes with WhisperX, scores moments for hook strength, trims optimal 30-60 second clips, adds TikTok-style word-level subtitles, and re-frames to 9:16 vertical video.

---

<a id="science-explainer-shorts--multi-language-autonomous-production"></a>
## 🔬 Science Explainer Shorts — Multi-Language Autonomous Production

CineForge now includes an interactive, end-to-end production workflow for **Science Mystery Shorts, Nature Curiosities, and Educational Viral Videos**. It combines dynamic real-time web research, high-impact scriptwriting, AI imagery, 3D Ken-Burns camera movement, acoustic ambient synthesis, and burned kinetic typography — with **zero required API keys ($0.00 compute cost)**.

```
"make a science video" ──▶ Dynamic Language ──▶ Live Web Research ──▶ AI-Scored Top 6 Topics
                                                                             │
                                                                             ▼
Final Broadcast MP4 ◀── Full Pipeline ◀── Single Human Approval ◀── Interactive Feature Menu
 (Shorts/Reels 1080p)    (Images/TTS/Mix)    ("Approved!")          (Format, Style, Tone)
```

### Key Workflow Highlights

1. **Dynamic Language Selection**: The studio asks for your preferred language first, then switches **all subsequent user interaction, narration, script, and subtitles** into that language immediately. Supported out of the box: English, Bengali (বাংলা), Hindi (हिन्दी), Spanish (Español), French (Français), German (Deutsch), Arabic (العربية), Japanese (日本語), and more.
2. **AI-Led Trend & Fact Research**: Silently browses current scientific publications and viral anomalies, scoring candidates by *surprise factor*, *visual potential*, and *viewer retention* before proposing the top 6 concepts.
3. **Interactive Feature Menu (1 Message)**: Configure video format (9:16 vertical Short, 16:9 landscape, 1:1 square), aesthetic art direction (Photorealistic CGI, Nature Doc, Flat Vector, Dark Noir), narrator tone, video duration (45s, 60s, 90s), and soundscape in a single response (or reply `"all default"`).
4. **Transparent Production Plan & 1-Gate Approval**: Inspect the 5-scene breakdown, script preview, asset map, exact runtime, and cost breakdown before compute begins. Once approved, the agent runs research, scripting, image generation, audio synthesis, subtitles, and final FFmpeg assembly autonomously without interruptions.

### Supported Video Platforms & Technical Pacing

| Platform | Format | Resolution | Optimal Length | Pacing & Algorithmic Optimization |
| :--- | :---: | :---: | :---: | :--- |
| **YouTube Shorts** | `9:16` | 1080×1920 | 50–60s | 3s visual cliffhanger, centered subtitles with 170px bottom safety margin |
| **Instagram Reels** | `9:16` | 1080×1920 | 60–75s | Aesthetic 3D CGI visuals, crisp contrast typography, explore feed reach |
| **TikTok** | `9:16` | 1080×1920 | 45–60s | High-energy curiosity hook, right-margin safe zone for interactive buttons |
| **Facebook Reels** | `9:16` | 1080×1920 | 60s | High universal appeal, family/nature mysteries, clear centered subtitles |
| **YouTube Standard** | `16:9` | 1920×1080 | 75–90s | Classical horizontal framing, deep documentary narration, playlist-ready |
| **Instagram Feed** | `1:1` | 1080×1080 | 45–60s | Balanced square composition, high contrast typography |
| **Snapchat Spotlight** | `9:16` | 1080×1920 | 30–45s | Fast dopamine pace, 220px bottom margin for UI buttons |
| **Pinterest Idea Pins** | `9:16` | 1080×1920 | 45–60s | Evergreen educational value, step-by-step visual clarity |
| **LinkedIn Video** | `16:9` | 1920×1080 | 60s | Innovation angle, high-readability professional subtitles |
| **X / Threads** | `9:16` / `16:9` | 1080×1920 | 45–60s | Viral cliffhanger, instant curiosity hook in first 2 seconds |

> 📖 **Full Guide & Interactive Documentation**: See [`docs/SCIENCE_EXPLAINER.md`](docs/SCIENCE_EXPLAINER.md) for full voice registries, ASS subtitle templates, FFmpeg zoompan mathematics, and sample sessions.

---

## Quick Start & Installation

### Prerequisites

- **Python 3.10, 3.11, or 3.12** — [python.org](https://www.python.org/downloads/)
- **Node.js 20+** — [nodejs.org](https://nodejs.org/)
- **FFmpeg 6.0+** — `sudo apt install ffmpeg` / `brew install ffmpeg` / [ffmpeg.org](https://ffmpeg.org/download.html)
- **Git** — [git-scm.com](https://git-scm.com/)

### Step 1: Clone & Setup

```bash
# 1. Clone repository
git clone https://github.com/mrsandipmandal/CineForge.git
cd CineForge

# 2. Automated setup (creates .venv, installs Python & Remotion packages)
make setup
```

*Manual Setup alternative (macOS/Linux):*
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cd remotion-composer && npm install && cd ..
pip install piper-tts
cp .env.example .env
```

*Manual Setup alternative (Windows PowerShell):*
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cd remotion-composer; npm install; cd ..
pip install piper-tts
Copy-Item .env.example .env
```

### Step 2: Configure Environment

Every API key is optional. The system operates fully offline with Piper TTS, open archival stock, and Remotion/HyperFrames:

```bash
# Edit .env to add keys for cloud models you wish to enable:
cp .env.example .env

# Popular options:
# ELEVENLABS_API_KEY=your_key     # Premium voice cloning & sound effects
# FAL_KEY=your_key                # FLUX images, Kling video, Veo video
# PEXELS_API_KEY=your_key         # Free stock footage
# PIXABAY_API_KEY=your_key        # Free stock audio & video
```

### Step 3: Launch Backlot Matrix Studio

```bash
# Start Backlot Live Control Room (accessible at http://127.0.0.1:8765)
python -m backlot.server

# Or open browser directly:
python -m backlot open
```

---

## Production Pipelines

Every video production request maps to an auditable pipeline manifest in `pipeline_defs/`:

```
research  →  proposal  →  script  →  scene_plan  →  assets  →  edit  →  compose  →  publish
```

| Pipeline | Target Format | Primary Use Case |
| :--- | :--- | :--- |
| **`animated_explainer`** | 16:9 / 9:16 | Educational explainers, tech breakdowns, diagrams, voiceover |
| **`character_animation`** | 16:9 / 9:16 | 2D/3D character rigs, pose libraries, GSAP timelines, SVG acting |
| **`cinematic`** | 16:9 / 21:9 | Cinematic trailers, high-concept teasers, sci-fi/fantasy mood pieces |
| **`documentary_montage`** | 16:9 | Archival documentaries, historical essays (Archive.org, NASA, Wikimedia) |
| **`youtube_shorts`** | 9:16 | Fast-paced short-form content, kinetic subtitles, hook optimization |
| **`talking_head`** | 9:16 / 16:9 | Presenter videos, SadTalker/Wav2Lip avatar sync, interviews |
| **`clip_factory`** | 9:16 | Batch repurposing long-form footage into ranked social clips |
| **`screen_demo`** | 16:9 | Polished software walkthroughs, cursor smoothing, terminal demos |

---

## Architecture & Design Principles

```
CineForge Matrix/
├── tools/                 # 100+ production tools (BaseTool subclasses)
│   ├── audio/             # Voice identity, TTS selector, audio mixer, Suno
│   ├── avatar/            # Character face identity, talking head, lip-sync
│   ├── video/             # Video generation, clip search, stitcher, trimmer
│   ├── graphics/          # FLUX, Imagen, Grok, diagrams, code snippets
│   ├── analysis/          # WhisperX transcriber, scene detector, frame sampler
│   └── enhancement/       # Face restoration (CodeFormer), upscale, background removal
│
├── sample-files/          # Identity Library: voices/, faces/, characters/, manifests/
├── pipeline_defs/         # Pipeline manifests (stages, tools, human approval gates)
├── skills/                # Stage director skills & quality review checklists
├── backlot/               # Backlot Matrix Studio (FastAPI, SSE change feed, Matrix UI)
├── remotion-composer/     # React / Remotion composition engine (1080p/4K video)
├── lib/                   # Checkpoints, pipeline loader, cost tracker, state machine
└── tests/                 # 100+ contract tests, integration tests, security tests
```

### Core Architecture Rules:
1. **The AI Agent is the Director**: Orchestration logic lives in transparent, readable markdown instructions (`skills/pipelines/`). Python provides robust tools and state persistence.
2. **Deterministic Checkpointing**: Every stage saves to `projects/<name>/checkpoints/latest.json`. Productions can be resumed, replayed, or branched at any point.
3. **Auditable Decision Log**: Every provider selection, cost estimate, and visual style decision is logged with alternatives considered and confidence scores.
4. **Pre-Compose & Post-Render Quality Gates**: Automated validation stops broken plans before spending compute. Post-render self-review runs `ffprobe`, audio clipping checks, and frame analysis before presenting output.

---

## Testing & Quality Assurance

CineForge includes an extensive automated test suite covering BaseTool contracts, identity library scanning, Backlot endpoints, and security boundaries:

```bash
# Run contract and library tests (zero API keys needed)
make test-contracts

# Run full test suite with coverage
pytest tests/ -v

# Run Backlot backend smoke tests
pytest tests/backlot/ -v
```

---

## Documentation Index

- [Science Explainer Shorts Production Guide](docs/SCIENCE_EXPLAINER.md) — Autonomous multi-language science & mystery short video pipeline.
- [Identity Library Architecture](docs/IDENTITY_LIBRARY.md) — Persistent voice and character profile layout.
- [Voice Identity Studio & Capability Matrix](docs/VOICE_IDENTITY.md) — Multilingual setup, cloning, and consent protocol.
- [Face & Character Identity Studio](docs/FACE_IDENTITY.md) — Multi-view character reference guidelines.
- [Matrix Studio UI & Terminal System](docs/MATRIX_UI.md) — Backlot green-on-black interface design system.
- [AI Provider Matrix & Pricing](docs/PROVIDERS.md) — Detailed guide covering 60+ video, image, and voice providers.
- [Upgrade & Migration Guide](docs/UPGRADE_MIGRATION.md) — Transitioning from legacy setups.
- [Agent Operating Contract](AGENT_GUIDE.md) — Mandatory agent protocols and execution rules.

---

## Community & Support

- **YouTube**: [@CineForgeLab](https://www.youtube.com/@CineForgeLab) — Video tutorials, production breakdowns, and showcase reels.
- **X (Twitter)**: [@mr_sandipmandal](https://x.com/mr_sandipmandal) — Developer updates, release announcements, and build notes.
- **GitHub Discussions**: [CineForge Discussions](https://github.com/mrsandipmandal/CineForge/discussions) — Ask questions, suggest new pipelines, and share generated films.
- **Issues**: [GitHub Issue Tracker](https://github.com/mrsandipmandal/CineForge/issues) — Report bugs or request tools.

<p align="center">
  <a href="https://www.buymeacoffee.com/sandiptaibt" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="60" width="217">
  </a>
</p>

---

## License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.
