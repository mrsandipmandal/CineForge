# Universal Interactive Production Wizard

The Production Wizard provides a conversational, progressive intake experience that adapts to user expertise, extracts existing context, and guides production choices safely.

## 1. Operating Modes

The Wizard adapts its question depth based on user mode:

- **Quick**: Asks only essential unresolved questions. Defaults safe, balanced options for standard production.
- **Guided (Default)**: Offers useful selections with concise explanations and tradeoffs for each option.
- **Advanced**: Exposes provider, model, render runtime, enhancement profiles, and budget cap choices.
- **Expert**: Exposes deep technical levers: CRF, bitrates, sampling rates, custom FFmpeg filter chains, PBR material tiers, and seed controls.

All modes preserve human approval gates and budget governance.

---

## 2. Progressive Intake Principle

**Extract before asking.** Before asking any question, extract answers already present in:
1. User prompt (e.g., "Make a 60-second explainer" -> duration is already known).
2. Previous answers in conversation history.
3. Existing project configuration or checkpoint state.
4. Source media metadata (e.g., probe duration, resolution, audio presence).
5. Reference video analysis (if provided).

Never ask duplicate questions.

---

## 3. Mandatory Duration Selection

If duration is NOT specified in the user prompt, you MUST present the following exact options:

```text
1. 15–30 seconds
2. 30–60 seconds
3. 1–3 minutes
4. 3–5 minutes
5. 5–10 minutes
6. Custom
7. Skip — Let AI Decide
```

- **Custom**: Prompt for specific target duration (e.g. "45 seconds", "2.5 minutes"). Validate > 0 and reasonable bounds.
- **Skip — Let AI Decide**: The AI makes a reasoned selection based on narrative scope, platform, and available capabilities.

---

## 4. Other Progressive Decision Categories

Present relevant choices only when unresolved:

1. **Production Purpose**:
   - Documentary, Short film, Advertisement, Educational, Science, History, Storytelling, Talking-head, Explainer, Music video, Cinematic sequence, Custom, Skip — Let AI Decide.

2. **Language**:
   - Independent options for Narration, Dialogue, Subtitles/Captions, On-screen text.

3. **Aspect Ratio**:
   - 16:9 (Landscape HD/4K), 9:16 (Vertical Reels/Shorts/TikTok), 1:1 (Square), 4:5 (Portrait Feed), 21:9 (Cinematic), Custom, Skip — Let AI Decide.

4. **Visual Style**:
   - Photorealistic 3D, Hollywood cinematic, Documentary realism, Historical reconstruction, Stylized 3D, 2D animation, Motion graphics, Anime, Science visualization, Sci-fi, Hybrid AI + procedural 3D, Custom, Skip — Let AI Decide.

5. **Production Strategy**:
   - Local only, Cloud API, Hybrid, AI + procedural rendering, Stock + AI, User-supplied assets, Skip — Let AI Decide.

6. **Rendering Backends**:
   - Discovered from preflight: Remotion, HyperFrames, FFmpeg, Blender, Three.js, Manim.
   - Always present both Remotion and HyperFrames when both are installed.

7. **Voice & Audio**:
   - Local TTS (Piper), Cloud TTS (ElevenLabs, Azure, Google, Fish Audio), Voice identity clone (with consent), User audio, BGM track, SFX, No narration.

8. **Enhancement (Video Quality & AI Human)**:
   - Video Quality Enhancer (Auto, Gentle, Balanced, Cinematic, Maximum, Custom, Disabled).
   - AI Human Enhancer (Auto, Natural, Cinematic, Face Restoration, Detail Recovery, Eye Detail, Custom, Disabled, Not Applicable).

9. **Quality Floor**:
   - Preview, Standard, Professional 1080p, Cinematic 1080p, 4K (when supported), Skip — Let AI Decide.

10. **Budget**:
    - Free / ₹0 (Local-only), Limited budget (with cap), Custom budget, Approved paid path.

---

## 5. "Skip — Let AI Decide" Semantics (Binding)

`Skip — Let AI Decide` does NOT mean ignoring the setting or disabling it. It requires the AI to make a reasoned, auditable choice.

### Audit Record Requirements:
Every AI decision must record:
- `selection_mode`: `"ai_decided"`
- `selected_value`: The concrete chosen option (e.g. `"1–3 minutes"`)
- `decision_reason`: Specific rationale tied to prompt intent, platform, or capability
- `constraints_considered`: List of factors (e.g. `["user_prompt_intent", "platform_youtube"]`)
- `confidence`: Numeric score between 0.0 and 1.0

### Distinct Selection States:
- `user_selected`: Explicitly chosen by user.
- `ai_decided`: Reasoned choice made by agent upon Skip or missing input.
- `not_applicable`: Subject/capability does not apply to this production (e.g. Human Enhancer on landscape with no people).
- `disabled`: User explicitly turned off the feature.
- `unavailable`: Tool/model not installed or configured on this machine.
- `pending_user_input`: Awaiting user response.

### Payment Safety Rule:
**"Skip — Let AI Decide" MUST NEVER silently authorize paid operations.**
If an AI decision recommends a paid provider or tool, it must be presented in the proposal packet and require explicit user approval. Unknown costs must remain marked unknown.

---

## 6. Decision Log Append-Only Contract

All production choices made through the wizard MUST be recorded into `decision_log`.
- `decision_log` is an append-only audit trail.
- Never overwrite or delete prior decision entries.
- If a decision is revised (e.g. user changes voice or runtime), append a new entry reusing the same `(category, subject)` pair.
