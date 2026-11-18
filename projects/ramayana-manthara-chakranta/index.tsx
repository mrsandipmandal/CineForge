import React from "react";
import {
  AbsoluteFill,
  Audio,
  Composition,
  Sequence,
  registerRoot,
  staticFile,
} from "remotion";
import { DynamicMotionScene } from "../../remotion-composer/src/components/DynamicMotionScene";

export interface SceneItem {
  id: number;
  image: string;
  subtitle: string;
  startFrame: number;
  durationFrames: number;
  mood: string;
  action: string;
  depthLayers: {
    background_scale_speed?: number;
    subject_scale_speed?: number;
    foreground_speed?: number;
  };
  characterDynamics: {
    breathing?: boolean;
    breathing_cycle_sec?: number;
    eye_glint_flicker?: boolean;
    weapon_glow_pulse?: boolean;
  };
  particleFx: {
    type?: string;
    density?: number;
    turbulence?: number;
  };
  cameraDynamics: {
    rate?: number;
    shake_intensity?: number;
    rack_focus_frames?: number;
    whip_pan?: boolean;
  };
}

const SCENES: SceneItem[] = [
  {
    "id": 1,
    "image": "ramayana-manthara-chakranta/scene_1.jpg",
    "subtitle": "প্রভাত হলেই শ্রীরামের রাজ্যাভিষেক... কিন্তু প্রাসাদের অন্ধকারে ঘনাচ্ছে অমঙ্গল!",
    "startFrame": 0,
    "durationFrames": 255,
    "mood": "festive_yet_ominous",
    "action": "Ayodhya illuminated with golden diyas as midnight shadows creep",
    "depthLayers": {
      "background_scale_speed": 1.05,
      "subject_scale_speed": 1.15,
      "foreground_speed": 1.35
    },
    "characterDynamics": {
      "breathing": true,
      "breathing_cycle_sec": 3.2,
      "eye_glint_flicker": true,
      "weapon_glow_pulse": false
    },
    "particleFx": {
      "type": "golden_embers",
      "density": 45,
      "turbulence": 1.4
    },
    "cameraDynamics": {
      "rate": 1.1,
      "shake_intensity": 0.0,
      "rack_focus_frames": 10,
      "whip_pan": false
    }
  },
  {
    "id": 2,
    "image": "ramayana-manthara-chakranta/scene_2.jpg",
    "subtitle": "কুটিলদাসী মন্থরা রানী কৈকেয়ীর কানে ঢালল বিষাক্ত সন্দেহের বিষ!",
    "startFrame": 255,
    "durationFrames": 240,
    "mood": "conspiratorial_dark",
    "action": "Manthara whispering poisonous malice into Kaikeyi's ear",
    "depthLayers": {
      "background_scale_speed": 1.08,
      "subject_scale_speed": 1.2,
      "foreground_speed": 1.4
    },
    "characterDynamics": {
      "breathing": true,
      "breathing_cycle_sec": 2.8,
      "eye_glint_flicker": true,
      "weapon_glow_pulse": false
    },
    "particleFx": {
      "type": "dark_palace_shadows",
      "density": 40,
      "turbulence": 1.8
    },
    "cameraDynamics": {
      "rate": 1.2,
      "shake_intensity": 0.05,
      "rack_focus_frames": 15,
      "whip_pan": false
    }
  },
  {
    "id": 3,
    "image": "ramayana-manthara-chakranta/scene_3.jpg",
    "subtitle": "মন্থরার বিষে উন্মাদ কৈকেয়ী প্রবেশ করলেন অন্ধকার কোপভবনে!",
    "startFrame": 495,
    "durationFrames": 255,
    "mood": "furious_vengeful",
    "action": "Kaikeyi furiously casting off royal ornaments and entering Kopabhavan",
    "depthLayers": {
      "background_scale_speed": 1.1,
      "subject_scale_speed": 1.25,
      "foreground_speed": 1.45
    },
    "characterDynamics": {
      "breathing": true,
      "breathing_cycle_sec": 2.4,
      "eye_glint_flicker": true,
      "weapon_glow_pulse": false
    },
    "particleFx": {
      "type": "storm_dust",
      "density": 50,
      "turbulence": 2.0
    },
    "cameraDynamics": {
      "rate": 1.3,
      "shake_intensity": 0.1,
      "rack_focus_frames": 12,
      "whip_pan": true
    }
  },
  {
    "id": 4,
    "image": "ramayana-manthara-chakranta/scene_4.jpg",
    "subtitle": "আনন্দে বিহ্বল বৃদ্ধ রাজা দশরথ কোপভবনে প্রবেশ করলেন...",
    "startFrame": 750,
    "durationFrames": 270,
    "mood": "heartbreaking_agony",
    "action": "Elderly Emperor Dasharatha entering Kopabhavan chamber holding golden lamp in grief",
    "depthLayers": {
      "background_scale_speed": 1.05,
      "subject_scale_speed": 1.15,
      "foreground_speed": 1.3
    },
    "characterDynamics": {
      "breathing": true,
      "breathing_cycle_sec": 3.5,
      "eye_glint_flicker": true,
      "weapon_glow_pulse": false
    },
    "particleFx": {
      "type": "candle_flicker",
      "density": 30,
      "turbulence": 1.1
    },
    "cameraDynamics": {
      "rate": 1.05,
      "shake_intensity": 0.02,
      "rack_focus_frames": 12,
      "whip_pan": false
    }
  },
  {
    "id": 5,
    "image": "ramayana-manthara-chakranta/scene_5.jpg",
    "subtitle": "'ভরতের রাজ্যাভিষেক, আর শ্রীরামের চোদ্দ বছরের কঠোর বনবাস!'",
    "startFrame": 1020,
    "durationFrames": 255,
    "mood": "cruel_demand",
    "action": "Queen Kaikeyi demanding two fatal boons: Bharata's coronation and Rama's 14-year exile",
    "depthLayers": {
      "background_scale_speed": 1.1,
      "subject_scale_speed": 1.22,
      "foreground_speed": 1.4
    },
    "characterDynamics": {
      "breathing": true,
      "breathing_cycle_sec": 3.0,
      "eye_glint_flicker": true,
      "weapon_glow_pulse": true
    },
    "particleFx": {
      "type": "dark_palace_shadows",
      "density": 45,
      "turbulence": 1.6
    },
    "cameraDynamics": {
      "rate": 1.25,
      "shake_intensity": 0.08,
      "rack_focus_frames": 14,
      "whip_pan": false
    }
  },
  {
    "id": 6,
    "image": "ramayana-manthara-chakranta/scene_6.jpg",
    "subtitle": "'কৈকেয়ী, আমার প্রাণ নাও, কিন্তু আমার রামকে বনবাস দিও না!'",
    "startFrame": 1275,
    "durationFrames": 255,
    "mood": "tragic_collapse",
    "action": "Emperor Dasharatha collapsing onto palace floor in unbearable grief pleading for Rama",
    "depthLayers": {
      "background_scale_speed": 1.12,
      "subject_scale_speed": 1.3,
      "foreground_speed": 1.5
    },
    "characterDynamics": {
      "breathing": true,
      "breathing_cycle_sec": 2.0,
      "eye_glint_flicker": true,
      "weapon_glow_pulse": false
    },
    "particleFx": {
      "type": "shockwave_dust",
      "density": 60,
      "turbulence": 2.2
    },
    "cameraDynamics": {
      "rate": 1.4,
      "shake_intensity": 0.25,
      "rack_focus_frames": 18,
      "whip_pan": true
    }
  },
  {
    "id": 7,
    "image": "ramayana-manthara-chakranta/scene_7.jpg",
    "subtitle": "নিষ্ঠুর কৈকেয়ী, অচেতন দশরথ... এরপর কী করবেন শ্রীরাম?",
    "startFrame": 1530,
    "durationFrames": 225,
    "mood": "epic_cliffhanger",
    "action": "Dark midnight over ancient Ayodhya under blood-red moon as Dasharatha lies unconscious",
    "depthLayers": {
      "background_scale_speed": 1.06,
      "subject_scale_speed": 1.18,
      "foreground_speed": 1.35
    },
    "characterDynamics": {
      "breathing": true,
      "breathing_cycle_sec": 3.2,
      "eye_glint_flicker": true,
      "weapon_glow_pulse": true
    },
    "particleFx": {
      "type": "golden_embers",
      "density": 50,
      "turbulence": 1.5
    },
    "cameraDynamics": {
      "rate": 1.15,
      "shake_intensity": 0.03,
      "rack_focus_frames": 12,
      "whip_pan": false
    }
  }
];

export const RamayanaEp7MantharaChakranta: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#080305" }}>
      {/* Multi-Frame 2.5D Cinematic Motion Scenes */}
      {SCENES.map((scene) => (
        <Sequence
          key={scene.id}
          from={scene.startFrame}
          durationInFrames={scene.durationFrames}
        >
          <DynamicMotionScene
            id={`scene_${scene.id}`}
            image={scene.image}
            depthLayers={scene.depthLayers}
            characterDynamics={scene.characterDynamics}
            particleFx={scene.particleFx}
            cameraDynamics={scene.cameraDynamics}
            mood={scene.mood}
            action={scene.action}
            vignette={true}
          />

          {/* Classical Vedic Subtitle Pill */}
          <div
            style={{
              position: "absolute",
              bottom: 120,
              left: 48,
              right: 48,
              display: "flex",
              justifyContent: "center",
              pointerEvents: "none",
            }}
          >
            <div
              style={{
                backgroundColor: "rgba(10, 4, 8, 0.85)",
                border: "1.5px solid rgba(255, 215, 0, 0.75)",
                borderRadius: 18,
                padding: "16px 28px",
                boxShadow: "0 10px 36px rgba(0, 0, 0, 0.9)",
                maxWidth: 960,
                textAlign: "center",
              }}
            >
              <span
                style={{
                  color: "#FFF9E6",
                  fontSize: 34,
                  fontWeight: 700,
                  fontFamily: "'Noto Sans Bengali', 'Cinzel', serif",
                  lineHeight: 1.35,
                  textShadow: "0 2px 10px rgba(0, 0, 0, 0.95)",
                }}
              >
                {scene.subtitle}
              </span>
            </div>
          </div>
        </Sequence>
      ))}

      {/* EBU R128 Mastered Sandip Broadcast Voiceover */}
      <Audio src={staticFile("ramayana-manthara-chakranta/audio_mix.wav")} />
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="RamayanaEp7MantharaChakranta"
      component={RamayanaEp7MantharaChakranta}
      durationInFrames={1755}
      fps={30}
      width={1080}
      height={1920}
    />
  );
};

registerRoot(RemotionRoot);
