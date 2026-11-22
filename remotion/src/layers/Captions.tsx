import { useMemo } from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { useLayout } from "../layout";
import { CLAMP, SANS, pop } from "../theme";
import type { Word } from "../types";

type Group = { words: Word[]; start: number; end: number };

/** Groups of up to 3 words, breaking after punctuation, like pro Shorts captions. */
const makeGroups = (words: Word[]): Group[] => {
  const groups: Group[] = [];
  let cur: Word[] = [];
  words.forEach((w, i) => {
    cur.push(w);
    const gap = words[i + 1] ? words[i + 1].start - w.end : 1;
    if (cur.length >= 3 || /[.,!?;:]$/.test(w.text) || gap > 0.35) {
      groups.push({ words: cur, start: cur[0].start, end: w.end });
      cur = [];
    }
  });
  if (cur.length) groups.push({ words: cur, start: cur[0].start, end: cur[cur.length - 1].end });
  return groups;
};

export const Captions: React.FC<{ words: Word[]; accentFor: (t: number) => string }> = ({ words, accentFor }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const L = useLayout();
  const t = frame / fps;
  const groups = useMemo(() => makeGroups(words), [words]);

  const gi = groups.findIndex((g, i) => t >= g.start && t < (groups[i + 1]?.start ?? g.end + 0.4));
  if (gi < 0) return null;
  const g = groups[gi];
  const accent = accentFor(t);
  const enter = pop(frame, fps, Math.round(g.start * fps), 12);

  return (
    <div
      style={{
        position: "absolute",
        top: L.captionTop,
        left: L.landscape ? 200 : 70,
        width: width - (L.landscape ? 400 : 140),
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: `0 ${L.captionSize * 0.4}px`,
        scale: interpolate(enter, [0, 1], [0.78, 1]),
        opacity: interpolate(enter, [0, 0.4], [0, 1], CLAMP),
        translate: `0px ${interpolate(enter, [0, 1], [30, 0])}px`,
      }}
    >
      {g.words.map((w, i) => {
        const active = t >= w.start && t < (g.words[i + 1]?.start ?? g.end + 0.4);
        const spoken = t >= w.start;
        return (
          <span
            key={i}
            style={{
              fontFamily: SANS,
              fontWeight: 900,
              fontSize: L.captionSize,
              lineHeight: 1.12,
              textTransform: "uppercase",
              letterSpacing: -1,
              color: active ? accent : "white",
              opacity: spoken ? 1 : 0.55,
              WebkitTextStroke: `${L.captionStroke}px rgba(0,0,0,0.85)`,
              paintOrder: "stroke fill",
              textShadow: active ? `0 0 40px ${accent}` : "0 8px 24px rgba(0,0,0,0.6)",
              scale: active ? 1.08 : 1,
              display: "inline-block",
            }}
          >
            {w.text.replace(/[.,;:]$/, "")}
          </span>
        );
      })}
    </div>
  );
};
