import { Composition, Still } from "remotion";
import { Short, calculateShortMetadata } from "./Short";
import { Thumbnail } from "./Thumbnail";
import type { ShortProps } from "./types";

// Preview data for Remotion Studio. The Python pipeline passes real props with --props.
const demo: ShortProps = {
  sfx: false,
  words: [],
  scenes: [
    { durationInFrames: 90, visual: { type: "hook", title: "How AI *actually* reads your words", subtitle: "AI in 60 seconds" } },
    { durationInFrames: 120, visual: { type: "concept", title: "*Tokens*", subtitle: "Small chunks of text the model reads one at a time", icon: "puzzle" } },
    { durationInFrames: 120, visual: { type: "flow", title: "What happens *inside*", items: ["Text becomes tokens", "Tokens become numbers", "Model predicts next token"] } },
    { durationInFrames: 120, visual: { type: "list", title: "Write *better* prompts", items: ["Give context", "Show an example", "Ask for a format"] } },
    { durationInFrames: 110, visual: { type: "compare", title: "Prompt *upgrade*", items: ["Weak: Write about dogs", "Strong: 3 fun dog facts for kids, one line each"] } },
    { durationInFrames: 100, visual: { type: "stat", title: "Context window", number: "200,000", subtitle: "tokens a model can read at once" } },
    { durationInFrames: 150, visual: { type: "chat", title: "Try this prompt", items: ["Explain tokens like I'm 10", "Imagine cutting a sentence into puzzle pieces. Each piece is a token."] } },
    { durationInFrames: 90, visual: { type: "cta", title: "Learn AI *daily*", subtitle: "New lesson every day" } },
  ],
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Short"
      component={Short}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={900}
      defaultProps={demo}
      calculateMetadata={calculateShortMetadata}
    />
    <Still
      id="Thumbnail"
      component={Thumbnail}
      width={1280}
      height={720}
      defaultProps={{ title: "How AI *actually* reads", icon: "brain" }}
    />
  </>
);
