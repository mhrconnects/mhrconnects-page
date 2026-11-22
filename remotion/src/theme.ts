import { Easing, spring } from "remotion";
import "./fonts";

export const BG = "#05050A";
export const ACCENTS = ["#8B5CFF", "#00D4FF", "#FF4D8D", "#FFB020", "#2DFFA3"];
export const accentAt = (i: number) => ACCENTS[((i % ACCENTS.length) + ACCENTS.length) % ACCENTS.length];
export const nextAccent = (i: number) => accentAt(i + 1);

export const SANS = "'Inter', system-ui, sans-serif";
export const DISPLAY = "'Space Grotesk', 'Inter', system-ui, sans-serif";

export const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
export const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1);

/** Springy 0 -> 1 starting at `delay` frames. */
export const pop = (frame: number, fps: number, delay = 0, damping = 13) =>
  spring({ frame: frame - delay, fps, config: { damping, stiffness: 140, mass: 0.7 } });

/** Smooth 0 -> 1 starting at `delay` frames. */
export const glide = (frame: number, fps: number, delay = 0) =>
  spring({ frame: frame - delay, fps, config: { damping: 200 } });

export const glass: React.CSSProperties = {
  background: "linear-gradient(135deg, rgba(30,30,48,0.82), rgba(12,12,22,0.72))",
  border: "1.5px solid rgba(255,255,255,0.16)",
  boxShadow: "0 30px 80px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.15)",
};

/** Split "Learn *tokens* fast" into words, flagging the emphasised ones. */
export const parseEmphasis = (text: string) =>
  text
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => ({ word: w.replace(/\*/g, ""), em: /\*/.test(w) }));

export const stripEmphasis = (text: string) => text.replace(/\*/g, "");
