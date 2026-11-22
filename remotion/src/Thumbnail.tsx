import { AbsoluteFill } from "remotion";
import { Icon } from "./icons";
import { Background } from "./layers/Background";
import { ACCENTS, DISPLAY, SANS, parseEmphasis } from "./theme";
import type { ThumbnailProps } from "./types";

export const Thumbnail: React.FC<ThumbnailProps> = ({ title, icon, handle }) => {
  const accent = ACCENTS[0];
  const accent2 = ACCENTS[1];
  const words = parseEmphasis(title);
  const size = words.length > 4 ? 118 : 138;
  return (
    <AbsoluteFill>
      <Background starts={[0]} accents={[accent]} frameOverride={40} />
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", padding: "0 70px", gap: 40 }}>
        <div style={{ flex: 1, display: "flex", flexWrap: "wrap", gap: "0 28px" }}>
          {words.map((w, i) => (
            <span
              key={i}
              style={{
                fontFamily: SANS,
                fontWeight: 900,
                fontSize: size,
                lineHeight: 1.0,
                letterSpacing: -4,
                textTransform: "uppercase",
                ...(w.em
                  ? {
                      backgroundImage: `linear-gradient(120deg, ${accent}, ${accent2})`,
                      WebkitBackgroundClip: "text",
                      color: "transparent",
                      filter: `drop-shadow(0 0 30px ${accent})`,
                    }
                  : { color: "white", WebkitTextStroke: "10px black", paintOrder: "stroke fill" }),
              }}
            >
              {w.word}
            </span>
          ))}
        </div>
        <div style={{ position: "relative", width: 380, height: 380, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ position: "absolute", inset: -60, borderRadius: "50%", background: `radial-gradient(circle, ${accent}88, transparent 70%)` }} />
          <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: `conic-gradient(${accent}, ${accent2}, ${accent})` }} />
          <div style={{ position: "absolute", inset: 12, borderRadius: "50%", background: "#0A0A14" }} />
          <div style={{ position: "relative", filter: `drop-shadow(0 0 30px ${accent})` }}>
            <Icon name={icon} size={200} color="white" strokeWidth={1.4} />
          </div>
        </div>
      </AbsoluteFill>
      {handle ? (
        <div style={{ position: "absolute", top: 28, right: 40, fontFamily: DISPLAY, fontWeight: 700, fontSize: 36, color: "rgba(255,255,255,0.8)" }}>{handle}</div>
      ) : null}
    </AbsoluteFill>
  );
};
