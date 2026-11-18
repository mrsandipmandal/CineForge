---
name: mythological-video-production
description: Use when producing Hindu epic or Indian mythological video content (Ramayana, Mahabharata, Puranas, Vedic deities, ancient kings) to ensure strict historical and scriptural authenticity, proper male Vedic royal attire, sacred Sanskrit Devanagari inscriptions, and broadcast-grade studio narration.
---

# Mythological Video Production (Vedic & Epic Authenticity)

## Overview

When generating scripts, artwork, audio narration, and Remotion video compositions for Indian mythological and epic stories (e.g. Ramayana, Mahabharata, Shiva Purana, Vishnu Purana), generic AI generators tend to make severe cultural and scriptural errors:
- Depicting male Vedic kings/emperors in feminine sarees or modern gowns.
- Inscribing foreign glyphs (Chinese, East Asian, or pseudo-runes) on holy celestial divine weapons (Pinaka, Gandiva, Sudarshana Chakra, Trishul).
- Using bland, thin, or generic text-to-speech without dramatic baritone resonance or emotional gravitas.
- Missing authentic Sanskrit mantras and sacred Devanagari calligraphy.

This skill establishes the non-negotiable authenticity rules, prompt engineering contracts, audio mastering standards, and visual composition patterns for CineForge mythological productions.

---

## 1. Visual Authenticity & Wardrobe Contract

### Male Royal & Emperor Attire (Kings, Maharajas, Rishis, Princes)
- **STRICTLY FORBIDDEN:** Gowns, sarees, Victorian capes, Greek tunics, or unisex dresses on male Vedic monarchs (e.g. Maharaja Janaka, Dasharatha, Rama, Lakshmana, Bharata).
- **MANDATORY SPECIFICATION:**
  - **Lower Body:** Pristine pleated silk *Dhoti* (धोती) or *Pancha* with intricate Zari golden brocade border (कशीदाकारी).
  - **Upper Body:** Regal pleated *Uttariya* or *Angavastram* (अंगवस्त्रम्) draped elegantly across broad shoulders, revealing royal chest jewelry, armor plate (*Kavach*), or sacred thread (*Yajnopavita*).
  - **Headwear:** Vedic golden crown (*Mukut* / मुकुट) with radiant sunburst or lotus crest, embedded with Navaratna jewels.
  - **Jewelry:** Golden armlets (*Keyura* / केयूर), wristlets (*Kankana*), pearl necklaces (*Haar*), and royal ear ornaments (*Kundala*).
  - **Appearance:** Royal beard or noble facial structure, raised hand in blessing or solemn oath (*Sankalpa*).

### Divine Weaponry & Inscriptions (Shiva Pinaka, Vishnu Sharanga, Gandiva)
- **STRICTLY FORBIDDEN:** Chinese, Japanese, Korean, Arabic, or generic fantasy runes on divine astras.
- **MANDATORY SPECIFICATION:**
  - Sacred Devanagari Sanskrit mantras engraved into the cosmic metal/wood:
    - Shiva astras (Pinaka): `"ॐ ॐ नमः शिवाय ॐ"`, Trishul (त्रिशूल), and Damru (डमरू) engravings.
    - Vishnu astras (Sharanga, Sudarshana): `"ॐ नमो नारायणाय"`, Shankha (शंख), and Chakra (चक्र) motifs.
  - Cosmic visual effects: Radiant blue and golden divine aura (*Divya Prabha*), lightning sparks crackling along the bowstring (*Pratyancha*), celestial weight requiring an 8-wheeled iron cart pulled by hundreds of men.

### Female Divine Attire (Devi Sita, Queen Sunayana, Kausalya)
- Traditional royal Vedic *Sari* / *Antariya* in auspicious vermilion red (*Sindoor*), crimson, or deep gold.
- Elaborate bridal floral garland (*Jaimala*), sheer silk veil (*Ghoonghat* / *Chunari*), traditional bridal jewellery (*Maang Tikka*, *Nath*, *Bajuband*).

---

## 2. Prompting Rules for Image Generators

Whenever generating imagery for an episode, every prompt MUST include:

1. **Negative Prompt Shield:**
   ```
   saree on male king, woman dress on man, Chinese characters, East Asian glyphs, modern western suits, low quality, deformed hands, blurry face, plastic skin
   ```
2. **Positive Authentication Block:**
   ```
   Masterpiece oil painting in the style of Raja Ravi Varma and divine cinematic Indian epic art, ancient Vedic Mithila sabha hall, hyper-detailed architecture, sacred Devanagari Sanskrit mantras carved in gold, royal Vedic emperor wearing traditional pleated golden-bordered dhoti and angavastram, mukut crown, 8K resolution, volumetric lighting, epic atmosphere.
   ```

---

## 3. Audio Narration & Voice Contract

Mythological storytelling requires dramatic gravitas, slow authoritative pacing, and rich baritone chest resonance.

### Voice Standard
- **Voice Archetype:** Sanjay Deep Authoritative Storyteller.
- **Provider & Model:**
  - Primary Cloud: Fish Audio `s2-pro` (`28dcd01c14684153842b6d0b4713af80` or Sanjay Baritone model) or OpenAI.fm Fable voice.
  - Prompt Direction: Deep, slow, suspenseful, epic mythological delivery with dramatic pauses between sentences.
- **Mastering Chain (FFmpeg / Sox):**
  - High-pass filter at 75 Hz (clean mud).
  - Parametric EQ boost: +2.5 dB at 120 Hz with Q=1.2 (rich chest resonance).
  - Subtle presence boost: +1.8 dB at 3.5 kHz (crisp Devanagari pronunciation clarity).
  - Opto-style dynamic compression: 3:1 ratio, 25ms attack, 120ms release.
  - Loudness normalization: EBU R128 integrated loudness target of -14 LUFS (True Peak -1.0 dBFS).

---

## 4. Visual Composition & Remotion 9:16 VFX Patterns

For YouTube Shorts and Instagram Reels (1080x1920 vertical format):

1. **Camera Motion:** Continuous Ken Burns slow push-in (zoom 1.0 -> 1.08) or subtle vertical pan upward to emphasize the monumental stature of divine figures and celestial bows.
2. **Particle Overlay Layers:**
   - Golden divine dust / embers (`spark_layer`) blending over dramatic moments.
   - Blue lightning flashes (`lightning_burst`) during bow bending or Parashurama's arrival.
   - Petal shower (*Pushp Vrishti*) during royal svayamvara climax.
3. **Subtitles & Typography:**
   - Font: Classical Devanagari / Serif font (e.g. Rozha One, Cinzel, Noto Sans Devanagari).
   - Styling: Golden gradient fill (`linear-gradient(180deg, #FFF6D1 0%, #E5A93C 100%)`), dark translucent pill backdrop with 1px golden border, and soft black drop shadow.
   - Pacing: Synchronized precisely with whisper/speech timestamps.
