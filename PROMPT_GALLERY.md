# Prompt Gallery

Tested prompts that produce impressive videos. Copy any prompt into your AI coding assistant after running `make setup`.

## 🔬 Science Explainer & Mystery Shorts (Multi-Language, Zero-Cost)

The `bengali-science-explainer` skill provides an **interactive, multi-language, AI-researched production suite** designed specifically for **YouTube Shorts, TikTok, Instagram Reels, and YouTube Standard**. It runs live web research, suggests top-scoring scientific curiosities, walks you through an interactive feature selector, and autonomously renders 1080p video with Ken-Burns motion, neural voiceover, and burned typography — with **$0.00 API spend**.

See [`docs/SCIENCE_EXPLAINER.md`](docs/SCIENCE_EXPLAINER.md) for the complete architecture and voice tables.

### 1. Interactive Launch (Dynamic Language & AI Topic Discovery)

> "Make a science video"

**What happens:**
1. The agent asks: *"What language do you want your video in? (English, Bengali, Hindi, Spanish, French, Arabic...)"*
2. Automatically performs live web research to unearth 15 trending scientific phenomena.
3. Ranks candidates by *surprise factor* and *visual potential*, presenting the top 6 with dramatic hooks.
4. Walks you through an interactive feature menu (format, visual art direction, tone, duration, audio bed).
5. Shows a complete 5-scene production plan and executes autonomously upon your `"approved"` confirmation.

**Estimated time:** 8–12 minutes | **Cost:** $0.00

---

### 2. Deep Sea Mystery — Bengali (`bn-IN`)

> "ব্যারেলআই মাছের স্বচ্ছ মাথা ও সবুজ চোখ নিয়ে একটা ৬০ সেকেন্ডের বাংলা ইউটিউব শর্টস ভিডিও বানাও। ডার্ক ও রহস্যময় স্টাইল এবং সিনেমাটিক ৩ডি ভিজ্যুয়াল ব্যবহার করো।"

**What you get:**
- Authentic West Bengal Bengali neural voiceover (`bn-IN-BashkarNeural`, -3% rate, -2Hz pitch).
- 5 photorealistic deep-sea 3D scene plates (transparent skull, upward-facing green tubular eyes, bioluminescent abyssal habitat).
- Synthesized underwater ambient soundscape (FFmpeg Brownian noise + 40Hz sub-bass).
- Crisp Bengali subtitles burned with Nirmala UI 56pt bold typography.
- Output: `projects/barreleye-mystery/renders/final.mp4` (1080×1920, 60s).

---

### 3. Biology Superpower — English (`en-US`)

> "Create a 60-second YouTube Short explaining why the mantis shrimp punches at the speed of a bullet and sees 16 visual pigments. Use a high-energy curious tone and 9:16 vertical framing."

**What you get:**
- Dynamic neural English narration (`en-US-JennyNeural`).
- 5 high-speed biological CGI plates illustrating cavitation bubbles and hyperspectral compound eyes.
- Smooth Ken-Burns push-in and dolly transitions rendered via FFmpeg.
- Centered bold white typography with 2px black outline, clearing platform UI safe zones.

---

### 4. Cosmic Biology — Hindi (`hi-IN`)

> "अंतरिक्ष और उबलते पानी में भी जीवित रहने वाले टारडीग्रेड (Tardigrade) के बारे में एक 60-सेकंड की शॉर्ट्स वीडियो बनाओ। हिंदी में स्पष्ट वॉइसओवर और सबटाइटल रखो।"

**What you get:**
- Clear, natural Hindi narration (`hi-IN-NeerjaNeural`).
- Microscopic extreme-close-up keyframe plates of cryptobiosis and cosmic radiation shielding.
- Synchronized Hindi Devanagari typography rendered with clean Unicode support.

---

### 5. Instant Single-Prompt Direct Spec Override

> "Run science-explainer: Subject is 'Venus Flytrap 9-millisecond snap mechanism'. Language is English. Format 9:16 vertical Short, duration 60s, visual style Nature Documentary, tone Fast & Punchy, audio ambient nature bed, subtitle style bold white bottom-center. Proceed with all defaults upon plan approval."

**What you get:**
- Bypasses intermediate feature Q&A and generates the production plan directly.
- Renders a complete 5-scene explainer ready for YouTube Shorts and TikTok upload.

---

## Zero-Key Demos (instant, no API keys)

These render pre-built compositions using only Remotion components — animated charts, typography, data visualization. No external services, no cost, no waiting.

```bash
make demo                         # Render all three demos
./render-demo.sh world-in-numbers # Render one specific demo
./render-demo.sh --list           # See all available demos
```

| Demo | Duration | What It Shows |
|------|----------|--------------|
| **world-in-numbers** | 45s | KPI grids, bar charts, pie charts, line charts, comparison cards, stat reveals |
| **code-to-screen** | 50s | Developer education: HTTP request lifecycle with progress bars, charts, callouts |
| **focusflow-pitch** | 40s | Startup pitch deck: traction metrics, revenue donut chart, customer testimonial |

---

## Zero-Key Prompts (free, works out of the box)

These use the full agent pipeline — research, scripting, asset generation, composition — using only free tools (Piper TTS, stock media, Remotion).

### Data Explainer

> "Make a 45-second animated explainer about why the sky is blue. Use data visualization and animated text — no images needed, just charts, stat cards, and typography."

**What you get:** Research-grounded script, Piper narration, Remotion-animated scenes with text cards, stat reveals, and callout boxes. Subtitles included.

**Estimated time:** 5-10 minutes | **Cost:** $0

### Quick Fact Video

> "Create a 60-second data-driven video about coffee consumption around the world. Include bar charts comparing countries and a pie chart of coffee types."

**What you get:** Animated data visualization with charts, comparison cards, and narrated facts. All data sourced from the research stage.

**Estimated time:** 8-12 minutes | **Cost:** $0

### History Explainer

> "Make a short explainer about how the internet works, with narration and animated captions. Keep it under 60 seconds."

**What you get:** Structured explainer with section titles, text cards, stat reveals, and TikTok-style word-by-word captions synced to narration.

**Estimated time:** 8-12 minutes | **Cost:** $0

### Developer Education

> "Create a 90-second animated explainer about how Git rebase works. Use animated diagrams and comparison cards to show rebase vs merge. Target audience: junior developers."

**What you get:** Technical explainer with comparison cards (rebase vs merge), callout tips, step-by-step animated text, and developer-friendly narration.

**Estimated time:** 10-15 minutes | **Cost:** $0

---

## One-Key Prompts (FAL_KEY only, ~$0.50-$1.50)

Adding `FAL_KEY` to your `.env` unlocks FLUX image generation. These prompts combine AI-generated visuals with Remotion animation.

### Science Explainer

> "Create an animated explainer about how CRISPR gene editing works, with AI-generated visuals of DNA and cell diagrams. Make it 90 seconds, educational but exciting."

**What you get:** Research-backed script, FLUX-generated images with Ken Burns animation, spring-animated transitions, narration, subtitles, and music.

**Estimated time:** 15-20 minutes | **Cost:** ~$0.80

### Product Teaser

> "Make a product launch teaser for a fictional smart water bottle called AquaPulse. 45 seconds, modern and minimal, with AI-generated product shots."

**What you get:** Cinematic product teaser with FLUX-generated visuals, stat reveals (hydration data), comparison cards, and a punchy closing.

**Estimated time:** 12-18 minutes | **Cost:** ~$0.60

### Marketing Explainer

> "Build a 90-second explainer about the psychology of color in marketing. Use AI-generated images showing color associations and include data about color impact on purchasing decisions."

**What you get:** Research-grounded explainer with AI-generated color psychology illustrations, bar charts, pie charts, and narrated insights.

**Estimated time:** 15-20 minutes | **Cost:** ~$1.00

---

## Animation Pipeline — Anime/Ghibli Style (FAL_KEY, ~$0.15)

These use the **Animation pipeline** with `image_animation` approach — FLUX-generated still images brought to life through multi-image crossfade, cinematic camera motion, particle overlays, and ambient music. No video generation APIs needed. Each 30-second video costs ~$0.15.

### Ghibli Fantasy World

> "Create a 30-second Ghibli-style animated video of a magical floating library in the clouds at golden hour. Books drift between shelves, warm light streams through stained glass windows, and a small cat naps on a reading desk."

**What you get:** 6 anime scenes with 12 FLUX-generated images, camera motion (zoom, pan, Ken Burns, drift), sparkle and light-ray particles, cinematic vignette, hero title overlay, and auto-sourced ambient music with energy-optimized offset.

**Estimated time:** 10-15 minutes | **Cost:** ~$0.15

### Underwater Exploration

> "Make a 30-second anime-style animation of an underwater temple with bioluminescent coral, ancient ruins covered in sea moss, luminous jellyfish drifting past stone pillars, and shafts of sunlight piercing the deep blue."

**What you get:** Deep ocean atmosphere with mist and sparkle particles, pan and drift camera motion, blue-green lighting overlays, section title overlays, and oceanic ambient soundtrack.

**Estimated time:** 10-15 minutes | **Cost:** ~$0.15

### Seasonal Journey

> "Create a 30-second Ghibli-style animated video showing the four seasons in a Japanese countryside village — cherry blossoms in spring, fireflies in summer, red maple leaves in autumn, and snow-covered thatched roofs in winter."

**What you get:** 6 scenes transitioning through seasons with petal, firefly, sparkle, and mist particles matching each season. Warm-to-cool lighting transitions and ambient seasonal soundtrack.

**Estimated time:** 10-15 minutes | **Cost:** ~$0.15

### Steampunk Cityscape

> "Make a 30-second anime-style animation of a steampunk city at dusk — airships floating between brass towers, steam rising from street vents, clockwork birds perching on copper lampposts, and a lone inventor walking home through cobblestone streets."

**What you get:** Industrial-fantasy atmosphere with mist and sparkle particles, parallax and zoom camera motion, warm amber lighting overlays, and steampunk-ambient soundtrack.

**Estimated time:** 10-15 minutes | **Cost:** ~$0.15

---

## HyperFrames — HTML/GSAP Motion Graphics (zero-key, ~$0)

These use the HyperFrames composition runtime — HTML + CSS + GSAP rendered deterministically to video via headless Chrome + FFmpeg. Perfect for kinetic typography, product promos, launch reels, and website-to-video treatments where the visual grammar is typographic and motion-first.

**Requirements:** Node.js ≥ 22, FFmpeg, `npx` — no monorepo checkout, the CLI is fetched via `npx @hyperframes/cli` on first run.

### Kinetic Product Launch

> "Make a 20-second product launch video for a new AI coding assistant called 'Cortex'. Big kinetic typography, three feature callouts, a bold accent color, and a final CTA card. Use the HyperFrames runtime."

**What you get:** HTML/GSAP composition with SplitText-style word reveals, staggered feature callouts, accent-driven color accents from a custom playbook, and `hyperframes lint`/`validate` gates passed before render.

**Estimated time:** 3-5 minutes | **Cost:** $0

### Website → Video Teaser

> "Here's my landing page URL: https://example.com. Make me a 15-second social ad for Instagram. Use HyperFrames and pick up the site's real colors and typography."

**What you get:** `website-to-hyperframes` workflow — capture the site, extract colors/typography into a `DESIGN.md`, storyboard 3-4 beats, generate narration, build compositions with GSAP timelines, lint + validate + render.

**Estimated time:** 8-12 minutes | **Cost:** $0 (or ~$0.05 with premium TTS)

### Launch Reel with Registry Blocks

> "Create a 25-second launch reel for a developer tools startup. Include a data chart block (showing user growth from HyperFrames registry), kinetic title cards, and a shader transition between scenes."

**What you get:** `hyperframes add data-chart` + `hyperframes add shader-transition` installed as sub-compositions, wired into index.html, animated with GSAP timelines. Registry blocks are HyperFrames-only; Remotion can't install them.

**Estimated time:** 5-10 minutes | **Cost:** $0

---

## Full Setup Prompts (~$1-$3)

With video generation (Veo, Kling, Runway) + premium TTS (ElevenLabs) + music (Suno). These produce broadcast-quality content.

### Cinematic Trailer

> "Create a cinematic 30-second trailer for a sci-fi concept: humanity receives a warning from 1000 years in the future. Use motion video clips, a cinematic soundtrack, and dramatic title cards."

**What you get:** Veo/Kling-generated motion clips, cinematic title cards with signal texture effects, Hans Zimmer-style soundtrack, and dramatic pacing.

**Estimated time:** 25-40 minutes | **Cost:** ~$2.50

### Animated Explainer (Premium)

> "Make a 90-second animated explainer about quantum computing for middle school students. Use a fun narrator voice, custom soundtrack, and AI-generated visuals of qubits and quantum gates."

**What you get:** Full production: ElevenLabs narration, FLUX visuals, Suno soundtrack, Remotion composition with animated charts and text overlays.

**Estimated time:** 20-30 minutes | **Cost:** ~$2.00

### Avatar Spokesperson

> "Create a 60-second avatar spokesperson video announcing a company rebrand. Professional tone, clean background, with animated text overlays showing the new brand values."

**What you get:** HeyGen avatar video with TTS narration, overlaid section titles, stat reveals, and branded text cards.

**Estimated time:** 15-25 minutes | **Cost:** ~$1.50

---

## For Specific Audiences

### For Teachers

> "Create a 3-minute animated explainer about photosynthesis for 8th graders. Make it fun and visual — use diagrams, charts showing energy conversion, and a friendly narrator voice."

### For Developer Advocates

> "Make a 60-second product demo video for our new REST API. Show the request/response flow with animated diagrams, include latency benchmarks as bar charts, and end with a quick start code snippet."

### For Indie Hackers

> "Create a 30-second Product Hunt launch video for my SaaS tool that helps teams track OKRs. Show 3 key features with animated stat cards and comparison views. Upbeat, modern."

### For Content Creators

> "Take my recent blog post about AI trends in 2026 and turn it into a 90-second video. Research current data to ground it, use animated charts for the statistics, and add a conversational narrator."

---

## Tips for Better Results

**Be specific about visual components.** Instead of "make it look good," say "use bar charts for the comparison, a donut chart for the breakdown, and stat cards for the key numbers."

**Mention your target audience.** "For junior developers" or "for 8th graders" dramatically changes the script, pacing, and visual style.

**Specify duration.** The agent optimizes content density based on your target length. 45 seconds needs ~110 words of narration; 90 seconds needs ~225 words.

**Request specific chart types.** The system has bar charts, line charts, pie/donut charts, KPI grids, progress bars, comparison cards, and callout boxes. Name the ones you want.

**Ask for the zero-key path.** If you want free results, say "use only free tools" or "no paid APIs." The agent will route to Piper TTS, stock media, and Remotion-only compositions.

**For anime/Ghibli-style videos,** mention the style explicitly: "Ghibli-style" or "anime-style." Describe the atmosphere, lighting, and mood. The agent uses the Animation pipeline with FLUX image generation and Remotion's anime scene engine — multi-image crossfade, camera motion, and particle overlays create the illusion of animation from still images. Cost is minimal (~$0.15 for 30 seconds).

---

## Contributing Prompts

Found a prompt that produces great results? Share it:

1. Open a [GitHub Discussion](../../discussions) in the "Prompt Exchange" category
2. Include: your prompt, a screenshot or description of the output, cost, and which providers you used
3. The best prompts get added to this gallery with credit

---

*This gallery is community-maintained. All prompts have been tested and produce complete videos.*
