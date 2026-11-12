---
name: bengali-science-explainer
description: >
  Interactive, multi-language Science Mystery Shorts production skill for CineForge.
  Dynamically selects language, researches trending science topics, presents
  AI-curated subject options, walks through feature selection with the user,
  shows a full production plan, waits for approval, then auto-produces the video.
  Communicates in the user's chosen language throughout.
triggers:
  - "science video"
  - "বিজ্ঞান ভিডিও"
  - "science short"
  - "mystery video"
  - "explainer video"
  - "/science-explainer"
pipeline: animated-explainer
---

# Science Explainer Shorts — Interactive Production Skill

This skill drives a **fully interactive** production session. It:
1. Asks the user for their preferred language (dynamic — not hardcoded).
2. Runs silent web research to find fresh, shareable science topics.
3. Presents AI-curated subject options with hooks.
4. Walks through every production feature one by one.
5. Builds and shows a complete production plan.
6. Waits for explicit user approval.
7. Then auto-produces the full video with no further interruptions.

**All user communication is in the language the user selects.**

---

## PRE-FLIGHT (Always Silent — Read This First)

Before talking to the user, do all of the following silently:

### 1. Read AGENT_GUIDE.md
```
f:\CineForge\AGENT_GUIDE.md
```

### 2. Read pipeline manifest
```
f:\CineForge\pipeline_defs\animated-explainer.yaml
```

### 3. Discover available tools
```python
from tools.tool_registry import registry
registry.discover()
```

Do NOT call `provider_menu_summary()` — it crashes on this machine (f5_tts torch bug).
Instead, check individual tools silently:

```python
# Check TTS options
import subprocess, shutil

tts_options = {}

# edge_tts — always available, free, multi-language
try:
    import edge_tts
    tts_options["edge_tts"] = True
except ImportError:
    tts_options["edge_tts"] = False

# ElevenLabs
import os
tts_options["elevenlabs"] = bool(os.environ.get("ELEVENLABS_API_KEY"))

# Google TTS
tts_options["google_tts"] = bool(os.environ.get("GOOGLE_API_KEY"))

# Check image generation
img_options = {
    "google_imagen": bool(os.environ.get("GOOGLE_API_KEY")),
    "image_subagent": True,  # always available via image-generator subagent
}

# Check composition
comp_options = {
    "ffmpeg": bool(shutil.which("ffmpeg")),
    "remotion": False,  # check below
}
try:
    result = subprocess.run(["npx", "--yes", "remotion", "--version"],
                            capture_output=True, timeout=10)
    comp_options["remotion"] = result.returncode == 0
except Exception:
    pass
```

Determine the best available path. The **default fallback stack** (always works, $0.00):
- TTS → `edge_tts`
- Image → `image-generator` subagent
- Compose → FFmpeg
- Ambient → `templates/ambient_synthesis.py`

---

## PHASE 1 — LANGUAGE SELECTION

**This is your FIRST message to the user.** Keep it short and friendly.

```
👋 Welcome to the Science Mystery Shorts creator!

Before we begin — what language do you want your video in?

  1. 🇬🇧 English
  2. 🇧🇩 Bengali (বাংলা)
  3. 🇮🇳 Hindi (हिन्दी)
  4. 🇸🇦 Arabic (العربية)
  5. 🇪🇸 Spanish (Español)
  6. 🇫🇷 French (Français)
  7. 🇩🇪 German (Deutsch)
  8. 🇯🇵 Japanese (日本語)
  9. Something else — just type it!

(This sets the narration voice, subtitles, AND how I'll talk to you.)
```

**Wait for user reply. Record:**
- `selected_language_name` (e.g., "Bengali")
- `selected_language_code` (e.g., "bn")
- `communication_language` = same as selected (switch all future messages to this language)

### Edge_TTS Voice Mapping

| Language | edge_tts Voice | Rate | Pitch |
|----------|---------------|------|-------|
| English | `en-US-JennyNeural` | `-2%` | `0Hz` |
| Bengali | `bn-IN-BashkarNeural` | `-3%` | `-2Hz` |
| Hindi | `hi-IN-NeerjaNeural` | `-2%` | `0Hz` |
| Arabic | `ar-EG-SalmaNeural` | `-2%` | `0Hz` |
| Spanish | `es-ES-ElviraNeural` | `-2%` | `0Hz` |
| French | `fr-FR-DeniseNeural` | `-2%` | `0Hz` |
| German | `de-DE-KatjaNeural` | `-2%` | `0Hz` |
| Japanese | `ja-JP-NanamiNeural` | `-3%` | `0Hz` |
| Other | `en-US-JennyNeural` | `-2%` | `0Hz` (fallback) |

If the user picks a language not in this table: use `search_web` to find the best `edge_tts` voice for that language, verify it exists, then proceed.

---

## PHASE 2 — SILENT RESEARCH (Do this while composing the next message)

Before showing topic options, run silent web research. This makes suggestions **specific, fresh, and shareable** — not generic.

### 2a. Research Trending Science Mysteries

Use `search_web` with queries like:
- `"most surprising science discovery 2025 2026 short video"`
- `"weird animal superpower viral science fact"`
- `"incredible ocean creature ability science explained"`
- `"strange physics phenomenon mind-blowing explained"`
- `"[selected_language] science mystery popular youtube shorts topic`

Collect 10–15 candidate facts. For each, note:
- **Subject** (e.g., "Mantis Shrimp")
- **Surprising hook** (e.g., "sees 16 colors, humans see 3")
- **Why shareable** (counter-intuitive, relatable, visual)
- **Visual potential** (can we make stunning images?)
- **Estimated viewer hook-strength** (1–5)

### 2b. Score and Rank

Score each candidate:
- Surprise factor (1–5)
- Visual potential (1–5)
- Relatability (1–5)
- Hook clarity (1–5)

Pick **top 6** by total score.

---

## PHASE 3 — SUBJECT SELECTION (In user's chosen language)

Present the top 6 research-backed suggestions. Example format (adapt to chosen language):

```
🔬 I researched 15 science mysteries — here are the top 6, ranked by wow-factor:

  1. 🦐 Mantis Shrimp Vision       — Sees 16 colors. Humans see 3. How?
  2. 🌊 Barreleye Fish             — Transparent head. Eyes that look UP through its skull.
  3. ⚡ Electric Eel               — 860 volts. Can remote-control other fish's muscles.
  4. 🌿 Pitcher Plant              — Digests insects ALIVE in 10 seconds.
  5. 🧊 Tardigrade                 — Survives in space, boiling water, and radiation.
  6. 🌀 Fibonacci in Sunflowers    — Why every sunflower follows the same math.

  💡 Or type your own topic!

Which interests you most? (Type a number, or describe your own idea)
```

**Wait for reply.** Record `selected_subject`.

---

## PHASE 4 — FEATURE SELECTION (Interactive, one block at a time)

After subject is chosen, walk through feature choices. Present ALL features in ONE message — not one at a time (less friction). Group them clearly.

```
🎬 Great choice! Now let's configure your video.
   Answer each question — or just say "default" to use my recommendation.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📐 VIDEO FORMAT
   A) Vertical Short  — 1080×1920  (YouTube Shorts, Reels, TikTok) ⭐ Recommended
   B) Landscape      — 1920×1080  (YouTube standard, blog embed)
   C) Square         — 1080×1080  (Instagram feed)

🎭 VISUAL STYLE
   A) Cinematic CGI        — Photorealistic 3D renders, dramatic lighting ⭐
   B) Documentary          — Real-world photography style, natural tones
   C) Illustrated / Flat   — Bold colors, stylized illustration
   D) Dark Dramatic        — High-contrast, moody, noir science

🎙️ NARRATOR TONE
   A) Curious & Exciting    — "Wait until you see THIS..." ⭐
   B) Calm & Educational    — Measured, BBC-documentary style
   C) Fast & Punchy         — Social-first, dopamine hooks every 3s

⏱️ VIDEO LENGTH
   A) ~60 seconds   — 5 scenes, standard Short ⭐
   B) ~90 seconds   — 7 scenes, deeper dive
   C) ~45 seconds   — 4 scenes, ultra-fast

🎵 BACKGROUND AUDIO
   A) Ocean / Nature ambient   — Synthesized via FFmpeg (free) ⭐
   B) Silence                  — Narration only, no background
   C) Your own track           — Drop an MP3 in music_library/ and tell me the filename

📝 SUBTITLE STYLE
   A) Bold white + black outline, bottom-center ⭐
   B) Colored highlight (yellow or cyan)
   C) No subtitles
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Type your choices (e.g.: "A, A, A, A, A, A") — or just "all default" to use ⭐ options.
```

**Wait for reply.** Parse choices and record all feature settings.

If user says "all default" or "default": use all ⭐ recommended options silently.

---

## PHASE 5 — BUILD PRODUCTION PLAN (Silently compute, then show)

After features are locked, silently compute:
- Project slug (kebab-case from subject name)
- 5 scene names and rough narration direction
- Asset list
- Render path
- Estimated production time

Then show the complete plan in the user's language:

```
📋 YOUR PRODUCTION PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 VIDEO:   "[Subject Title]"
🌐 LANGUAGE: [Language]
📐 FORMAT:  [Format] | [Duration]
🎭 STYLE:   [Visual Style]

🎬 SCENE BREAKDOWN:
  Scene 1 — Hook (0–13s)
    "[Shocking opening statement about the subject]"
    Visual: [Image description]

  Scene 2 — The Science (13–26s)
    "[How it actually works]"
    Visual: [Image description]

  Scene 3 — Deep Dive (26–39s)
    "[Most surprising detail / comparison]"
    Visual: [Image description]

  Scene 4 — Twist / Wow (39–52s)
    "[The counter-intuitive fact that blows minds]"
    Visual: [Image description]

  Scene 5 — Outro / CTA (52–65s)
    "[Closing + engagement prompt]"
    Visual: [Image description]

🛠️ PRODUCTION STEPS I WILL TAKE:
  ① Research validation & script writing          ~2 min
  ② Generate 5 scene images (AI image generator)  ~5 min
  ③ Record [Language] narration (edge_tts)         ~1 min
  ④ Synthesize ambient audio (FFmpeg)              ~30 sec
  ⑤ Generate subtitles (.ASS format)              ~30 sec
  ⑥ Compose & render final video (FFmpeg)         ~3 min
                                        Total:    ~12 min

🎙️ VOICE:   [edge_tts voice name]
🖼️ IMAGES:  AI image generator (free)
🎵 AUDIO:   [chosen audio option]
💰 COST:    $0.00 (all free tools)

📁 OUTPUT:  projects/[slug]/renders/final.mp4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Approve this plan to start production? (yes / change something)
```

**Write checkpoint: `awaiting_human`**
**END YOUR TURN.** Wait for user reply.

---

## PHASE 6 — APPROVAL HANDLING

### If user says YES / approves:
- Write checkpoint: `completed` (human_approved=True)
- Immediately say: `"🎬 Perfect! Starting production now — I'll update you at each stage."`
- Proceed to PHASE 7 without further questions.

### If user says "change X":
- Address only the specific change they mention.
- Re-show the updated plan section only (not the full plan again).
- Ask: `"Updated. Ready to go now?"`
- Wait for final approval.

---

## PHASE 7 — PRODUCTION (Mostly Auto — Minimal User Interruption)

### 7a. Project Init (silent)
```python
from lib.checkpoint import init_project
init_project('{slug}', title='{Title}', pipeline_type='animated-explainer')
```
Open Backlot: `python -m backlot open {slug}` (if fails, continue — board is non-blocking)

### 7b. Research Stage (silent)
Read: `skills/pipelines/animated-explainer/research-director.md`

Deepen research on the chosen subject. Collect:
- 8–10 specific facts with sources
- Key scientific terms (translated to chosen language)
- 2–3 analogies / comparisons for relatability
- Visual references for each scene

Write `artifacts/research_brief.json`, validate, checkpoint `completed`.

Narrate progress to user:
```
🔬 [Step 1/6] Research done — found [N] verified facts about [subject].
```

### 7c. Script Stage (silent)
Read: `skills/pipelines/animated-explainer/script-director.md`

Write full narration script in the **selected language**. Rules:
- Scene 1 (Hook): Start with a question or shocking statement. Max 2 sentences.
- Scenes 2–4: One key concept each. 3–4 sentences. No jargon without explanation.
- Scene 5 (Outro): Call-to-action + comment bait. 1–2 sentences.
- Each scene narration: **35–50 words** (edge_tts at adjusted rate → ~11–14 seconds)
- **Breathing gap:** 0.6s silence appended to each clip

Validate script timing: total should be 60–75 seconds.

Write `artifacts/script.json`, validate schema, checkpoint `completed`.

Narrate progress:
```
📝 [Step 2/6] Script written — [N] words total, estimated [X]s runtime.
```

### 7d. Scene Plan Stage (silent)
Read: `skills/pipelines/animated-explainer/scene-plan-director.md`

For each scene write an **English** image prompt (even if video language is non-English):

**Image Prompt Formula:**
```
Ultra-photorealistic 9:16 vertical cinematic frame, [subject detail] in [environment],
[lighting conditions], [camera angle: macro/wide/overhead/POV],
[color palette], dramatic depth of field, 8K resolution,
no text, no watermark, no logos, award-winning wildlife/science photography
```

Adapt formula per chosen visual style:
- **Cinematic CGI**: add `"photorealistic 3D render, volumetric lighting, subsurface scattering"`
- **Documentary**: add `"National Geographic style, natural lighting, shallow depth of field"`
- **Illustrated**: add `"bold flat illustration, Kurzgesagt-inspired, clean vector art"`
- **Dark Dramatic**: add `"noir lighting, dramatic shadows, deep blacks, single key light"`

Write `artifacts/scene_plan.json`, validate, checkpoint `completed`.

Narrate progress:
```
🎨 [Step 3/6] Scene plan ready — generating 5 images now.
```

### 7e. Assets Stage (parallel where possible)

**7e-i. Images** — `image-generator` subagent

For each of 5 scenes:
- Send prompt to `image-generator` subagent
- Target size: 1080×1920 (or closest available, then resize with FFmpeg)
- Save as: `projects/{slug}/assets/images/scene_{i}_{name}.png`

**FFmpeg resize if needed:**
```bash
ffmpeg -y -i input.jpg -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" scene_1_name.png
```

Report as each image lands:
```
  🖼️ Scene [N]/5 image — done
```

**7e-ii. TTS Narration** — `edge_tts`

For each scene:
```python
import asyncio, edge_tts

async def tts(text, voice, rate, pitch, out_path):
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await comm.save(out_path)

asyncio.run(tts(narration, "{voice}", "{rate}", "{pitch}",
                f"projects/{slug}/assets/audio/scene_{i}_narration.mp3"))
```

**7e-iii. Ambient Audio** — FFmpeg (if chosen)
```bash
python .agents/skills/bengali-science-explainer/templates/ambient_synthesis.py \
    projects/{slug}/assets/audio/full_ambient.mp3 80
```

For non-ocean ambient themes, adjust the FFmpeg synthesis:
- **Ocean/Nature**: brown noise + sine 40Hz + sine 8kHz (see ambient_synthesis.py)
- **Space**: white noise very low + sine 80Hz fade
- **Forest**: brown noise + birds (sine 2kHz pulsed)
- **Lab/Tech**: pink noise + subtle hum 60Hz

**7e-iv. Subtitles** — ASS format

Parse each narration for sentence breaks. Write `.ass` file:
```
[Script Info]
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, Bold, Alignment, MarginL, MarginR, MarginV, Outline, Shadow
Style: Default,{font_name},56,&H00FFFFFF,&H00000000,-1,2,80,80,170,2,1
```

Font selection per language:
| Language | Font Name |
|----------|-----------|
| Bengali | `Nirmala UI` |
| Hindi | `Nirmala UI` |
| Arabic | `Arial Unicode MS` |
| Japanese | `Yu Gothic` |
| Other | `Arial Bold` |

Write `projects/{slug}/assets/subtitles.ass`

**Once ALL assets done** — narrate:
```
✅ [Step 4/6] All assets ready:
   • 5/5 images generated
   • 5/5 narrations recorded ([X]s total)
   • Ambient audio synthesized
   • Subtitles written ([N] lines)

🎬 Composing final video now...
```

Write `artifacts/asset_manifest.json`, validate, checkpoint `completed` (human_approved=True — pre-authorized by plan approval).

### 7f. Edit Stage (silent)
Read: `skills/pipelines/animated-explainer/edit-director.md`

Write `artifacts/edit_decisions.json`:
```json
{
  "render_runtime": "ffmpeg",
  "composition_mode": "templated",
  "scenes": [
    {
      "index": 1,
      "image": "assets/images/scene_1_{name}.png",
      "audio": "assets/audio/scene_1_narration.mp3",
      "duration": "{measured_duration + 0.6}"
    }
  ],
  "subtitles": {
    "style": "sentence",
    "file": "assets/subtitles.ass",
    "font": "{font_name}",
    "size": 56
  },
  "music": {
    "source": "{chosen_audio_option}",
    "ambient_level": 0.15,
    "file": "assets/audio/full_ambient.mp3"
  },
  "transitions": "cut",
  "output_resolution": "{chosen_format_wh}",
  "output_fps": 30
}
```

Checkpoint `completed`.
Narrate: `⚙️ [Step 5/6] Edit decisions finalized — rendering now...`

### 7g. Compose Stage (silent)
Read: `skills/pipelines/animated-explainer/compose-director.md`

```bash
python .agents/skills/bengali-science-explainer/templates/render_final.py \
    "f:\CineForge\projects\{slug}" 5 "f:\CineForge\projects\{slug}\renders\final.mp4"
```

**Zoompan per scene:**
```
zoompan=z='min(zoom+0.0005,1.18)':x='iw/2-(iw/zoom/2)':y='ih*0.30-(ih/zoom*0.30)':d={frames}:s={width}x{height}:fps=30
```
Where `{frames} = int((scene_duration) * 30)`

**Verify output:**
```bash
ffprobe -v quiet -print_format json -show_streams "projects/{slug}/renders/final.mp4"
```
Check: duration ≥ 55s, codec=h264, resolution matches chosen format.

Write `artifacts/render_report.json`, checkpoint `completed`.

---

## PHASE 8 — FINAL DELIVERY

Show in user's chosen language:

```
🎉 YOUR VIDEO IS READY!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📹 File:        projects/{slug}/renders/final.mp4
⏱️  Duration:    {X} seconds
📐 Resolution:  {format}
🌐 Language:    {language}
🎙️  Voice:       {voice_name}
💰 Total cost:  $0.00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 SCENE SUMMARY:
  1. {scene_1_name}  — {one-line description}
  2. {scene_2_name}  — {one-line description}
  3. {scene_3_name}  — {one-line description}
  4. {scene_4_name}  — {one-line description}
  5. {scene_5_name}  — {one-line description}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Backlot board: http://127.0.0.1:4750/p/{slug}

✨ Want another video? Just say the word!
   (Try a different language, style, or topic)
```

Write `artifacts/final_review.json`, checkpoint `completed`.

---

## PRODUCTION PARAMETERS REFERENCE

| Parameter | Default | Options |
|-----------|---------|---------|
| Format | 1080×1920 | 1920×1080, 1080×1080 |
| FPS | 30 | — |
| Scenes | 5 | 4 (45s), 5 (60s), 7 (90s) |
| Scene duration | ~13s | auto from TTS |
| Breathing gap | 0.6s | — |
| Zoompan max | 1.18x | — |
| Video codec | libx264 | — |
| CRF | 18 | — |
| Preset | medium | — |
| Audio codec | aac 192k | — |
| Ambient vol | 0.15 | — |

---

## CHECKPOINT SYSTEM

```python
from lib.checkpoint import write_checkpoint, validate_artifact

# Stage entry
write_checkpoint(slug, "research", "in_progress", {}, metadata={})

# Stage complete
validate_artifact("research_brief", artifact_data)
write_checkpoint(slug, "research", "completed", artifact_data)

# Awaiting human (proposal, assets)
write_checkpoint(slug, "proposal", "awaiting_human", artifact_data)
# → END TURN → wait for user → on approval:
write_checkpoint(slug, "proposal", "completed", artifact_data, human_approved=True)
```

**Gate policy:**
- `proposal` → awaiting_human (Phase 5)
- `script` → auto-proceed (pre-authorized by plan approval)
- `scene_plan` → auto-proceed
- `assets` → auto-proceed (pre-authorized)
- `edit` → auto-proceed
- `compose` → auto-proceed

Only ONE human gate in Phase 5. All subsequent stages auto-proceed unless the user changes their mind.

---

## ERROR RECOVERY (In User's Language)

When something fails, immediately surface:

```
⚠️ Hit a snag!

What I tried:    [action]
What failed:     [error message, simplified]
Type of issue:   [quota / auth / tool unavailable / quality]

My options:
  A) [Alternative path — e.g., use different image tool]
  B) [Skip & continue — e.g., use placeholder image]
  C) [Retry — e.g., try again with simplified prompt]

My recommendation: [A/B/C] because [reason]

Which do you prefer?
```

**Common failures & fallbacks:**

| Failure | Auto-fallback | User notification |
|---------|--------------|-------------------|
| `google_imagen` 429 | `image-generator` subagent | None (silent) |
| `edge_tts` voice not found | `en-US-JennyNeural` | Yes — confirm |
| FFmpeg missing | Cannot compose — block | Yes — escalate |
| Image wrong resolution | FFmpeg scale+crop | None (silent) |
| Ambient synthesis fails | Silence (no ambient) | None (silent) |

---

## PROGRESS NARRATION TEMPLATE

After plan approval, narrate like a human project manager:

```
🎬 Starting production...

🔬 [Step 1/6] Research & Script       ← when starting research
📝 Script ready — [N] words, ~[X]s estimated
🎨 [Step 2/6] Generating images...
  🖼️ Scene 1/5 — done
  🖼️ Scene 2/5 — done
  ...
🎙️ [Step 3/6] Recording narration...
🎵 [Step 4/6] Synthesizing audio...
📝 [Step 5/6] Writing subtitles...
⚙️ [Step 6/6] Composing final video...
🎉 Done! Your video is ready.
```

Keep these updates SHORT — one line each. No walls of text mid-production.

---

## KEY RULES

1. **Dynamic language** — never hardcode. Always ask first, then use throughout.
2. **Research before suggestions** — topic ideas come from real web research, not a fixed list.
3. **One approval gate** — at the production plan stage. After that, auto-proceed.
4. **Progress updates** — brief, one-line updates only during production.
5. **Error transparency** — always tell the user what failed and ask which path to take.
6. **Pipeline governance** — every stage writes CineForge checkpoints + validated artifacts.
7. **Layer 3 skills** — read the relevant `.agents/skills/` skill before calling any generation tool.
8. **Communication language = selected language** — switch immediately after language choice and never go back.
