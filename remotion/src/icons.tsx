import {
  BookOpen, Bot, Brain, Clock, Code, Cpu, Database, Eye, FileText, Globe, GraduationCap, Image,
  Layers, Lightbulb, MessageSquare, Network, Puzzle, Rocket, Search, Shield, Sparkles, Target, Wand, Zap,
} from "lucide-react";

export const ICONS = {
  brain: Brain, chip: Cpu, chat: MessageSquare, spark: Sparkles, book: BookOpen, code: Code,
  image: Image, shield: Shield, bolt: Zap, eye: Eye, search: Search, layers: Layers, target: Target,
  globe: Globe, idea: Lightbulb, bot: Bot, data: Database, magic: Wand, doc: FileText,
  learn: GraduationCap, rocket: Rocket, puzzle: Puzzle, network: Network, time: Clock,
} as const;

export const ICON_NAMES = Object.keys(ICONS);

export const Icon: React.FC<{ name?: string; size: number; color: string; strokeWidth?: number }> = ({
  name, size, color, strokeWidth = 1.6,
}) => {
  const Cmp = ICONS[(name ?? "spark") as keyof typeof ICONS] ?? Sparkles;
  return <Cmp size={size} color={color} strokeWidth={strokeWidth} />;
};
