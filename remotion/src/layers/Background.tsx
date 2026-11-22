import { AbsoluteFill, interpolate, random, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { BG, CLAMP } from "../theme";

/** Mix two hex colours. */
const mix = (a: string, b: string, t: number) => {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  return `rgb(${pa.map((v, i) => Math.round(v + (pb[i] - v) * t)).join(",")})`;
};

type Props = { starts: number[]; accents: string[]; frameOverride?: number };

/** Continuous animated backdrop: drifting glow blobs, a moving perspective grid, particles and grain. */
export const Background: React.FC<Props> = ({ starts, accents, frameOverride }) => {
  const current = useCurrentFrame();
  const frame = frameOverride ?? current;
  const { width, height } = useVideoConfig();

  // Smoothly blend the accent colour into the next scene's around each cut
  let idx = 0;
  for (let i = 0; i < starts.length; i++) if (frame >= starts[i]) idx = i;
  const nextStart = starts[idx + 1];
  const blend = nextStart === undefined ? 0 : interpolate(frame, [nextStart - 12, nextStart], [0, 1], CLAMP);
  const accent = mix(accents[idx], accents[Math.min(idx + 1, accents.length - 1)], blend);
  const accent2 = mix(accents[(idx + 1) % accents.length], accents[(idx + 2) % accents.length], blend);

  const t = frame / 30;
  const blobs = [
    { x: 0.2 + 0.12 * Math.sin(t * 0.5), y: 0.22 + 0.06 * Math.cos(t * 0.4), r: 0.75, c: accent, o: 0.55 },
    { x: 0.85 + 0.1 * Math.cos(t * 0.35), y: 0.55 + 0.1 * Math.sin(t * 0.45), r: 0.7, c: accent2, o: 0.35 },
    { x: 0.4 + 0.15 * Math.sin(t * 0.3 + 2), y: 0.92, r: 0.8, c: accent, o: 0.3 },
  ];

  const particles = new Array(46).fill(0).map((_, i) => {
    const speed = 0.4 + random(`s${i}`) * 1.4;
    const y = (random(`y${i}`) * height - frame * speed * 2 + height * 4) % height;
    const x = random(`x${i}`) * width + Math.sin(frame / 40 + i) * 12;
    const size = 2 + random(`r${i}`) * 5;
    const tw = 0.25 + 0.75 * Math.abs(Math.sin(frame / (18 + i) + i));
    return { x, y, size, o: tw * (0.25 + random(`o${i}`) * 0.5) };
  });

  return (
    <AbsoluteFill style={{ backgroundColor: BG, overflow: "hidden" }}>
      {blobs.map((b, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: b.x * width - (b.r * width) / 2,
            top: b.y * height - (b.r * width) / 2,
            width: b.r * width,
            height: b.r * width,
            borderRadius: "50%",
            background: `radial-gradient(circle, ${b.c} 0%, transparent 65%)`,
            opacity: b.o,
          }}
        />
      ))}

      {/* perspective grid floor */}
      <div
        style={{
          position: "absolute",
          left: -width * 0.5,
          width: width * 2,
          top: height * 0.62,
          height: height * 0.9,
          backgroundImage: `linear-gradient(${accent} 2px, transparent 2px), linear-gradient(90deg, ${accent} 2px, transparent 2px)`,
          backgroundSize: "110px 110px",
          backgroundPosition: `0px ${(frame * 3) % 110}px`,
          transform: "perspective(700px) rotateX(68deg)",
          transformOrigin: "top center",
          opacity: 0.22,
          maskImage: "linear-gradient(to bottom, transparent 0%, black 25%, black 60%, transparent 100%)",
        }}
      />

      {particles.map((p, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: p.x,
            top: p.y,
            width: p.size,
            height: p.size,
            borderRadius: "50%",
            background: "white",
            opacity: p.o,
            boxShadow: `0 0 ${p.size * 3}px ${accent}`,
          }}
        />
      ))}

      {/* vignette */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, transparent 45%, rgba(0,0,0,0.75) 100%)" }} />

      {/* animated film grain: a pre-made noise tile, shifted every frame */}
      <AbsoluteFill
        style={{
          opacity: 0.09,
          mixBlendMode: "overlay",
          backgroundImage: `url(${staticFile("noise.png")})`,
          backgroundPosition: `${Math.floor(random(`gx${frame}`) * 512)}px ${Math.floor(random(`gy${frame}`) * 512)}px`,
        }}
      />
    </AbsoluteFill>
  );
};
