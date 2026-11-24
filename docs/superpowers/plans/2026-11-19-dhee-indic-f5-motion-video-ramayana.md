# Dhee-Indic-F5 Local Voice Cloning & Multi-Frame Motion Video Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement local zero-shot Bengali voice cloning using `dheeyantra/dhee-indic-f5` with Sandip's voice profile (`sample-files/voices/sandip/samples/Bng_sample.mp3`), and engineer a multi-frame cinematic motion video engine (replacing static Ken Burns zoom-in/out with 2.5D depth parallax, animated character dynamics, and particle physics) to produce 100% YouTube monetization-compliant Ramayana Shorts.

**Architecture:** A local modular pipeline integrating PyTorch/Transformers zero-shot TTS (`DheeIndicF5TTS`) using Sandip's reference audio and verbatim transcript (`"নমস্কার আমি সন্দীপ অডিওতে বলা কথাটি লিখলে ক্লোনিং নিখুঁত হয়"`), combined with an automated broadcast audio mastering chain (EBU R128 -14 LUFS, 75Hz high-pass, warmth EQ). Visuals are elevated from static image pans to a multi-layered 2.5D motion engine in Remotion with procedural particle dynamics and animated character layers.

**Tech Stack:** Python 3.11, PyTorch (CUDA 12.4 / FP16), HuggingFace Transformers (`dheeyantra/dhee-indic-f5`), SoundFile, FFmpeg / FFprobe, Remotion 4.0, TypeScript / React, EBU R128 Audio Normalizer.

**Spec:** User directive for YouTube-monetizable Ramayana series featuring Sandip's authentic human voice profile and real multi-frame video motion instead of basic zoom-in/out.

## Global Constraints

- Hardware target: NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM / 4096 MiB) with strict memory guard (<3.2 GB peak VRAM, FP16, `torch.cuda.empty_cache()`, CPU fallback).
- Output format: 9:16 Vertical Full HD (1080x1920 @ 30fps), total duration under 60 seconds.
- Voice identity: Zero-shot voice cloning from `sample-files/voices/sandip/samples/Bng_sample.mp3` with reference transcript `"নমস্কার আমি সন্দীপ অডিওতে বলা কথাটি লিখলে ক্লোনিং নিখুঁত হয়"`.
- Authentic Vedic aesthetics: Ancient Indian royal attire (dhoti, angavastram, mukut, strictly NO sarees on male kings), Devanagari Sanskrit mantras, classical Raja Ravi Varma academic fine art style.
- YouTube monetization compliance: 100% human-sounding creator voice, dynamic multi-frame visual motion, EBU R128 broadcast audio standard (-14 LUFS).

## Review Focus

- OOM on 4GB VRAM when generating long audio passages: test batch chunking under 12 seconds per segment and FP16 inference.
- Missing CUDA environment: test automatic fallback to CPU synthesis when PyTorch CUDA is unavailable.
- Reference audio transcript mismatch: test exact verbatim text alignment with `Bng_sample.mp3` to avoid pronunciation drift.
- Static visual freeze: test that every Remotion scene contains active multi-layer motion (foreground/background differential speed, particle dynamics).
- Audio clipping or distortion: test that EBU R128 mastering enforces -1.0 dBFS true peak ceiling.

---

### Task 1: Dhee-Indic-F5 Local Voice Cloning Tool Integration

**Files:**
- Create: `tools/audio/dhee_indicf5_tts.py`
- Test: `tests/tools/test_dhee_indicf5_tts.py`

**Interfaces:**
- Consumes: `sample-files/voices/sandip/samples/Bng_sample.mp3`, text string in Bengali, target output path.
- Produces: `DheeIndicF5TTS.execute(inputs: dict[str, Any]) -> ToolResult` returning `output_path`, `duration_seconds`, `sample_rate`.

- [ ] **Step 1: Write the failing test for Dhee-Indic-F5 tool**

```python
# tests/tools/test_dhee_indicf5_tts.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

def test_dhee_indicf5_tool_registration():
    from tools.audio.dhee_indicf5_tts import DheeIndicF5TTS
    tool = DheeIndicF5TTS()
    assert tool.name == "dhee_indicf5_tts"
    assert tool.capability == "tts"
    assert "bn-IN" in tool.supports["languages"]

def test_dhee_indicf5_sandip_profile_resolution():
    from tools.audio.dhee_indicf5_tts import DheeIndicF5TTS
    tool = DheeIndicF5TTS()
    ref_audio, ref_text = tool.resolve_sandip_reference()
    assert Path(ref_audio).exists()
    assert "নমস্কার আমি সন্দীপ" in ref_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/tools/test_dhee_indicf5_tts.py -v`
Expected: FAIL with "No module named 'tools.audio.dhee_indicf5_tts'"

- [ ] **Step 3: Implement `DheeIndicF5TTS` in `tools/audio/dhee_indicf5_tts.py`**

Implement tool with:
- Model repository: `dheeyantra/dhee-indic-f5` (fallback `ai4bharat/IndicF5`).
- Automatic resolution of Sandip reference audio (`sample-files/voices/sandip/samples/Bng_sample.mp3`) and reference text (`"নমস্কার আমি সন্দীপ অডিওতে বলা কথাটি লিখলে ক্লোনিং নিখুঁত হয়"`).
- VRAM management: FP16 model loading, max 4GB safety clamp, and CPU fallback when CUDA is absent.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/tools/test_dhee_indicf5_tts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/audio/dhee_indicf5_tts.py tests/tools/test_dhee_indicf5_tts.py
git commit -m "feat(audio): add local Dhee-Indic-F5 zero-shot voice cloning tool"
```

---

### Task 2: Sandip Broadcast Audio Mastering Chain

**Files:**
- Create: `tools/audio/sandip_audio_master.py`
- Test: `tests/tools/test_sandip_audio_master.py`

**Interfaces:**
- Consumes: Raw audio generated by `DheeIndicF5TTS` or user microphone recordings.
- Produces: `SandipAudioMaster.master_narration(raw_audio_path: str, output_path: str) -> str` adhering to EBU R128 (-14 LUFS, -1 dBFS peak, 75Hz high-pass, vocal warmth EQ).

- [ ] **Step 1: Write the failing test for Sandip voice mastering**

```python
# tests/tools/test_sandip_audio_master.py
import pytest
from pathlib import Path

def test_sandip_audio_mastering_pipeline(tmp_path):
    from tools.audio.sandip_audio_master import SandipAudioMaster
    master = SandipAudioMaster()
    dummy_wav = tmp_path / "dummy.wav"
    output_wav = tmp_path / "mastered.wav"
    
    # Create simple sine wave for testing
    import wave, math, struct
    with wave.open(str(dummy_wav), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(24000)
        for i in range(24000):
            val = int(32767 * 0.5 * math.sin(2 * math.pi * 440 * i / 24000))
            f.writeframes(struct.pack('<h', val))
            
    res = master.master_narration(str(dummy_wav), str(output_wav))
    assert Path(res).exists()
    assert Path(res).stat().st_size > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/tools/test_sandip_audio_master.py -v`
Expected: FAIL with "No module named 'tools.audio.sandip_audio_master'"

- [ ] **Step 3: Implement `SandipAudioMaster` in `tools/audio/sandip_audio_master.py`**

Implement FFmpeg filter chain:
- High-pass: `highpass=f=75` (eliminates low mic rumble).
- Warmth & Presence: `equalizer=f=120:width_type=o:width=1.5:g=2.5,equalizer=f=3000:width_type=o:width=1.5:g=1.5`.
- Dynamic opto compression: `acompressor=threshold=-18dB:ratio=3:attack=15:release=120`.
- EBU R128 Loudness Normalization: `loudnorm=I=-14:LRA=7:TP=-1.0`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/tools/test_sandip_audio_master.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/audio/sandip_audio_master.py tests/tools/test_sandip_audio_master.py
git commit -m "feat(audio): add studio mastering chain for Sandip voice profile"
```

---

### Task 3: Multi-Frame Cinematic Motion Engine (Beyond Simple Zoom)

**Files:**
- Create: `tools/video/cinematic_motion_animator.py`
- Modify: `remotion-composer/src/components/DynamicMotionScene.tsx`
- Test: `tests/tools/test_cinematic_motion_animator.py`

**Interfaces:**
- Consumes: 8K scene illustrations, motion parameters (2.5D parallax velocity, character breathing rate, particle intensity, camera shake/push).
- Produces: Remotion motion scene descriptors with multi-layer depth differential, animated overlays, and dynamic camera choreography.

- [ ] **Step 1: Write the failing test for dynamic motion animator**

```python
# tests/tools/test_cinematic_motion_animator.py
import pytest

def test_dynamic_motion_scene_descriptor():
    from tools.video.cinematic_motion_animator import CinematicMotionAnimator
    animator = CinematicMotionAnimator()
    
    scene = {
        "id": 1,
        "image": "scene_1.jpg",
        "action": "manthara_poisoning_mind",
        "mood": "dark_conspiracy"
    }
    descriptor = animator.build_motion_descriptor(scene)
    assert descriptor["motion_type"] == "2.5d_parallax_pulse"
    assert "particle_fx" in descriptor
    assert "camera_dynamics" in descriptor
    assert descriptor["camera_dynamics"]["rate"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/tools/test_cinematic_motion_animator.py -v`
Expected: FAIL with "No module named 'tools.video.cinematic_motion_animator'"

- [ ] **Step 3: Implement `CinematicMotionAnimator` and Remotion `DynamicMotionScene.tsx`**

Implement:
- Multi-layer 2.5D differential velocity (background moves at 1.05x, subject at 1.15x, foreground dust/particles at 1.35x).
- Micro-motions: periodic character breathing scale, eye glint flicker, divine weapon gleam animation.
- Dynamic environmental particle physics: swirling embers, stormy dust, falling palace drapes, candle flicker.
- Dramatic camera choreography: speed-ramped whip zooms, shockwave shakes for climaxes.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/tools/test_cinematic_motion_animator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/video/cinematic_motion_animator.py remotion-composer/src/components/DynamicMotionScene.tsx tests/tools/test_cinematic_motion_animator.py
git commit -m "feat(video): add 2.5D multi-frame cinematic motion engine"
```

---

### Task 4: Ramayana Viral Episode Script (Manthara's Midnight Plot)

**Files:**
- Create: `projects/ramayana-manthara-chakranta/artifacts/script.json`
- Create: `scripts/generate_ramayana_ep7_content.py`
- Test: `tests/pipelines/test_ramayana_ep7_spec.py`

**Interfaces:**
- Consumes: Script narrative, Sandip voice tone markers, scene visual prompts.
- Produces: Full 7-scene production specification (<60s duration, viral YouTube hooks, high retention pacing).

- [ ] **Step 1: Write the failing test for Episode 7 specification**

```python
# tests/pipelines/test_ramayana_ep7_spec.py
import pytest
from pathlib import Path
import json

def test_ep7_script_structure():
    script_path = Path("projects/ramayana-manthara-chakranta/artifacts/script.json")
    assert script_path.exists()
    with open(script_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data["scenes"]) == 7
    assert data["total_duration"] <= 59.0
    assert "মন্থরা" in data["scenes"][0]["narration_bn"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/pipelines/test_ramayana_ep7_spec.py -v`
Expected: FAIL with file not found

- [ ] **Step 3: Write `generate_ramayana_ep7_content.py` and produce `script.json`**

Create 7 high-adrenaline scenes in Bengali:
1. Scene 1: অযোধ্যায় উৎসবের আলো ও প্রাসাদে অন্ধকারের ছায়া (0-8s) - Opening Hook.
2. Scene 2: দাসী মন্থরার কুটিল প্রবেশ ও বিষাক্ত মন্ত্রণা (8-16s) - Rising Tension.
3. Scene 3: রাণী কৈকেয়ীর ক্রোধাগার প্রবেশ ও অলঙ্কার ত্যাগ (16-24s) - Shock Factor.
4. Scene 4: মহারাজ দশরথের আনন্দ ও কৈকেয়ীর চরম বর প্রার্থনা (24-33s) - Heartbreak.
5. Scene 5: দুটি প্রাণঘাতী বর: ভরতের অভিষেক ও রামের ১৪ বছর বনবাস (33-42s) - Plot Twist.
6. Scene 6: দশরথের বুকফাটা হাহাকার ও অজ্ঞান হয়ে মাটিতে পতন (42-50s) - Emotional Climax.
7. Scene 7: প্রভাতের সূর্য ও শ্রীরামের শান্ত আত্মত্যাগ... জয় শ্রী রাম! (50-58s) - Viral Call to Action.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/pipelines/test_ramayana_ep7_spec.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add projects/ramayana-manthara-chakranta/artifacts/script.json scripts/generate_ramayana_ep7_content.py tests/pipelines/test_ramayana_ep7_spec.py
git commit -m "feat(mythological): add Ramayana Ep7 high-retention script and scene plan"
```

---

### Task 5: End-to-End Voice & Video Pipeline Verification

**Files:**
- Create: `scripts/produce_ramayana_ep7_full.py`
- Test: `tests/integration/test_ramayana_ep7_e2e.py`

**Interfaces:**
- Consumes: Synthesized Sandip narration + 7 multi-frame motion scenes.
- Produces: Rendered 1080x1920 @ 30fps MP4 video (`ramayana_manthara_chakranta_9x16.mp4`), verifying YouTube monetization readiness.

- [ ] **Step 1: Write the failing integration test**

```python
# tests/integration/test_ramayana_ep7_e2e.py
import pytest
from pathlib import Path

def test_ep7_production_artifacts():
    proj_dir = Path("projects/ramayana-manthara-chakranta")
    assert (proj_dir / "artifacts/script.json").exists()
    assert (proj_dir / "artifacts/timestamps.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_ramayana_ep7_e2e.py -v`
Expected: FAIL

- [ ] **Step 3: Implement end-to-end production orchestrator `produce_ramayana_ep7_full.py`**

- Generates voiceover via `DheeIndicF5TTS` using Sandip reference.
- Applies `SandipAudioMaster` EBU R128 loudness and EQ.
- Renders Remotion composition with `DynamicMotionScene` multi-frame effects.
- Asserts video parameters (1080x1920, 30fps, duration <= 59.0s).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_ramayana_ep7_e2e.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/produce_ramayana_ep7_full.py tests/integration/test_ramayana_ep7_e2e.py
git commit -m "feat(integration): complete end-to-end Ep7 production pipeline"
```
