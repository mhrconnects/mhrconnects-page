import { AbsoluteFill } from "remotion";
import { Icon } from "./icons";
import { ACCENTS, DISPLAY, SANS } from "./theme";

export type AvatarProps = {
  variant: "monogram" | "icon" | "ai" | "minimal";
  text?: string;
  icon?: string;
  bg?: string;
  fg?: string;
  accent?: string;
  font?: "sans" | "grotesk";
  lower?: boolean;
};

/** Minimal flat monogram: one or two colours, lots of space, tiny accent dot. */
const Minimal: React.FC<AvatarProps> = ({ text = "MHR", bg = "#111113", fg = "#F5F3EE", accent = "#00D4FF", font = "sans", lower }) => (
  <AbsoluteFill style={{ background: bg, alignItems: "center", justifyContent: "center" }}>
    <div style={{ display: "flex", alignItems: "baseline" }}>
      <span
        style={{
          fontFamily: font === "grotesk" ? DISPLAY : SANS,
          fontWeight: font === "grotesk" ? 700 : 900,
          fontSize: lower ? 250 : 210,
          letterSpacing: lower ? -14 : -12,
          color: fg,
          lineHeight: 1,
        }}
      >
        {lower ? text.toLowerCase() : text}
      </span>
      <span style={{ width: 44, height: 44, borderRadius: 22, background: accent, marginLeft: 10 }} />
    </div>
  </AbsoluteFill>
);

/** Channel profile picture (800x800). Everything important stays inside the centre circle. */
export const Avatar: React.FC<AvatarProps> = (props) => {
  const { variant, text = "MHR", icon = "brain" } = props;
  if (variant === "minimal") return <Minimal {...props} />;
  const a = ACCENTS[0];
  const b = ACCENTS[1];
  return (
    <AbsoluteFill style={{ background: "#07070D", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
      <div style={{ position: "absolute", width: 900, height: 900, borderRadius: "50%", background: `radial-gradient(circle at 30% 25%, ${a}88, transparent 55%), radial-gradient(circle at 75% 80%, ${b}77, transparent 55%)` }} />
      <div style={{ position: "absolute", width: 640, height: 640, borderRadius: "50%", background: `conic-gradient(from 210deg, ${a}, ${b}, ${a})`, boxShadow: `0 0 80px ${a}aa` }} />
      <div style={{ position: "absolute", width: 608, height: 608, borderRadius: "50%", background: "radial-gradient(circle at 50% 35%, #16162A, #07070D 70%)" }} />
      <div style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
        {variant === "monogram" ? (
          <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 210, letterSpacing: -10, backgroundImage: `linear-gradient(120deg, ${a}, ${b})`, WebkitBackgroundClip: "text", color: "transparent", filter: `drop-shadow(0 0 30px ${a}99)` }}>
            {text}
          </div>
        ) : null}
        {variant === "icon" ? (
          <div style={{ filter: `drop-shadow(0 0 40px ${a})` }}>
            <Icon name={icon} size={330} color="white" strokeWidth={1.3} />
          </div>
        ) : null}
        {variant === "ai" ? (
          <>
            <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 290, lineHeight: 0.9, letterSpacing: -12, backgroundImage: `linear-gradient(120deg, ${a}, ${b})`, WebkitBackgroundClip: "text", color: "transparent", filter: `drop-shadow(0 0 30px ${a}99)` }}>
              AI
            </div>
            <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 66, letterSpacing: 14, color: "white", marginLeft: 14 }}>{text}</div>
          </>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
