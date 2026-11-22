import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { CLAMP, DISPLAY, SANS, glide, parseEmphasis, pop } from "../theme";

export type SceneProps = {
  title: string;
  subtitle?: string;
  items?: string[];
  icon?: string;
  number?: string;
  accent: string;
  accent2: string;
};

/** Content area above the captions. Adds a slow camera push and an exit blur on every scene. */
export const Stage: React.FC<{ children: React.ReactNode; align?: "center" | "start" }> = ({ children, align = "center" }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const out = interpolate(frame, [durationInFrames - 8, durationInFrames], [0, 1], CLAMP);
  return (
    <div
      style={{
        position: "absolute",
        top: 170,
        left: 80,
        right: 80,
        height: 1060,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: align === "center" ? "center" : "flex-start",
        gap: 40,
        scale: interpolate(frame, [0, durationInFrames], [1, 1.045]) - out * 0.06,
        opacity: 1 - out,
        filter: `blur(${out * 14}px)`,
      }}
    >
      {children}
    </div>
  );
};

/** Big title whose words slam in one by one. *Emphasised* words get an accent gradient. */
export const KineticTitle: React.FC<{
  text: string; accent: string; accent2: string; size?: number; delay?: number; stagger?: number; align?: "center" | "left";
}> = ({ text, accent, accent2, size = 120, delay = 0, stagger = 4, align = "center" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = parseEmphasis(text);
  return (
    <div style={{ display: "flex", flexWrap: "wrap", justifyContent: align === "center" ? "center" : "flex-start", gap: `0 ${size * 0.26}px` }}>
      {words.map((w, i) => {
        const p = pop(frame, fps, delay + i * stagger, 11);
        return (
          <span
            key={i}
            style={{
              fontFamily: SANS,
              fontWeight: 900,
              fontSize: size,
              lineHeight: 1.02,
              letterSpacing: -size * 0.03,
              display: "inline-block",
              opacity: interpolate(p, [0, 0.3], [0, 1], CLAMP),
              translate: `0px ${interpolate(p, [0, 1], [size * 0.7, 0])}px`,
              scale: interpolate(p, [0, 1], [1.5, 1]),
              filter: `blur(${interpolate(p, [0, 1], [14, 0], CLAMP)}px)`,
              color: "white",
              ...(w.em
                ? {
                    backgroundImage: `linear-gradient(120deg, ${accent} 10%, ${accent2} 90%)`,
                    WebkitBackgroundClip: "text",
                    backgroundClip: "text",
                    color: "transparent",
                    filter: `drop-shadow(0 0 30px ${accent}99) blur(${interpolate(p, [0, 1], [14, 0], CLAMP)}px)`,
                  }
                : { textShadow: "0 10px 40px rgba(0,0,0,0.5)" }),
            }}
          >
            {w.word}
          </span>
        );
      })}
    </div>
  );
};

/** Small glowing pill label, e.g. "KEY TERM". */
export const Chip: React.FC<{ text: string; accent: string; delay?: number }> = ({ text, accent, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = glide(frame, fps, delay);
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        padding: "14px 30px",
        borderRadius: 999,
        border: `2px solid ${accent}`,
        background: `${accent}22`,
        boxShadow: `0 0 40px ${accent}55`,
        fontFamily: DISPLAY,
        fontWeight: 700,
        fontSize: 36,
        letterSpacing: 5,
        color: "white",
        textTransform: "uppercase",
        opacity: p,
        translate: `0px ${interpolate(p, [0, 1], [-30, 0])}px`,
      }}
    >
      <div style={{ width: 16, height: 16, borderRadius: 8, background: accent, boxShadow: `0 0 16px ${accent}`, opacity: 0.6 + 0.4 * Math.sin(frame / 4) }} />
      {text}
    </div>
  );
};

/** Words fade up one after another between `start` and `start + duration` frames. */
export const RevealText: React.FC<{
  text: string; start: number; duration: number; size?: number; weight?: number; color?: string; align?: "center" | "left";
}> = ({ text, start, duration, size = 52, weight = 600, color = "rgba(255,255,255,0.88)", align = "center" }) => {
  const frame = useCurrentFrame();
  const words = text.split(/\s+/).filter(Boolean);
  const per = duration / Math.max(words.length, 1);
  return (
    <div style={{ display: "flex", flexWrap: "wrap", justifyContent: align === "center" ? "center" : "flex-start", gap: `0 ${size * 0.28}px` }}>
      {words.map((w, i) => {
        const p = interpolate(frame, [start + i * per, start + i * per + 8], [0, 1], CLAMP);
        return (
          <span
            key={i}
            style={{
              fontFamily: SANS,
              fontWeight: weight,
              fontSize: size,
              lineHeight: 1.3,
              color,
              opacity: p,
              translate: `0px ${(1 - p) * 18}px`,
              display: "inline-block",
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};

/** Expanding ring shockwave. */
export const Shockwave: React.FC<{ accent: string; delay?: number; size?: number }> = ({ accent, delay = 0, size = 700 }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [delay, delay + 28], [0, 1], { ...CLAMP, easing: (x) => 1 - (1 - x) ** 3 });
  if (p <= 0 || p >= 1) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: "50%",
        marginLeft: -size / 2,
        marginTop: -size / 2,
        width: size,
        height: size,
        borderRadius: "50%",
        border: `${interpolate(p, [0, 1], [18, 1])}px solid ${accent}`,
        scale: interpolate(p, [0, 1], [0.1, 1.8]),
        opacity: 1 - p,
        boxShadow: `0 0 60px ${accent}`,
      }}
    />
  );
};
