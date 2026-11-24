import React from "react";
import {
  AbsoluteFill,
  Audio,
  Composition,
  Img,
  Sequence,
  interpolate,
  registerRoot,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Helper for deterministic seeded pseudorandom numbers
const seededRandom = (seed: number): number => {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
};

// ---------------------------------------------------------------------------
// VFX 1: Festive Ayodhya Deepotsav (Scene 1)
// ---------------------------------------------------------------------------
const DeepotsavVFX: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Warm Golden Horizon Glow */}
      <div
        style={{
          position: "absolute",
          bottom: 150,
          left: 0,
          right: 0,
          height: 600,
          background:
            "radial-gradient(ellipse at 50% 90%, rgba(255, 170, 0, 0.35) 0%, rgba(255, 110, 0, 0.16) 50%, transparent 80%)",
          mixBlendMode: "screen",
          opacity: 0.85 + Math.sin(frame * 0.08) * 0.15,
        }}
      />

      {/* Floating Sacred Golden Diyas and Flower Petals */}
      {Array.from({ length: 40 }).map((_, i) => {
        const seedX = seededRandom(i * 71);
        const seedY = seededRandom(i * 43);
        const curY = (seedY * 1920 + frame * (1.5 + seededRandom(i * 19) * 2.5)) % 1920;
        const curX = seedX * 1080 + Math.sin(frame * 0.04 + i) * 25;
        const size = 4 + seededRandom(i * 31) * 6;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: curX,
              top: curY,
              width: size,
              height: size,
              borderRadius: "50%",
              backgroundColor: i % 2 === 0 ? "#FFE082" : "#FFB300",
              boxShadow: "0 0 14px 4px rgba(255, 179, 0, 0.85)",
              opacity: Math.sin(frame * 0.06 + i) * 0.35 + 0.65,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// VFX 2: Midnight Palace Sinister Conspiracy (Scene 2)
// ---------------------------------------------------------------------------
const MidnightConspiracyVFX: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Dark Conspiratorial Vignette Pulse */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(12, 4, 18, 0.65) 100%)",
          opacity: 0.85 + Math.sin(frame * 0.05) * 0.15,
        }}
      />

      {/* Eerie Whispering Shadow Dust */}
      {Array.from({ length: 28 }).map((_, i) => {
        const seedX = seededRandom(i * 83);
        const seedY = seededRandom(i * 59);
        const curY = ((seedY * 1920 - frame * 1.8) % 1920 + 1920) % 1920;
        const curX = seedX * 1080 + Math.sin(frame * 0.03 + i) * 20;
        const size = 3 + seededRandom(i * 23) * 4;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: curX,
              top: curY,
              width: size,
              height: size,
              borderRadius: "50%",
              backgroundColor: "#E0AAFF",
              boxShadow: "0 0 10px 2px rgba(180, 80, 255, 0.5)",
              opacity: Math.sin(frame * 0.08 + i) * 0.4 + 0.45,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// VFX 3: Kopabhavan Candlelight & Broken Jewels (Scene 3)
// ---------------------------------------------------------------------------
const KopabhavanVFX: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Flickering Somber Oil Lamp Warm Aura */}
      <div
        style={{
          position: "absolute",
          top: 550,
          left: 120,
          width: 500,
          height: 500,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(255, 170, 0, 0.32) 0%, rgba(255, 100, 0, 0.12) 50%, transparent 80%)",
          mixBlendMode: "screen",
          opacity: 0.8 + Math.sin(frame * 0.14) * 0.2,
        }}
      />

      {/* Scattered Shimmering Pearl Sparkles on Marble */}
      {Array.from({ length: 25 }).map((_, i) => {
        const seedX = seededRandom(i * 97);
        const seedY = seededRandom(i * 67);
        const curY = 1250 + seedY * 550;
        const curX = seedX * 1080;
        const glint = Math.sin(frame * 0.15 + i * 2) * 0.5 + 0.5;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: curX,
              top: curY,
              width: 4,
              height: 4,
              borderRadius: "50%",
              backgroundColor: "#FFFFFF",
              boxShadow: "0 0 12px 4px rgba(255, 235, 180, 0.9)",
              opacity: glint,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// VFX 4: Dasharatha Oath & Royal Sun Crest (Scene 4)
// ---------------------------------------------------------------------------
const DasharathaOathVFX: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Golden Solar Halo behind the Throne */}
      <div
        style={{
          position: "absolute",
          top: 600,
          left: 200,
          width: 680,
          height: 680,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(255, 200, 50, 0.25) 0%, rgba(255, 140, 0, 0.1) 50%, transparent 75%)",
          mixBlendMode: "screen",
          transform: `scale(${1 + Math.sin(frame * 0.04) * 0.05})`,
        }}
      />

      {/* Somber Floating Embers */}
      {Array.from({ length: 25 }).map((_, i) => {
        const seedX = seededRandom(i * 53);
        const seedY = seededRandom(i * 89);
        const curY = ((seedY * 1920 - frame * 2.0) % 1920 + 1920) % 1920;
        const curX = seedX * 1080 + Math.sin(frame * 0.03 + i) * 15;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: curX,
              top: curY,
              width: 3,
              height: 3,
              borderRadius: "50%",
              backgroundColor: "#FFD54F",
              boxShadow: "0 0 10px 2px rgba(255, 215, 0, 0.7)",
              opacity: Math.sin(frame * 0.06 + i) * 0.35 + 0.55,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// VFX 5: The Fatal Two Boons & Impending Exile (Scene 5)
// ---------------------------------------------------------------------------
const VanvasDestinyVFX: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Heavy Fateful Crimson & Shadow Vignette */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(20, 5, 8, 0.7) 100%)",
          opacity: 0.85 + Math.sin(frame * 0.06) * 0.15,
        }}
      />

      {/* Dramatic Fateful Sparks */}
      {Array.from({ length: 28 }).map((_, i) => {
        const seedX = seededRandom(i * 67);
        const seedY = seededRandom(i * 91);
        const curY = ((seedY * 1920 - frame * 2.5) % 1920 + 1920) % 1920;
        const curX = seedX * 1080 + Math.sin(frame * 0.04 + i) * 20;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: curX,
              top: curY,
              width: 3,
              height: 5,
              borderRadius: "40%",
              backgroundColor: i % 2 === 0 ? "#FFAB40" : "#FF5252",
              boxShadow: "0 0 10px 2px rgba(255, 80, 50, 0.7)",
              opacity: Math.sin(frame * 0.08 + i) * 0.35 + 0.55,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// VFX 6: Dasharatha Agony & Thunderous Grief (Scene 6)
// ---------------------------------------------------------------------------
const HeartbreakGriefVFX: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Heavy Grief Vignette & Pulsing Dark Shadow */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 35%, rgba(15, 2, 4, 0.72) 100%)",
          opacity: 0.8 + Math.sin(frame * 0.08) * 0.2,
        }}
      />

      {/* Weeping Ember Tears */}
      {Array.from({ length: 30 }).map((_, i) => {
        const seedX = seededRandom(i * 73);
        const seedY = seededRandom(i * 39);
        const curY = (seedY * 1920 + frame * 3.5) % 1920;
        const curX = seedX * 1080 + Math.sin(frame * 0.04 + i) * 12;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: curX,
              top: curY,
              width: 3,
              height: 7,
              borderRadius: "40%",
              backgroundColor: "#FF8A80",
              boxShadow: "0 0 10px 3px rgba(255, 82, 82, 0.65)",
              opacity: Math.sin(frame * 0.09 + i) * 0.35 + 0.6,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// VFX 7: Maryada Purushottam Rama Solar Halo & CTA Radiance (Scene 7)
// ---------------------------------------------------------------------------
const SuryaDharmaVFX: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Radiant Solar Crown Aura */}
      <div
        style={{
          position: "absolute",
          top: 350,
          left: 140,
          width: 800,
          height: 800,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(255, 235, 120, 0.38) 0%, rgba(255, 160, 0, 0.18) 45%, transparent 75%)",
          mixBlendMode: "screen",
          transform: `scale(${1 + Math.sin(frame * 0.04) * 0.06})`,
          opacity: 0.9,
        }}
      />

      {/* Celestial Golden Sparkles Cascading */}
      {Array.from({ length: 45 }).map((_, i) => {
        const seedX = seededRandom(i * 61);
        const seedY = seededRandom(i * 47);
        const curY = (seedY * 1920 + frame * 2.8) % 1920;
        const curX = seedX * 1080 + Math.sin(frame * 0.04 + i) * 30;
        const size = 3 + seededRandom(i * 31) * 6;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: curX,
              top: curY,
              width: size,
              height: size,
              borderRadius: "50%",
              backgroundColor: i % 2 === 0 ? "#FFF8E1" : "#FFD54F",
              boxShadow: "0 0 14px 4px rgba(255, 215, 0, 0.95)",
              opacity: Math.sin(frame * 0.07 + i) * 0.35 + 0.65,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Scene Slide Component (Image + Ken Burns + VFX + Synchronized Subtitles)
// ---------------------------------------------------------------------------
export interface SceneItem {
  id: number;
  imageSrc: string;
  subtitle: string;
  startFrame: number;
  durationFrames: number;
  zoomDirection: "in" | "out" | "pan-left" | "pan-right";
  vfx: "deepotsav" | "conspiracy" | "kopabhavan" | "dasharatha_oath" | "vanvas_destiny" | "heartbreak" | "surya_dharma";
}

const SceneSlide: React.FC<{ item: SceneItem }> = ({ item }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Smooth Ken Burns Camera Motion
  let transform = "";
  if (item.zoomDirection === "in") {
    const scale = interpolate(frame, [0, item.durationFrames], [1.0, 1.15], {
      extrapolateRight: "clamp",
    });
    transform = `scale(${scale})`;
  } else if (item.zoomDirection === "out") {
    const scale = interpolate(frame, [0, item.durationFrames], [1.15, 1.0], {
      extrapolateRight: "clamp",
    });
    transform = `scale(${scale})`;
  } else if (item.zoomDirection === "pan-left") {
    const scale = 1.12;
    const transX = interpolate(frame, [0, item.durationFrames], [25, -25], {
      extrapolateRight: "clamp",
    });
    transform = `scale(${scale}) translateX(${transX}px)`;
  } else {
    const scale = 1.12;
    const transX = interpolate(frame, [0, item.durationFrames], [-25, 25], {
      extrapolateRight: "clamp",
    });
    transform = `scale(${scale}) translateX(${transX}px)`;
  }

  // Crossfade Dissolve (8 frames)
  const opacity = interpolate(
    frame,
    [0, 8, item.durationFrames - 8, item.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Subtitle Spring Animation
  const subEntrance = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  return (
    <AbsoluteFill style={{ opacity }}>
      {/* Background Painting with Ken Burns Motion */}
      <AbsoluteFill style={{ overflow: "hidden" }}>
        <Img
          src={staticFile(item.imageSrc)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform,
          }}
        />
      </AbsoluteFill>

      {/* Cinematic Vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 48%, rgba(5, 5, 8, 0.58) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* Top Banner: Episode 7 Title Pill */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 0,
          right: 0,
          textAlign: "center",
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            display: "inline-block",
            padding: "10px 28px",
            backgroundColor: "rgba(10, 10, 15, 0.78)",
            border: "1.5px solid rgba(255, 215, 0, 0.7)",
            borderRadius: 30,
            backdropFilter: "blur(10px)",
            boxShadow: "0 4px 20px rgba(0,0,0,0.7)",
          }}
        >
          <span
            style={{
              color: "#FFD700",
              fontSize: 26,
              fontWeight: 800,
              fontFamily: "'Segoe UI', 'Mukta', sans-serif",
              letterSpacing: 2,
              textTransform: "uppercase",
              textShadow: "0 2px 8px rgba(0,0,0,0.8)",
            }}
          >
            रामायण • भाग ७ : मंथरा का षड्यंत्र एवं कैकेयी के दो वरदान
          </span>
        </div>
      </div>

      {/* Thematic Atmospheric VFX Layer */}
      {item.vfx === "deepotsav" && <DeepotsavVFX />}
      {item.vfx === "conspiracy" && <MidnightConspiracyVFX />}
      {item.vfx === "kopabhavan" && <KopabhavanVFX />}
      {item.vfx === "dasharatha_oath" && <DasharathaOathVFX />}
      {item.vfx === "vanvas_destiny" && <VanvasDestinyVFX />}
      {item.vfx === "heartbreak" && <HeartbreakGriefVFX />}
      {item.vfx === "surya_dharma" && <SuryaDharmaVFX />}

      {/* Synchronized Devanagari Hindi Subtitle Box */}
      <div
        style={{
          position: "absolute",
          bottom: 120,
          left: 40,
          right: 40,
          textAlign: "center",
          transform: `scale(${subEntrance})`,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            display: "inline-block",
            padding: "18px 32px",
            backgroundColor: "rgba(8, 8, 12, 0.88)",
            border: "2px solid #FFD700",
            borderRadius: 18,
            backdropFilter: "blur(12px)",
            boxShadow: "0 10px 30px rgba(0,0,0,0.9), 0 0 25px rgba(255,215,0,0.35)",
          }}
        >
          <span
            style={{
              color: "#FFFFFF",
              fontSize: 34,
              fontWeight: 700,
              lineHeight: 1.45,
              fontFamily: "'Segoe UI', 'Mukta', 'Noto Sans Devanagari', sans-serif",
              textShadow:
                "0 2px 4px rgba(0,0,0,0.95), 0 0 12px rgba(255,215,0,0.5)",
            }}
          >
            {item.subtitle}
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Episode 7 Scene List (2470 Frames @ 30 FPS = 82.323s)
// ---------------------------------------------------------------------------
const SCENES: SceneItem[] = [
  {
    id: 1,
    imageSrc: "ramayana-manthara-chakranta/scene_1.jpg",
    subtitle: "प्रभात होते ही श्री राम का राज्याभिषेक... पर महल में घिर रहा था अंधेरा!",
    startFrame: 0,
    durationFrames: 336,
    zoomDirection: "in",
    vfx: "deepotsav",
  },
  {
    id: 2,
    imageSrc: "ramayana-manthara-chakranta/scene_2.jpg",
    subtitle: "कुटिल मंथरा ने कैकेयी के कान में घोला ईर्ष्या का भयानक विष!",
    startFrame: 336,
    durationFrames: 384,
    zoomDirection: "pan-left",
    vfx: "conspiracy",
  },
  {
    id: 3,
    imageSrc: "ramayana-manthara-chakranta/scene_3.jpg",
    subtitle: "क्रोध में जलती कैकेयी ने आभूषण फेंक दिए... कोपभवन में हाहाकार!",
    startFrame: 720,
    durationFrames: 354,
    zoomDirection: "out",
    vfx: "kopabhavan",
  },
  {
    id: 4,
    imageSrc: "ramayana-manthara-chakranta/scene_4.jpg",
    subtitle: "महाराज दशरथ कांप उठे—'प्रिये बताओ, रघुकुल की शपथ जो मांगोगी दूंगा!'",
    startFrame: 1074,
    durationFrames: 401,
    zoomDirection: "in",
    vfx: "dasharatha_oath",
  },
  {
    id: 5,
    imageSrc: "ramayana-manthara-chakranta/scene_5.jpg",
    subtitle: "कैकेयी के दो सर्वनाशी वरदान—'भरत को राजगद्दी और राम को १४ वर्ष वनवास!'",
    startFrame: 1475,
    durationFrames: 314,
    zoomDirection: "pan-right",
    vfx: "vanvas_destiny",
  },
  {
    id: 6,
    imageSrc: "ramayana-manthara-chakranta/scene_6.jpg",
    subtitle: "दशरथ छाती पकड़कर गिर पड़े—'मेरे प्राण ले ले, पर राम को मत छीन!' 😭",
    startFrame: 1789,
    durationFrames: 344,
    zoomDirection: "in",
    vfx: "heartbreak",
  },
  {
    id: 7,
    imageSrc: "ramayana-manthara-chakranta/scene_7.jpg",
    subtitle: "अयोध्या पर छाई अभिशप्त कालरात्रि... कमेंट में लिखें 'जय श्री राम' 🚩",
    startFrame: 2133,
    durationFrames: 337,
    zoomDirection: "out",
    vfx: "surya_dharma",
  },
];

export const RamayanaEp7MantharaChakranta: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      {/* 7 Animated Scenes with Synchronized Devanagari Hindi Subtitles */}
      {SCENES.map((scene) => (
        <Sequence
          key={scene.id}
          from={scene.startFrame}
          durationInFrames={scene.durationFrames}
        >
          <SceneSlide item={scene} />
        </Sequence>
      ))}

      {/* Studio-Mastered Deep Storyteller Audio Narration + Drone Score */}
      <Audio src={staticFile("ramayana-manthara-chakranta/audio_mix_hindi.mp3")} />
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="RamayanaEp7MantharaChakranta"
      component={RamayanaEp7MantharaChakranta}
      durationInFrames={2470}
      fps={30}
      width={1080}
      height={1920}
    />
  );
};

registerRoot(RemotionRoot);
