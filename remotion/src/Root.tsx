import { Composition, Still } from "remotion";
import { Short, calculateShortMetadata } from "./Short";
import { Avatar } from "./Avatar";
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

const longDemo: ShortProps = {
  sfx: false,
  words: [],
  scenes: [
    { durationInFrames: 90, visual: { type: "hook", title: "Claude *basics*", subtitle: "Beginner guide" } },
    { durationInFrames: 120, visual: { type: "section", number: "01", title: "What is Claude?", subtitle: "Your AI assistant" } },
    { durationInFrames: 150, visual: { type: "app", title: "Start a new chat", highlight: "new_chat" } },
    { durationInFrames: 240, visual: { type: "app", title: "Your first prompt", items: ["Explain compound interest like I'm 12", "Imagine you plant one apple tree. Each year it grows apples, and those apples grow new trees. Your money does the same thing."] } },
    { durationInFrames: 240, visual: { type: "app", title: "Upload a file", subtitle: "report.pdf", highlight: "attach", items: ["Summarize this report in 5 bullet points", "Here are the five key points from your report..."] } },
    { durationInFrames: 120, visual: { type: "list", title: "Better *prompts*", items: ["Context", "Task", "Example", "Format"] } },
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
    <Composition
      id="Long"
      component={Short}
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={900}
      defaultProps={longDemo}
      calculateMetadata={calculateShortMetadata}
    />
    <Still
      id="Thumbnail"
      component={Thumbnail}
      width={1280}
      height={720}
      defaultProps={{ title: "How AI *actually* reads", icon: "brain" }}
    />
    <Still id="Avatar" component={Avatar} width={800} height={800} defaultProps={{ variant: "monogram" as const, text: "MHR", icon: "brain" }} />
  </>
);
