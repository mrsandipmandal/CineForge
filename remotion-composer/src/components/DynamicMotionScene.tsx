import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { resolveAsset } from "../lib/resolveAsset";
import { ParticleOverlay, type ParticleType } from "./ParticleOverlay";

/**
 * Deterministic pseudo-random helper for frame-independent rendering.
 */
function seededRandom(seed: number): number {
  const x = Math.sin(seed * 12.9898 + seed * 78.233) * 43758.5453;
  return x - Math.floor(x);
}

export interface DepthLayersConfig {
  background_scale_speed?: number;
  subject_scale_speed?: number;
  foreground_speed?: number;
  backgroundScaleSpeed?: number;
  subjectScaleSpeed?: number;
  foregroundSpeed?: number;
}

export interface CharacterDynamicsConfig {
  breathing?: boolean;
  breathing_cycle_sec?: number;
  breathingCycleSec?: number;
  eye_glint_flicker?: boolean;
  eyeGlintFlicker?: boolean;
  weapon_glow_pulse?: boolean;
  weaponGlowPulse?: boolean;
}

export interface ParticleFxConfig {
  type?: string;
  density?: number;
  turbulence?: number;
}

export interface CameraDynamicsConfig {
  rate?: number;
  shake_intensity?: number;
  shakeIntensity?: number;
  rack_focus_frames?: number;
  rackFocusFrames?: number;
  whip_pan?: boolean;
  whipPan?: boolean;
}

export interface DynamicMotionSceneProps {
  /** Scene identifier */
  id?: string;
  scene_id?: string;

  /** Primary image asset path or URL */
  image?: string;
  /** Image paths array (if multi-layer or sequential assets are provided) */
  images?: string[];

  /** Dedicated layer images for 2.5D separation */
  backgroundImage?: string;
  background_image?: string;
  subjectImage?: string;
  subject_image?: string;
  foregroundImage?: string;
  foreground_image?: string;

  /** Scene duration in seconds */
  sceneDurationSeconds?: number;
  duration_seconds?: number;

  /** Motion type identifier (e.g. 2.5d_parallax_pulse) */
  motionType?: string;
  motion_type?: string;

  /** Parallax scale and speed configurations */
  depthLayers?: DepthLayersConfig;
  depth_layers?: DepthLayersConfig;

  /** Character micro-motion parameters (breathing, eye glint, weapon glow) */
  characterDynamics?: CharacterDynamicsConfig;
  character_dynamics?: CharacterDynamicsConfig;

  /** Particle physics configuration or preset name */
  particleFx?: ParticleFxConfig | string;
  particle_fx?: ParticleFxConfig | string;

  /** Camera motion parameters (shake, rack focus, whip pan) */
  cameraDynamics?: CameraDynamicsConfig;
  camera_dynamics?: CameraDynamicsConfig;

  /** Narrative scene context */
  action?: string;
  mood?: string;

  /** Base scene background color */
  backgroundColor?: string;

  /** Whether to render cinematic vignette */
  vignette?: boolean;
}

// ---------------------------------------------------------------------------
// Procedural Particle Physics Engines
// ---------------------------------------------------------------------------

/**
 * Radiant Golden Embers:
 * Floating sparks with sinusoidal turbulence and glowing golden auras.
 */
const GoldenEmbersPhysics: React.FC<{ density: number; turbulence: number }> = ({
  density,
  turbulence,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const count = Math.max(10, Math.min(100, density));

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {Array.from({ length: count }, (_, i) => {
        const baseX = seededRandom(i * 17 + 1) * 100;
        const speed = 0.6 + seededRandom(i * 13 + 3) * 0.9;
        const phase = seededRandom(i * 19 + 5) * Math.PI * 2;
        const size = 3 + seededRandom(i * 23 + 7) * 7;

        const cycle = (frame / fps) * speed;
        // Float upwards from bottom (110%) to top (-10%)
        const yPercent = 110 - ((cycle * 30 + seededRandom(i * 31) * 120) % 125);
        const xOffset = Math.sin(cycle * turbulence * 2 + phase) * (18 * turbulence);
        const flicker = 0.45 + 0.55 * Math.sin(frame * 0.25 + phase);

        const colors = ["#FFD700", "#FFB300", "#FFA000", "#FFE082", "#FFF8E1"];
        const color = colors[i % colors.length];

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `calc(${baseX}% + ${xOffset}px)`,
              top: `${yPercent}%`,
              width: size,
              height: size,
              borderRadius: "50%",
              backgroundColor: color,
              opacity: flicker * 0.85,
              boxShadow: `0 0 ${size * 2.5}px ${size * 1.2}px ${color}`,
              filter: "blur(0.5px)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/**
 * Dark Palace Shadows:
 * Ominous, rolling ethereal smoke plumes and swirling dark silhouettes.
 */
const DarkPalaceShadowsPhysics: React.FC<{ density: number; turbulence: number }> = ({
  density,
  turbulence,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const count = Math.max(6, Math.min(25, Math.round(density * 0.5)));

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {Array.from({ length: count }, (_, i) => {
        const baseX = seededRandom(i * 11 + 2) * 100;
        const baseY = 20 + seededRandom(i * 29 + 4) * 70;
        const speed = 0.3 + seededRandom(i * 7 + 1) * 0.4;
        const phase = seededRandom(i * 17 + 8) * Math.PI * 2;

        const t = (frame / fps) * speed;
        const xDrift = Math.sin(t * turbulence + phase) * 25;
        const yDrift = Math.cos(t * 0.7 * turbulence + phase) * 18;
        const scale = 1.0 + Math.sin(t * 0.5 + phase) * 0.2;
        const opacity = 0.35 + 0.25 * Math.sin(t * 0.8 + phase);

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `calc(${baseX}% + ${xDrift}px)`,
              top: `calc(${baseY}% + ${yDrift}px)`,
              width: 480,
              height: 480,
              transform: `translate(-50%, -50%) scale(${scale})`,
              borderRadius: "50%",
              background:
                "radial-gradient(circle, rgba(8, 6, 14, 0.75) 0%, rgba(18, 12, 28, 0.45) 45%, transparent 75%)",
              opacity,
              filter: "blur(35px)",
              mixBlendMode: "multiply",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/**
 * Lightning Shockwaves:
 * Concentric divine electric shockwaves radiating from mythical weapons or cosmic clash.
 */
const LightningShockwavesPhysics: React.FC<{ density: number; turbulence: number }> = ({
  density,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cycleFrames = 48; // Shockwave fires periodically
  const cycleFrame = frame % cycleFrames;

  const ringScale = interpolate(cycleFrame, [0, 36], [0.1, 2.8], {
    extrapolateRight: "clamp",
  });
  const ringOpacity = interpolate(cycleFrame, [0, 8, 36], [0.95, 0.7, 0], {
    extrapolateRight: "clamp",
  });

  const flashOpacity =
    cycleFrame < 4
      ? interpolate(cycleFrame, [0, 2, 4], [0, 0.35, 0], {
          extrapolateRight: "clamp",
        })
      : 0;

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {/* Ambient flash */}
      {flashOpacity > 0 && (
        <AbsoluteFill
          style={{
            backgroundColor: "rgba(220, 245, 255, 1)",
            opacity: flashOpacity,
            mixBlendMode: "screen",
          }}
        />
      )}

      {/* Expanding shockwave ring */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "45%",
          width: 500,
          height: 500,
          marginLeft: -250,
          marginTop: -250,
          borderRadius: "50%",
          border: "4px solid rgba(0, 229, 255, 0.85)",
          boxShadow:
            "0 0 40px rgba(0, 229, 255, 0.8), inset 0 0 30px rgba(255, 235, 59, 0.6)",
          transform: `scale(${ringScale})`,
          opacity: ringOpacity,
          filter: "blur(1px)",
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Main DynamicMotionScene Component
// ---------------------------------------------------------------------------

export const DynamicMotionScene: React.FC<DynamicMotionSceneProps> = ({
  image,
  images,
  backgroundImage,
  background_image,
  subjectImage,
  subject_image,
  foregroundImage,
  foreground_image,
  sceneDurationSeconds,
  duration_seconds,
  motionType = "2.5d_parallax_pulse",
  motion_type,
  depthLayers,
  depth_layers,
  characterDynamics,
  character_dynamics,
  particleFx,
  particle_fx,
  cameraDynamics,
  camera_dynamics,
  backgroundColor = "#07090E",
  vignette = true,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Resolve scene duration correctly
  const durSec =
    sceneDurationSeconds ?? duration_seconds ?? (durationInFrames / fps);
  const effectiveDuration = Math.max(1, Math.round(durSec * fps));

  // Normalise configurations from snake_case or camelCase
  const dl = depthLayers ?? depth_layers ?? {};
  const bgScaleSpeed = dl.background_scale_speed ?? dl.backgroundScaleSpeed ?? 1.05;
  const subjScaleSpeed = dl.subject_scale_speed ?? dl.subjectScaleSpeed ?? 1.15;
  const fgSpeed = dl.foreground_speed ?? dl.foregroundSpeed ?? 1.35;

  const cd = characterDynamics ?? character_dynamics ?? {};
  const breathing = cd.breathing ?? true;
  const breathingCycleSec = cd.breathing_cycle_sec ?? cd.breathingCycleSec ?? 3.2;
  const eyeGlintFlicker = cd.eye_glint_flicker ?? cd.eyeGlintFlicker ?? true;
  const weaponGlowPulse = cd.weapon_glow_pulse ?? cd.weaponGlowPulse ?? true;

  const cam = cameraDynamics ?? camera_dynamics ?? {};
  const rate = cam.rate ?? 1.2;
  const shakeIntensity = cam.shake_intensity ?? cam.shakeIntensity ?? 0.0;
  const rackFocusFrames = cam.rack_focus_frames ?? cam.rackFocusFrames ?? 12;
  const whipPan = cam.whip_pan ?? cam.whipPan ?? false;

  // Determine particle type and parameters
  let pType = "golden_embers";
  let pDensity = 35;
  let pTurbulence = 1.2;

  const pConfig = particleFx ?? particle_fx;
  if (typeof pConfig === "string" && pConfig.trim()) {
    pType = pConfig.trim();
  } else if (pConfig && typeof pConfig === "object") {
    pType = pConfig.type ?? "golden_embers";
    pDensity = pConfig.density ?? 35;
    pTurbulence = pConfig.turbulence ?? 1.2;
  }

  // Linear progression normalized over effective duration
  const progress = interpolate(frame, [0, effectiveDuration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Layer 1: Background Parallax Transform
  const bgScale = interpolate(progress, [0, 1], [1.0, bgScaleSpeed]);
  const bgTranslateY = interpolate(progress, [0, 1], [0, -18 * rate]);
  const bgTranslateX = interpolate(progress, [0, 1], [0, 12 * rate]);

  // Layer 2: Subject Parallax & Micro-Motion Transform
  const subjBaseScale = interpolate(progress, [0, 1], [1.02, subjScaleSpeed]);
  const subjTranslateY = interpolate(progress, [0, 1], [4 * rate, -30 * rate]);
  const subjTranslateX = interpolate(progress, [0, 1], [-10 * rate, 18 * rate]);

  // Sinusoidal Character Breathing Expansion: scale(1 + sin(frame * 0.05) * 0.015)
  const breathingScale = breathing ? 1 + Math.sin(frame * 0.05) * 0.015 : 1;
  const breathingOffsetY = breathing ? Math.sin(frame * 0.05) * 3 : 0;

  const finalSubjScale = subjBaseScale * breathingScale;
  const finalSubjY = subjTranslateY + breathingOffsetY;

  // Layer 3: Foreground Parallax Transform
  const fgScale = interpolate(progress, [0, 1], [1.04, fgSpeed]);
  const fgTranslateY = interpolate(progress, [0, 1], [10 * rate, -50 * rate]);
  const fgTranslateX = interpolate(progress, [0, 1], [-15 * rate, 25 * rate]);

  // Camera Dynamics: Rack focus blur on scene entrance
  const rackBlur =
    rackFocusFrames > 0
      ? interpolate(frame, [0, rackFocusFrames], [5.0, 0.0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 0.0;

  // Camera Dynamics: Shake intensity
  const shakeX =
    shakeIntensity > 0 ? Math.sin(frame * 0.75) * shakeIntensity * 12 : 0;
  const shakeY =
    shakeIntensity > 0 ? Math.cos(frame * 0.85) * shakeIntensity * 8 : 0;

  // Camera Dynamics: Whip pan entrance
  const whipPanX = whipPan
    ? interpolate(frame, [0, 8], [120, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 0;

  // Resolve Layer Assets
  const bgSrc =
    backgroundImage ??
    background_image ??
    image ??
    (images && images.length > 0 ? images[0] : "");

  const subjSrc =
    subjectImage ??
    subject_image ??
    (images && images.length > 1 ? images[1] : bgSrc);

  const fgSrc = foregroundImage ?? foreground_image;

  // Eye glint & weapon glow flicker intensities
  const glintAlpha = eyeGlintFlicker
    ? 0.35 + 0.65 * Math.abs(Math.sin(frame * 0.18))
    : 0;

  const weaponGlowAlpha = weaponGlowPulse
    ? 0.3 + 0.5 * Math.sin(frame * 0.09)
    : 0;

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        backgroundColor,
        width: 1080,
        height: 1920,
      }}
    >
      {/* Root transform container holding camera shake and rack focus blur */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          transform: `translate(${shakeX + whipPanX}px, ${shakeY}px)`,
          filter: rackBlur > 0.05 ? `blur(${rackBlur}px)` : undefined,
        }}
      >
        {/* Layer 1: Background Depth Layer */}
        {bgSrc && (
          <AbsoluteFill
            style={{
              transform: `scale(${bgScale}) translate(${bgTranslateX}px, ${bgTranslateY}px)`,
              transformOrigin: "center center",
            }}
          >
            <Img
              src={resolveAsset(bgSrc)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                filter: "brightness(0.92) contrast(1.05)",
              }}
            />
          </AbsoluteFill>
        )}

        {/* Ambient Depth Gradient between Background and Subject */}
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(ellipse at 50% 50%, rgba(10,12,20,0.1) 0%, rgba(5,6,12,0.45) 100%)",
            pointerEvents: "none",
          }}
        />

        {/* Layer 2: Midground Subject Layer with Micro-motion Breathing */}
        {subjSrc && (
          <AbsoluteFill
            style={{
              transform: `scale(${finalSubjScale}) translate(${subjTranslateX}px, ${finalSubjY}px)`,
              transformOrigin: "center 60%",
            }}
          >
            <Img
              src={resolveAsset(subjSrc)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                filter: "drop-shadow(0 15px 35px rgba(0,0,0,0.65))",
              }}
            />

            {/* Weapon Glow Aura */}
            {weaponGlowPulse && (
              <div
                style={{
                  position: "absolute",
                  left: "50%",
                  top: "45%",
                  width: "60%",
                  height: "60%",
                  transform: "translate(-50%, -50%)",
                  borderRadius: "50%",
                  background:
                    "radial-gradient(circle, rgba(255,215,0,0.28) 0%, rgba(255,140,0,0.12) 50%, transparent 80%)",
                  opacity: weaponGlowAlpha,
                  mixBlendMode: "screen",
                  pointerEvents: "none",
                }}
              />
            )}

            {/* Eye Glint Shimmer Effect */}
            {eyeGlintFlicker && (
              <div
                style={{
                  position: "absolute",
                  left: "50%",
                  top: "35%",
                  width: 24,
                  height: 24,
                  transform: "translate(-50%, -50%)",
                  borderRadius: "50%",
                  backgroundColor: "rgba(255, 255, 255, 0.95)",
                  boxShadow:
                    "0 0 16px 8px rgba(255, 235, 150, 0.9), 0 0 32px 16px rgba(255, 200, 50, 0.5)",
                  opacity: glintAlpha,
                  pointerEvents: "none",
                }}
              />
            )}
          </AbsoluteFill>
        )}

        {/* Layer 3: Foreground Overlay Asset (if specified) */}
        {fgSrc && (
          <AbsoluteFill
            style={{
              transform: `scale(${fgScale}) translate(${fgTranslateX}px, ${fgTranslateY}px)`,
              transformOrigin: "center center",
              pointerEvents: "none",
            }}
          >
            <Img
              src={resolveAsset(fgSrc)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                opacity: 0.85,
              }}
            />
          </AbsoluteFill>
        )}

        {/* Procedural Particle Dynamics Engine */}
        {pType === "golden_embers" && (
          <GoldenEmbersPhysics density={pDensity} turbulence={pTurbulence} />
        )}
        {pType === "dark_palace_shadows" && (
          <DarkPalaceShadowsPhysics density={pDensity} turbulence={pTurbulence} />
        )}
        {pType === "lightning_shockwaves" && (
          <LightningShockwavesPhysics density={pDensity} turbulence={pTurbulence} />
        )}

        {/* Fallback to standard ParticleOverlay for other particle types */}
        {["fireflies", "petals", "sparkles", "mist", "light-rays"].includes(pType) && (
          <ParticleOverlay
            type={pType as ParticleType}
            count={pDensity}
            intensity={0.7}
          />
        )}

        {/* Cinematic Vignette */}
        {vignette && (
          <AbsoluteFill
            style={{
              background:
                "radial-gradient(ellipse at center, transparent 40%, rgba(2, 3, 7, 0.65) 100%)",
              pointerEvents: "none",
            }}
          />
        )}
      </div>
    </AbsoluteFill>
  );
};
