import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { useLayout } from "../layout";
import { CLAMP, DISPLAY } from "../theme";

/** Light sweep + flash on every scene cut. */
export const CutFlash: React.FC<{ starts: number[]; accents: string[] }> = ({ starts, accents }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const i = starts.findIndex((s, k) => k > 0 && frame >= s - 6 && frame < s + 12);
  if (i < 0) return null;
  const d = frame - starts[i];
  const sweep = interpolate(d, [-6, 12], [-1.2, 1.6], CLAMP);
  const flash = interpolate(d, [-2, 0, 8], [0, 0.28, 0], CLAMP);
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill style={{ backgroundColor: "white", opacity: flash, mixBlendMode: "overlay" }} />
      <div
        style={{
          position: "absolute",
          top: -height * 0.25,
          left: sweep * width,
          width: width * 0.35,
          height: height * 1.5,
          rotate: "18deg",
          background: `linear-gradient(90deg, transparent, ${accents[i]}AA, rgba(255,255,255,0.85), ${accents[i]}AA, transparent)`,
          filter: "blur(30px)",
          opacity: 0.55,
          mixBlendMode: "screen",
        }}
      />
    </AbsoluteFill>
  );
};

export const ProgressBar: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();
  const p = frame / Math.max(durationInFrames - 1, 1);
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width, height: 12, background: "rgba(255,255,255,0.08)" }}>
      <div
        style={{
          width: width * p,
          height: "100%",
          background: `linear-gradient(90deg, ${accent}, white)`,
          boxShadow: `0 0 24px ${accent}`,
          borderRadius: "0 6px 6px 0",
        }}
      />
    </div>
  );
};

export const Handle: React.FC<{ handle: string }> = ({ handle }) => {
  const { width } = useVideoConfig();
  const L = useLayout();
  return (
    <div
      style={{
        position: "absolute",
        bottom: L.handleBottom,
        width,
        textAlign: "center",
        fontFamily: DISPLAY,
        fontWeight: 500,
        fontSize: 40,
        color: "rgba(255,255,255,0.55)",
        letterSpacing: 2,
      }}
    >
      {handle}
    </div>
  );
};
