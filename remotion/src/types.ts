export type VisualType =
  | "hook"
  | "concept"
  | "list"
  | "compare"
  | "flow"
  | "stat"
  | "chat"
  | "cta";

export type Visual = {
  type: VisualType;
  /** Main on-screen text. Wrap one key word in *asterisks* to highlight it. */
  title: string;
  subtitle?: string;
  items?: string[];
  icon?: string;
  number?: string;
};

export type SceneData = {
  durationInFrames: number;
  visual: Visual;
};

/** One spoken word, timed in seconds from the start of the video. */
export type Word = { text: string; start: number; end: number };

export type ShortProps = {
  scenes: SceneData[];
  words: Word[];
  /** Paths relative to remotion/public */
  audio?: string | null;
  music?: string | null;
  musicVolume?: number;
  sfx?: boolean;
  handle?: string;
};

export type ThumbnailProps = {
  title: string;
  icon?: string;
  handle?: string;
};
