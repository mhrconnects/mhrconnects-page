import { Audio } from "@remotion/media";
import { ArrowUp, ChevronDown, FileText, FolderOpen, Menu, MessageSquare, Paperclip, Plus, Sparkles } from "lucide-react";
import { Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { useLayout } from "../layout";
import { CLAMP, DISPLAY, EASE_OUT, SANS, glide, pop, stripEmphasis } from "../theme";
import { Chip, RevealText, SceneProps, Stage } from "./common";

/**
 * A stylised AI-chat app window (Claude-style tutorial look, no logos):
 * a cursor can click a UI element, a prompt types into the box, then the answer streams in.
 * items = [prompt, reply]; subtitle = attached file name; highlight = UI element to point at.
 */
export type AppHighlight = "none" | "new_chat" | "projects" | "attach" | "model" | "input";

const UI = {
  window: "#1E1D1B",
  side: "#171614",
  panel: "#2B2A27",
  text: "#ECE8E1",
  dim: "#9C978E",
  line: "rgba(255,255,255,0.09)",
  warm: "#D97757",
};

type Box = { x: number; y: number; w: number; h: number };

export const AppScene: React.FC<SceneProps & { highlight?: string; sfx: boolean }> = ({
  title, subtitle, items = [], highlight = "none", accent, sfx,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const L = useLayout();
  const W = L.landscape ? 1760 : 920;
  const H = L.landscape ? 820 : 1000;
  const side = L.landscape ? 330 : 0;
  const prompt = items[0] ?? "";
  const reply = items[1] ?? "";
  const file = subtitle?.trim();

  // ---- element boxes (window coordinates)
  const inputBox: Box = { x: side + 70, y: H - 210, w: W - side - 140, h: 170 };
  const targets: Record<string, Box> = {
    new_chat: L.landscape ? { x: 22, y: 84, w: side - 44, h: 62 } : { x: W - 300, y: 22, w: 270, h: 66 },
    projects: { x: 22, y: 222, w: (L.landscape ? side : 520) - 44, h: 58 },
    attach: { x: inputBox.x + 22, y: inputBox.y + inputBox.h - 74, w: 58, h: 58 },
    model: { x: inputBox.x + inputBox.w - 330, y: inputBox.y + inputBox.h - 74, w: 220, h: 58 },
    input: inputBox,
  };
  const target = targets[highlight];
  const pointAt = target && highlight !== "input";
  const drawer = !L.landscape && highlight === "projects";

  // ---- timeline
  const click = 36;
  const typeStart = pointAt ? 62 : 16;
  const fileAt = file ? typeStart - 10 : -1;
  const typeEnd = typeStart + Math.max(Math.min(prompt.length * 0.75, 75), 1);
  const sendAt = Math.round(typeEnd + 8);
  const replyStart = sendAt + 24;
  const sent = !!prompt && frame >= sendAt;

  const enter = pop(frame, fps, 0, 18);
  const typed = prompt.slice(0, Math.floor(interpolate(frame, [typeStart, typeEnd], [0, prompt.length], CLAMP)));

  // cursor path
  const cp = interpolate(frame, [8, 34], [0, 1], { ...CLAMP, easing: EASE_OUT });
  const cx = target ? interpolate(cp, [0, 1], [W * 0.62, target.x + target.w / 2]) : 0;
  const cy = target ? interpolate(cp, [0, 1], [H * 0.55, target.y + target.h / 2]) : 0;
  const ripple = interpolate(frame, [click, click + 16], [0, 1], CLAMP);
  const ringOn = target ? interpolate(frame, [pointAt ? click : 8, (pointAt ? click : 8) + 8], [0, 1], CLAMP) : 0;

  const sideItem = (icon: React.ReactNode, label: string, y: number, strong = false) => (
    <div style={{ position: "absolute", left: 22, top: y, width: (L.landscape ? side : 520) - 44, height: 58, display: "flex", alignItems: "center", gap: 18, padding: "0 18px", borderRadius: 14, fontFamily: SANS, fontWeight: strong ? 700 : 500, fontSize: 30, color: UI.text }}>
      {icon}
      {label}
    </div>
  );

  const sidebar = (
    <>
      <div style={{ position: "absolute", left: 30, top: 26, fontFamily: DISPLAY, fontWeight: 700, fontSize: 38, color: UI.text }}>Claude</div>
      <div style={{ position: "absolute", left: 22, top: 84, width: (L.landscape ? side : 520) - 44, height: 62, borderRadius: 16, background: UI.panel, display: "flex", alignItems: "center", gap: 14, padding: "0 18px", fontFamily: SANS, fontWeight: 700, fontSize: 30, color: UI.text }}>
        <Plus size={30} color={UI.warm} /> New chat
      </div>
      {sideItem(<MessageSquare size={28} color={UI.dim} />, "Chats", 162)}
      {sideItem(<FolderOpen size={28} color={UI.dim} />, "Projects", 222)}
      <div style={{ position: "absolute", left: 40, top: 312, fontFamily: SANS, fontWeight: 600, fontSize: 24, color: UI.dim, letterSpacing: 1 }}>Recents</div>
      {["Trip plan for Lisbon", "Explain compound interest", "Cover letter draft", "Python bug fix"].map((r, i) => (
        <div key={r} style={{ position: "absolute", left: 40, top: 360 + i * 54, fontFamily: SANS, fontSize: 26, color: UI.dim, whiteSpace: "nowrap" }}>{r}</div>
      ))}
    </>
  );

  return (
    <Stage>
      {title ? <Chip text={stripEmphasis(title)} accent={accent} /> : null}
      <div
        style={{
          position: "relative",
          width: W,
          height: H,
          borderRadius: 32,
          overflow: "hidden",
          background: UI.window,
          border: `1.5px solid ${UI.line}`,
          boxShadow: `0 50px 120px rgba(0,0,0,0.6), 0 0 80px ${accent}22`,
          scale: interpolate(enter, [0, 1], [0.9, 1]),
          opacity: enter,
          flexShrink: 0,
        }}
      >
        {/* sidebar (landscape) or top bar (portrait) */}
        {L.landscape ? (
          <div style={{ position: "absolute", left: 0, top: 0, width: side, height: H, background: UI.side, borderRight: `1.5px solid ${UI.line}` }}>{sidebar}</div>
        ) : (
          <div style={{ position: "absolute", left: 0, top: 0, width: W, height: 110, borderBottom: `1.5px solid ${UI.line}`, display: "flex", alignItems: "center", padding: "0 30px", gap: 20 }}>
            <Menu size={40} color={UI.text} />
            <div style={{ fontFamily: DISPLAY, fontWeight: 700, fontSize: 38, color: UI.text }}>Claude</div>
            <div style={{ position: "absolute", right: 30, top: 22, height: 66, width: 270, borderRadius: 16, background: UI.panel, display: "flex", alignItems: "center", justifyContent: "center", gap: 12, fontFamily: SANS, fontWeight: 700, fontSize: 30, color: UI.text }}>
              <Plus size={30} color={UI.warm} /> New chat
            </div>
          </div>
        )}

        {/* conversation area */}
        <div style={{ position: "absolute", left: side + 70, right: 70, top: L.landscape ? 60 : 150, bottom: 240 }}>
          {!sent ? (
            <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 22, opacity: glide(frame, fps, 4) }}>
              <Sparkles size={64} color={UI.warm} />
              <div style={{ fontFamily: DISPLAY, fontWeight: 500, fontSize: L.landscape ? 54 : 50, color: UI.text, textAlign: "center" }}>How can I help you today?</div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 34 }}>
              <div
                style={{
                  alignSelf: "flex-end",
                  maxWidth: "80%",
                  padding: "22px 28px",
                  borderRadius: 24,
                  background: UI.panel,
                  fontFamily: SANS,
                  fontWeight: 500,
                  fontSize: L.landscape ? 32 : 34,
                  lineHeight: 1.35,
                  color: UI.text,
                  opacity: glide(frame, fps, sendAt),
                  translate: `0px ${(1 - glide(frame, fps, sendAt)) * 60}px`,
                }}
              >
                {file ? (
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12, fontSize: 26, color: UI.dim }}>
                    <FileText size={28} color={UI.warm} /> {file}
                  </div>
                ) : null}
                {prompt}
              </div>
              <div style={{ display: "flex", gap: 22, alignItems: "flex-start" }}>
                <div style={{ rotate: frame < replyStart ? `${frame * 8}deg` : "0deg", marginTop: 4 }}>
                  <Sparkles size={44} color={UI.warm} />
                </div>
                {frame >= replyStart ? (
                  <RevealText
                    text={reply}
                    start={replyStart}
                    duration={Math.max(Math.min(durationInFrames - replyStart - 30, reply.split(" ").length * 5), 15)}
                    size={L.landscape ? 34 : 36}
                    weight={400}
                    color={UI.text}
                    align="left"
                  />
                ) : null}
              </div>
            </div>
          )}
        </div>

        {/* message box */}
        <div style={{ position: "absolute", left: inputBox.x, top: inputBox.y, width: inputBox.w, height: inputBox.h, borderRadius: 26, background: UI.panel, border: `1.5px solid ${UI.line}` }}>
          {file && frame >= fileAt && !sent ? (
            <div style={{ position: "absolute", left: 24, top: -74, height: 58, padding: "0 20px", borderRadius: 14, background: UI.side, border: `1.5px solid ${UI.line}`, display: "flex", alignItems: "center", gap: 12, fontFamily: SANS, fontSize: 26, color: UI.text, scale: pop(frame, fps, fileAt, 12) }}>
              <FileText size={28} color={UI.warm} /> {file}
            </div>
          ) : null}
          <div style={{ position: "absolute", left: 30, top: 24, right: 30, fontFamily: SANS, fontSize: L.landscape ? 32 : 34, color: sent || !typed ? UI.dim : UI.text, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {sent || !typed ? "Write a message..." : typed}
            {!sent && typed && frame < typeEnd + 6 ? <span style={{ opacity: Math.round(frame / 6) % 2, color: UI.warm }}>|</span> : null}
          </div>
          <div style={{ position: "absolute", left: 22, bottom: 16, width: 58, height: 58, borderRadius: 14, border: `1.5px solid ${UI.line}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Paperclip size={28} color={UI.dim} />
          </div>
          <div style={{ position: "absolute", right: 110, bottom: 16, width: 220, height: 58, display: "flex", alignItems: "center", justifyContent: "center", gap: 8, fontFamily: SANS, fontWeight: 600, fontSize: 26, color: UI.dim }}>
            Model <ChevronDown size={24} color={UI.dim} />
          </div>
          <div
            style={{
              position: "absolute",
              right: 20,
              bottom: 16,
              width: 64,
              height: 58,
              borderRadius: 14,
              background: typed && !sent ? UI.warm : "rgba(217,119,87,0.35)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              scale: 1 + 0.25 * interpolate(frame, [sendAt - 4, sendAt, sendAt + 6], [0, 1, 0], CLAMP),
            }}
          >
            <ArrowUp size={32} color="white" />
          </div>
        </div>

        {/* portrait drawer for Projects */}
        {drawer ? (
          <div style={{ position: "absolute", left: 0, top: 0, width: 520, height: H, background: UI.side, borderRight: `1.5px solid ${UI.line}`, translate: `${interpolate(glide(frame, fps, 4), [0, 1], [-520, 0])}px 0px`, boxShadow: "20px 0 60px rgba(0,0,0,0.5)" }}>
            {sidebar}
          </div>
        ) : null}

        {/* highlight ring */}
        {target ? (
          <div
            style={{
              position: "absolute",
              left: target.x - 8,
              top: target.y - 8,
              width: target.w + 16,
              height: target.h + 16,
              borderRadius: 20,
              border: `4px solid ${accent}`,
              boxShadow: `0 0 ${30 + 14 * Math.sin(frame / 5)}px ${accent}, inset 0 0 20px ${accent}55`,
              opacity: ringOn,
              scale: 1 + 0.03 * Math.sin(frame / 5),
            }}
          />
        ) : null}

        {/* cursor */}
        {pointAt ? (
          <>
            {ripple > 0 && ripple < 1 ? (
              <div style={{ position: "absolute", left: cx - 50, top: cy - 50, width: 100, height: 100, borderRadius: 50, border: `4px solid ${accent}`, scale: ripple * 1.6, opacity: 1 - ripple }} />
            ) : null}
            <svg
              width={54}
              height={54}
              viewBox="0 0 24 24"
              style={{
                position: "absolute",
                left: cx - 6,
                top: cy - 4,
                scale: frame >= click && frame < click + 5 ? 0.85 : 1,
                opacity: interpolate(frame, [6, 10, typeStart - 4, typeStart], [0, 1, 1, 0], CLAMP),
                filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.6))",
              }}
            >
              <path d="M4 2 L4 20 L9 15.5 L12.5 22 L15.5 20.5 L12 14 L19 14 Z" fill="white" stroke="black" strokeWidth={1.2} strokeLinejoin="round" />
            </svg>
            {sfx ? (
              <Sequence from={click} durationInFrames={20} layout="none">
                <Audio src={staticFile("sfx/pop.wav")} volume={0.4} />
              </Sequence>
            ) : null}
          </>
        ) : null}
      </div>
    </Stage>
  );
};

/** Chapter title card: big outlined number + title. */
export const SectionScene: React.FC<SceneProps> = ({ title, subtitle, number, accent, accent2 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = pop(frame, fps, 0, 14);
  const line = interpolate(frame, [6, 26], [0, 1], { ...CLAMP, easing: EASE_OUT });
  return (
    <Stage>
      <div
        style={{
          fontFamily: SANS,
          fontWeight: 900,
          fontSize: 300,
          lineHeight: 0.9,
          color: "transparent",
          WebkitTextStroke: `4px ${accent}`,
          filter: `drop-shadow(0 0 30px ${accent}88)`,
          opacity: p,
          scale: interpolate(p, [0, 1], [1.4, 1]),
        }}
      >
        {number ?? ""}
      </div>
      <div style={{ width: 520 * line, height: 8, borderRadius: 4, background: `linear-gradient(90deg, ${accent}, ${accent2})`, boxShadow: `0 0 24px ${accent}` }} />
      <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 120, color: "white", letterSpacing: -3, textAlign: "center", opacity: glide(frame, fps, 8), translate: `0px ${(1 - glide(frame, fps, 8)) * 40}px` }}>
        {stripEmphasis(title)}
      </div>
      {subtitle ? <RevealText text={subtitle} start={18} duration={16} size={50} /> : null}
    </Stage>
  );
};
