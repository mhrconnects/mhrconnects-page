import { Audio } from "@remotion/media";
import { AbsoluteFill, CalculateMetadataFunction, Sequence, Series, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "./layers/Background";
import { Captions } from "./layers/Captions";
import { CutFlash, Handle, ProgressBar } from "./layers/Overlays";
import {
  ChatScene, CompareScene, ConceptScene, CtaScene, FlowScene, HookScene, ListScene, StatScene,
} from "./scenes/Scenes";
import { AppScene, SectionScene } from "./scenes/AppScene";
import { accentAt } from "./theme";
import type { SceneData, ShortProps } from "./types";

const sceneStarts = (scenes: SceneData[]) => {
  const out: number[] = [];
  let t = 0;
  for (const s of scenes) {
    out.push(t);
    t += s.durationInFrames;
  }
  return out;
};

export const calculateShortMetadata: CalculateMetadataFunction<ShortProps> = ({ props }) => ({
  durationInFrames: Math.max(1, props.scenes.reduce((sum, s) => sum + s.durationInFrames, 0)),
});

const SceneSwitch: React.FC<{ scene: SceneData; index: number; sfx: boolean; handle?: string }> = ({ scene, index, sfx, handle }) => {
  const v = scene.visual;
  const common = { ...v, accent: accentAt(index), accent2: accentAt(index + 1) };
  switch (v.type) {
    case "hook": return <HookScene {...common} />;
    case "concept": return <ConceptScene {...common} />;
    case "list": return <ListScene {...common} sfx={sfx} />;
    case "compare": return <CompareScene {...common} sfx={sfx} />;
    case "flow": return <FlowScene {...common} sfx={sfx} />;
    case "stat": return <StatScene {...common} />;
    case "chat": return <ChatScene {...common} />;
    case "cta": return <CtaScene {...common} handle={handle} />;
    case "app": return <AppScene {...common} sfx={sfx} />;
    case "section": return <SectionScene {...common} />;
    default: return <HookScene {...common} />;
  }
};

export const Short: React.FC<ShortProps> = ({ scenes, words, audio, music, musicVolume = 0.12, sfx = true, handle }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const starts = sceneStarts(scenes);
  const accents = scenes.map((_, i) => accentAt(i));
  let current = 0;
  starts.forEach((s, i) => { if (frame >= s) current = i; });
  const accentForTime = (t: number) => {
    let i = 0;
    starts.forEach((s, k) => { if (t * 30 >= s) i = k; });
    return accents[i];
  };

  return (
    <AbsoluteFill>
      <Background starts={starts} accents={accents} />
      <Series>
        {scenes.map((scene, i) => (
          <Series.Sequence key={i} name={`${i + 1}. ${scene.visual.type}`} durationInFrames={scene.durationInFrames}>
            <SceneSwitch scene={scene} index={i} sfx={sfx} handle={handle} />
          </Series.Sequence>
        ))}
      </Series>
      <Captions words={words} accentFor={accentForTime} />
      <CutFlash starts={starts} accents={accents} />
      {width > height ? <ProgressBar accent={accents[current]} /> : null}
      {handle ? <Handle handle={handle} /> : null}

      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={musicVolume} loop /> : null}
      {sfx ? (
        <>
          <Sequence from={0} durationInFrames={40} layout="none">
            <Audio src={staticFile("sfx/impact.wav")} volume={0.5} />
          </Sequence>
          {starts.slice(1).map((s, i) => (
            <Sequence key={i} from={Math.max(0, s - 5)} durationInFrames={30} layout="none">
              <Audio src={staticFile("sfx/whoosh.wav")} volume={0.45} />
            </Sequence>
          ))}
        </>
      ) : null}
    </AbsoluteFill>
  );
};
