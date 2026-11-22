import { Bell, ChevronsDown } from "lucide-react";
import { Audio } from "@remotion/media";
import { Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Icon } from "../icons";
import { CLAMP, DISPLAY, SANS, glass, glide, pop, stripEmphasis } from "../theme";
import { Chip, KineticTitle, RevealText, SceneProps, Shockwave, Stage } from "./common";

const Pop: React.FC<{ at: number; sfx: boolean }> = ({ at, sfx }) =>
  sfx ? (
    <Sequence from={at} durationInFrames={20} layout="none">
      <Audio src={staticFile("sfx/pop.wav")} volume={0.35} />
    </Sequence>
  ) : null;

/* ---------------------------------------------------------------- HOOK */
export const HookScene: React.FC<SceneProps> = ({ title, subtitle, accent, accent2 }) => {
  return (
    <Stage>
      <Shockwave accent={accent} delay={2} size={800} />
      <Shockwave accent={accent2} delay={9} size={800} />
      <KineticTitle text={title} accent={accent} accent2={accent2} size={138} stagger={5} />
      {subtitle ? <Chip text={subtitle} accent={accent} delay={16} /> : null}
    </Stage>
  );
};

/* ---------------------------------------------------------------- CONCEPT */
export const ConceptScene: React.FC<SceneProps> = ({ title, subtitle, icon, accent, accent2 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const p = pop(frame, fps, 0, 10);
  return (
    <Stage>
      <Chip text="Key term" accent={accent} delay={0} />
      <div style={{ position: "relative", width: 380, height: 380, display: "flex", alignItems: "center", justifyContent: "center", scale: p, rotate: `${interpolate(p, [0, 1], [-25, 0])}deg` }}>
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            background: `conic-gradient(from ${frame * 3}deg, ${accent}, transparent 30%, ${accent2}, transparent 70%, ${accent})`,
            filter: "blur(2px)",
          }}
        />
        <div style={{ position: "absolute", inset: 10, borderRadius: "50%", background: "#0A0A14" }} />
        <div style={{ position: "absolute", inset: -40, borderRadius: "50%", background: `radial-gradient(circle, ${accent}55, transparent 70%)` }} />
        <div style={{ position: "relative", translate: `0px ${Math.sin(frame / 12) * 8}px`, filter: `drop-shadow(0 0 24px ${accent})` }}>
          <Icon name={icon} size={190} color="white" strokeWidth={1.4} />
        </div>
      </div>
      <KineticTitle text={title} accent={accent} accent2={accent2} size={112} delay={8} />
      {subtitle ? <RevealText text={subtitle} start={18} duration={Math.max(durationInFrames * 0.45, 20)} /> : null}
    </Stage>
  );
};

/* ---------------------------------------------------------------- LIST */
export const ListScene: React.FC<SceneProps & { sfx: boolean }> = ({ title, items = [], accent, accent2, sfx }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const n = Math.max(items.length, 1);
  const spread = durationInFrames * 0.62;
  const at = (i: number) => Math.round(14 + (i * spread) / n);
  const latest = items.reduce((acc, _, i) => (frame >= at(i) ? i : acc), -1);
  return (
    <Stage align="start">
      <KineticTitle text={title} accent={accent} accent2={accent2} size={92} />
      <div style={{ display: "flex", flexDirection: "column", gap: 30, width: "100%", marginTop: 20 }}>
        {items.map((item, i) => {
          const p = pop(frame, fps, at(i), 14);
          const active = i === latest;
          return (
            <div
              key={i}
              style={{
                ...glass,
                display: "flex",
                alignItems: "center",
                gap: 34,
                padding: "34px 40px",
                borderRadius: 34,
                opacity: interpolate(p, [0, 0.3], [0, 1], CLAMP) * (active ? 1 : 0.62),
                translate: `${interpolate(p, [0, 1], [160, 0])}px 0px`,
                scale: active ? 1.03 : 1,
                border: active ? `2px solid ${accent}` : glass.border,
                boxShadow: active ? `0 0 60px ${accent}55, ${glass.boxShadow}` : glass.boxShadow,
              }}
            >
              <Pop at={at(i)} sfx={sfx} />
              <div
                style={{
                  minWidth: 92,
                  height: 92,
                  borderRadius: 26,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: `linear-gradient(135deg, ${accent}, ${accent2})`,
                  fontFamily: DISPLAY,
                  fontWeight: 700,
                  fontSize: 50,
                  color: "white",
                  boxShadow: `0 10px 30px ${accent}66`,
                }}
              >
                {i + 1}
              </div>
              <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 54, color: "white", lineHeight: 1.15 }}>{stripEmphasis(item)}</div>
            </div>
          );
        })}
      </div>
    </Stage>
  );
};

/* ---------------------------------------------------------------- COMPARE */
const splitItem = (s: string) => {
  const [label, ...rest] = s.split(":");
  return { label: label.trim(), detail: rest.join(":").trim() };
};

export const CompareScene: React.FC<SceneProps & { sfx: boolean }> = ({ title, items = [], accent, accent2, sfx }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const a = splitItem(items[0] ?? "Before: ");
  const b = splitItem(items[1] ?? "After: ");
  const tA = 12;
  const tB = Math.round(durationInFrames * 0.4);
  const pA = pop(frame, fps, tA, 14);
  const pB = pop(frame, fps, tB, 14);
  const vs = pop(frame, fps, tB - 6, 8);
  const card = (side: { label: string; detail: string }, p: number, from: number, good: boolean): React.ReactNode => (
    <div
      style={{
        ...glass,
        width: "100%",
        padding: "40px 46px",
        borderRadius: 40,
        opacity: interpolate(p, [0, 0.3], [0, 1], CLAMP),
        translate: `${interpolate(p, [0, 1], [from, 0])}px 0px`,
        border: good ? `2px solid ${accent}` : "2px solid rgba(255,90,90,0.5)",
        boxShadow: good ? `0 0 70px ${accent}44, ${glass.boxShadow}` : glass.boxShadow,
      }}
    >
      <div style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 40, letterSpacing: 4, textTransform: "uppercase", color: good ? accent : "#FF7A7A" }}>
        {good ? "✓ " : "✕ "}
        {side.label}
      </div>
      <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 56, color: "white", marginTop: 14, lineHeight: 1.15 }}>{side.detail}</div>
    </div>
  );
  return (
    <Stage>
      <KineticTitle text={title} accent={accent} accent2={accent2} size={92} />
      <Pop at={tA} sfx={sfx} />
      <Pop at={tB} sfx={sfx} />
      {card(a, pA, -200, false)}
      <div
        style={{
          width: 120,
          height: 120,
          borderRadius: 60,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: `linear-gradient(135deg, ${accent}, ${accent2})`,
          fontFamily: DISPLAY,
          fontWeight: 700,
          fontSize: 48,
          color: "white",
          scale: vs,
          rotate: `${interpolate(vs, [0, 1], [-90, 0])}deg`,
          boxShadow: `0 0 50px ${accent}`,
          margin: "-30px 0",
          zIndex: 2,
        }}
      >
        VS
      </div>
      {card(b, pB, 200, true)}
    </Stage>
  );
};

/* ---------------------------------------------------------------- FLOW */
export const FlowScene: React.FC<SceneProps & { sfx: boolean }> = ({ title, items = [], accent, accent2, sfx }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const n = Math.max(items.length, 1);
  const step = (durationInFrames * 0.6) / n;
  const at = (i: number) => Math.round(12 + i * step);
  const NODE = 128;
  const GAP = 70;
  const total = n * NODE + (n - 1) * GAP;
  const drawn = interpolate(frame, [at(0), at(n - 1)], [0, 1], CLAMP);
  const pulse = ((frame - at(n - 1)) % 45) / 45;
  return (
    <Stage align="start">
      <KineticTitle text={title} accent={accent} accent2={accent2} size={92} />
      <div style={{ position: "relative", width: "100%", height: total, marginTop: 30 }}>
        {/* connector track + animated fill */}
        <div style={{ position: "absolute", left: 64, top: NODE / 2, width: 8, height: total - NODE, background: "rgba(255,255,255,0.1)", borderRadius: 4 }} />
        <div
          style={{
            position: "absolute",
            left: 64,
            top: NODE / 2,
            width: 8,
            height: (total - NODE) * drawn,
            background: `linear-gradient(${accent}, ${accent2})`,
            borderRadius: 4,
            boxShadow: `0 0 24px ${accent}`,
          }}
        />
        {frame > at(n - 1) ? (
          <div
            style={{
              position: "absolute",
              left: 52,
              top: NODE / 2 + (total - NODE) * pulse - 16,
              width: 32,
              height: 32,
              borderRadius: 16,
              background: "white",
              boxShadow: `0 0 30px 10px ${accent}`,
            }}
          />
        ) : null}
        {items.map((item, i) => {
          const p = pop(frame, fps, at(i), 12);
          return (
            <div key={i} style={{ position: "absolute", top: i * (NODE + GAP), left: 0, right: 0, height: NODE, display: "flex", alignItems: "center", gap: 36 }}>
              <Pop at={at(i)} sfx={sfx} />
              <div
                style={{
                  width: NODE + 8,
                  height: NODE,
                  borderRadius: NODE / 2,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: `linear-gradient(135deg, ${accent}, ${accent2})`,
                  scale: p,
                  boxShadow: `0 0 40px ${accent}88`,
                  fontFamily: DISPLAY,
                  fontWeight: 700,
                  fontSize: 54,
                  color: "white",
                }}
              >
                {i + 1}
              </div>
              <div
                style={{
                  ...glass,
                  flex: 1,
                  padding: "26px 36px",
                  borderRadius: 30,
                  fontFamily: SANS,
                  fontWeight: 800,
                  fontSize: 52,
                  color: "white",
                  opacity: interpolate(p, [0, 0.3], [0, 1], CLAMP),
                  translate: `${interpolate(p, [0, 1], [120, 0])}px 0px`,
                }}
              >
                {stripEmphasis(item)}
              </div>
            </div>
          );
        })}
      </div>
    </Stage>
  );
};

/* ---------------------------------------------------------------- STAT */
export const StatScene: React.FC<SceneProps> = ({ title, subtitle, number = "100%", accent, accent2 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const m = number.match(/^([^0-9]*)([0-9][0-9.,]*)(.*)$/);
  const prefix = m?.[1] ?? "";
  const raw = m?.[2] ?? "";
  const suffix = m ? m[3] : number;
  const target = parseFloat(raw.replace(/,/g, "")) || 0;
  const decimals = raw.includes(".") ? raw.split(".")[1].length : 0;
  const prog = interpolate(frame, [6, 40], [0, 1], { ...CLAMP, easing: (x) => 1 - (1 - x) ** 4 });
  const shown = m
    ? (target * prog).toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals, useGrouping: raw.includes(",") })
    : "";
  const R = 300;
  const C = 2 * Math.PI * R;
  const ring = pop(frame, fps, 0, 18);
  return (
    <Stage>
      <KineticTitle text={title} accent={accent} accent2={accent2} size={84} />
      <div style={{ position: "relative", width: 2 * R + 60, height: 2 * R + 60, display: "flex", alignItems: "center", justifyContent: "center", scale: ring }}>
        <svg width={2 * R + 60} height={2 * R + 60} style={{ position: "absolute", rotate: "-90deg" }}>
          <defs>
            <linearGradient id="ringG" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={accent} />
              <stop offset="100%" stopColor={accent2} />
            </linearGradient>
          </defs>
          <circle cx={R + 30} cy={R + 30} r={R} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={26} />
          <circle
            cx={R + 30}
            cy={R + 30}
            r={R}
            fill="none"
            stroke="url(#ringG)"
            strokeWidth={26}
            strokeLinecap="round"
            strokeDasharray={C}
            strokeDashoffset={C * (1 - prog)}
            style={{ filter: `drop-shadow(0 0 18px ${accent})` }}
          />
        </svg>
        <div
          style={{
            fontFamily: SANS,
            fontWeight: 900,
            fontSize: Math.min(210, 780 / Math.max(number.length, 3)),
            letterSpacing: -6,
            color: "white",
            textShadow: `0 0 60px ${accent}`,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {m ? `${prefix}${shown}${suffix}` : number}
        </div>
      </div>
      {subtitle ? <RevealText text={subtitle} start={20} duration={25} size={50} /> : null}
    </Stage>
  );
};

/* ---------------------------------------------------------------- CHAT */
export const ChatScene: React.FC<SceneProps> = ({ title, items = [], accent, accent2 }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const user = items[0] ?? "";
  const ai = items[1] ?? "";
  const typeEnd = 10 + Math.min(user.length * 0.9, 45);
  const typed = user.slice(0, Math.floor(interpolate(frame, [10, typeEnd], [0, user.length], CLAMP)));
  const thinkEnd = typeEnd + 16;
  const win = pop(frame, fps, 0, 16);
  const aiIn = glide(frame, fps, thinkEnd);
  return (
    <Stage align="start">
      <Chip text={stripEmphasis(title)} accent={accent} />
      <div
        style={{
          ...glass,
          width: "100%",
          borderRadius: 44,
          overflow: "hidden",
          scale: interpolate(win, [0, 1], [0.85, 1]),
          opacity: win,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "26px 34px", borderBottom: "1.5px solid rgba(255,255,255,0.12)" }}>
          {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => (
            <div key={c} style={{ width: 22, height: 22, borderRadius: 11, background: c }} />
          ))}
          <div style={{ marginLeft: 20, fontFamily: DISPLAY, fontWeight: 500, fontSize: 34, color: "rgba(255,255,255,0.7)" }}>AI chat</div>
        </div>
        <div style={{ padding: 40, display: "flex", flexDirection: "column", gap: 34 }}>
          <div
            style={{
              alignSelf: "flex-end",
              maxWidth: "88%",
              padding: "28px 34px",
              borderRadius: "34px 34px 8px 34px",
              background: `linear-gradient(135deg, ${accent}, ${accent2})`,
              fontFamily: SANS,
              fontWeight: 600,
              fontSize: 44,
              lineHeight: 1.3,
              color: "white",
              minHeight: 60,
            }}
          >
            {typed}
            {frame < typeEnd ? <span style={{ opacity: Math.round(frame / 6) % 2 }}>|</span> : null}
          </div>
          {frame >= typeEnd && frame < thinkEnd ? (
            <div style={{ display: "flex", gap: 14, padding: "28px 34px", alignSelf: "flex-start", ...glass, borderRadius: 30 }}>
              {[0, 1, 2].map((d) => (
                <div key={d} style={{ width: 20, height: 20, borderRadius: 10, background: "white", opacity: 0.3 + 0.7 * Math.abs(Math.sin((frame - d * 4) / 5)) }} />
              ))}
            </div>
          ) : null}
          {frame >= thinkEnd ? (
            <div
              style={{
                alignSelf: "flex-start",
                maxWidth: "92%",
                padding: "30px 34px",
                borderRadius: "34px 34px 34px 8px",
                background: "rgba(255,255,255,0.08)",
                border: "1.5px solid rgba(255,255,255,0.14)",
                opacity: aiIn,
                translate: `0px ${(1 - aiIn) * 30}px`,
              }}
            >
              <RevealText text={ai} start={thinkEnd} duration={Math.max(durationInFrames - thinkEnd - 20, 15)} size={42} weight={500} align="left" />
            </div>
          ) : null}
        </div>
      </div>
    </Stage>
  );
};

/* ---------------------------------------------------------------- CTA */
export const CtaScene: React.FC<SceneProps & { handle?: string }> = ({ title, subtitle, accent, accent2, handle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const btn = pop(frame, fps, 14, 9);
  return (
    <Stage>
      <div style={{ rotate: `${Math.sin(frame / 2.5) * 14 * Math.max(0, 1 - frame / 40)}deg`, filter: `drop-shadow(0 0 30px ${accent})`, scale: pop(frame, fps, 0, 10) }}>
        <Bell size={170} color="white" strokeWidth={1.5} />
      </div>
      <KineticTitle text={title} accent={accent} accent2={accent2} size={110} delay={4} />
      <div
        style={{
          padding: "34px 90px",
          borderRadius: 999,
          background: `linear-gradient(135deg, ${accent}, ${accent2})`,
          fontFamily: DISPLAY,
          fontWeight: 700,
          fontSize: 64,
          letterSpacing: 6,
          color: "white",
          scale: btn * (1 + 0.04 * Math.sin(frame / 5)),
          boxShadow: `0 0 ${50 + 30 * Math.sin(frame / 5)}px ${accent}`,
        }}
      >
        FOLLOW
      </div>
      {subtitle || handle ? <RevealText text={subtitle || handle || ""} start={22} duration={14} size={46} /> : null}
      <div style={{ translate: `0px ${Math.abs(Math.sin(frame / 6)) * 24}px`, opacity: interpolate(frame, [20, 30], [0, 0.8], CLAMP) }}>
        <ChevronsDown size={90} color="white" />
      </div>
    </Stage>
  );
};
