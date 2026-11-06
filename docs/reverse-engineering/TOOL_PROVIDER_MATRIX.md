# OpenMontage Matrix — Tool & Provider Capability Matrix

**Date:** 2026-11-06  
**Audited Tool Count:** 155 tools across 26 capabilities  
**Source of Truth:** Live `ToolRegistry` reflection + Codebase Inspection  

---

## 1. Voice & TTS Capability Matrix

| Provider | Tool Name | Bengali (bn-IN) TTS | Hindi (hi-IN) TTS | Voice Cloning | Enrollment Required | Runtime | Estimated Cost | License / Terms |
|---|---|---|---|---|---|---|---|---|
| **ElevenLabs** | `elevenlabs_tts` | Yes (`eleven_multilingual_v2`, `eleven_turbo_v2_5`) | Yes | Yes (Instant Voice Clone via sample audio; Professional Voice Clone via API) | Optional (Instant needs 1-3 samples; PVC requires consent audio) | API | Paid (~$0.15-$0.30 / 1k chars) | Commercial Proprietary |
| **Fish Audio** | `fish_audio_tts` | Yes (Multilingual S1/S2/S2.1) | Yes | Yes (Zero-shot reference audio clone via `reference_id` or uploaded sample) | No (Direct reference audio supported) | API / Self-hosted | Low cost API / Free self-hosted | Apache-2.0 / Commercial API |
| **Azure Speech** | `azure_tts` | Yes (`bn-IN-BashkarNeural`, `bn-IN-TanishaaNeural`) | Yes (`hi-IN-MadhurNeural`, `hi-IN-SwaraNeural`) | Custom Neural Voice only (Enterprise approval required) | Yes (Explicit consent recording + Microsoft gating) | API | ~$0.016 / 1k chars (Pay-as-you-go) | Commercial Proprietary |
| **Google Cloud** | `google_tts` | Yes (`bn-IN-Standard`, `bn-IN-Wavenet`, `bn-IN-Neural2`) | Yes (`hi-IN-Neural2`, `hi-IN-Wavenet`, `hi-IN-Standard`) | No (Custom Voice enterprise only) | N/A | API | Free tier (4M chars), then ~$0.016 / 1k chars | Commercial Proprietary |
| **OpenAI** | `openai_tts` | Limited (Multilingual model speaks Bengali phonetically with accent) | Yes | No (Preset voices only: alloy, echo, fable, onyx, nova, shimmer) | N/A | API | ~$0.015 / 1k chars | Commercial Proprietary |
| **Piper TTS** | `piper_tts` | Experimental (limited community checkpoints) | Yes (Indic community checkpoints available) | No (Pre-trained ONNX voices only) | N/A | Local (CPU) | Free (Zero cost, offline) | MIT / Open Source |
| **F5-TTS / IndicF5** | `f5_tts` / Local | Yes (IndicF5 / multilingual F5 supports bn-IN) | Yes | Yes (Zero-shot voice cloning with 5-10s reference audio) | No | Local GPU | Free (Compute only) | MIT / Open Source |
| **Coqui XTTS-v2** | `xtts_tts` / Local | Experimental / Phonetic | Yes (17 languages native, Hindi supported) | Yes (Zero-shot reference cloning with 3-10s audio) | No | Local GPU | Free (Compute only) | Coqui CPML (Non-commercial / Commercial license) |
| **Doubao Speech** | `doubao_tts` | No | No | Voice clone via Volcengine console | Console required | API | Paid | Commercial Proprietary |
| **Kling TTS** | `kling_tts` | No | No | Kling voice catalog only | No | API | Paid | Commercial Proprietary |
| **Cartesia** | `cartesia_tts` | No | Yes | Voice clone via Cartesia API | Yes | API | Paid | Commercial Proprietary |

> [!IMPORTANT]
> **Distinction Between TTS and Voice Cloning:** Ordinary TTS converts text to speech using pre-trained catalog voices. Voice cloning conditions acoustic generation on private reference audio to reproduce a specific human speaker's vocal timbre, cadence, and identity. A model supporting Bengali text does NOT automatically support Bengali voice cloning.

---

## 2. Face, Avatar & Character Identity Matrix

| Operation | Tool Name | Provider / Engine | Input Assets | Output Artifact | Consistency Mechanism | Status |
|---|---|---|---|---|---|---|
| **Talking Head** | `talking_head` | SadTalker / MuseTalk | 1 Front Portrait + Audio WAV | Head-animated MP4 | 2D Landmark warping & 3DMM morphing | Available (Local GPU) |
| **Lip Sync** | `lip_sync` | Wav2Lip | Existing Video MP4 + Audio WAV | Re-synced MP4 | Mouth region GAN replacement | Available (Local) |
| **Cloud Lip Sync** | `kling_lip_sync` | Kling Official API | Existing Video MP4 + Audio | Re-synced MP4 | Kling neural lip-sync engine | Available (API) |
| **Cloud Avatar** | `kling_avatar` | Kling Official API | Reference Image + Script/Audio | Video MP4 | Kling digital human synthesis | Available (API) |
| **Cloud Avatar** | `heygen_avatar` | HeyGen API | Avatar Look ID + Script/Audio | Video MP4 | HeyGen interactive digital twin | Available (API) |
| **Face Restoration** | `face_restore` | CodeFormer / GFPGAN | Degraded or blurry face image | Enhanced face PNG | Codebook lookup & generative facial prior | Available (Local GPU) |
| **Face Enhancement** | `face_enhance` | InsightFace / Real-ESRGAN | Face image | Upscaled & sharpened PNG | Feature enhancement pipeline | Available (Local GPU) |
| **Character Consistency** | Provider adapters | Seedance 2.0, Kling, Higgsfield | Reference Images (front, side, expressions) | Scene Video MP4 | Multi-image reference conditioning / Soul ID | Integrated in asset pipeline |
| **Authorized Replacement** | `faceswap` | InsightFace / Inswapper | Source face PNG + Target video MP4 | Replaced video MP4 | Latent identity embedding transfer | Controlled / Consent-gated |

---

## 3. Video Generation Matrix

| Tool Name | Provider | Runtime | Input Modality | Reference Conditioning | Best For |
|---|---|---|---|---|---|
| `seedance_video` / `seedance_ark` | Volcengine / fal.ai | API | Text / Image-to-Video | Yes (Image anchors & motion reference) | Premium cinematic shots, dynamic action |
| `kling_video` / `kling_official_video` | Kling AI | API | Text / Image-to-Video | Yes (Character/element references) | High-fidelity motion, complex physical interaction |
| `minimax_video` | MiniMax Hailuo | API | Text / Image-to-Video | Yes (First/Last frame control) | Realistic human movement, 2K outputs |
| `veo_video` | Google Veo / Vertex | API | Text / Image-to-Video | Yes (Visual reference prompts) | Photorealistic textures, complex camera motion |
| `wan_video` / `wan_engine` | Wan 2.1 / Wan 2.2 | Local GPU / Replicate | Text / Image-to-Video | Yes (Image conditioning) | Open-weights production, zero API cost |
| `hunyuan_cloud_video` | Tencent Hunyuan | API | Text / Image-to-Video | Yes | Stylized cinematic and Chinese cultural visuals |
| `runway_video` | Runway Gen-4 | API | Text / Image-to-Video | Yes (Director mode, camera control) | Precision camera choreography |
| `comfyui_video` | ComfyUI Local Server | Local GPU / Server | Node graph workflow | Full (ControlNet, IP-Adapter, LoRAs) | Maximum local customization and exact identity control |

---

## 4. Composition Runtimes

| Runtime | Engine | Best For | Hardware / Software Prerequisites |
|---|---|---|---|
| **FFmpeg** | `video_compose` (FFmpeg) | Direct cuts, audio mix, subtitles, Ken Burns pan & zoom | `ffmpeg` binary on PATH |
| **Remotion** | `video_compose` (Remotion) | Kinetic typography, React stat cards, spring physics, word captions | Node.js, `remotion-composer/`, `npm install` |
| **HyperFrames** | `hyperframes_compose` | HTML/CSS/GSAP composition, web UI walkthroughs, 3D Three.js worlds | Node.js ≥ 22, `npx hyperframes` |
