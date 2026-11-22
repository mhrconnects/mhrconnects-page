"""Command line: python -m ytauto <command> ...

  make "topic"               Claude writes the script, then the video is built
  make --script file.json    build from a script you wrote or edited (no API key needed)
  batch topics.txt           one video per line in a text file
  ideas -n 20                brainstorm topic ideas into ideas.txt
"""

import argparse
import json
import sys
from pathlib import Path

from . import config


def main() -> int:
    ap = argparse.ArgumentParser(prog="ytauto", description="Faceless YouTube Shorts generator")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def video_opts(p):
        p.add_argument("--out", default="output", help="output folder (default: output)")
        p.add_argument("--voice-engine", choices=["auto", "edge", "espeak"], default="auto",
                       help="auto = natural edge-tts voice, falling back to offline espeak-ng")
        p.add_argument("--voice", help=f"voice name (default {config.EDGE_VOICE})")
        p.add_argument("--music", type=Path, help="optional background music file (use royalty-free tracks)")
        p.add_argument("--handle", default=config.CHANNEL_HANDLE, help="channel handle shown on screen")

    m = sub.add_parser("make", help="make one video")
    m.add_argument("topic", nargs="?", help="what the video is about")
    m.add_argument("--script", type=Path, help="use this script JSON instead of asking Claude")
    m.add_argument("--script-only", action="store_true", help="only write the script JSON, for review/editing")
    video_opts(m)

    b = sub.add_parser("batch", help="make one video per topic line in a file")
    b.add_argument("topics_file", type=Path)
    video_opts(b)

    i = sub.add_parser("ideas", help="brainstorm topics")
    i.add_argument("-n", type=int, default=20)
    i.add_argument("--save", type=Path, default=Path("ideas.txt"))

    args = ap.parse_args()
    from . import pipeline, script_gen

    if args.cmd == "ideas":
        ideas = script_gen.generate_ideas(args.n)
        args.save.write_text("\n".join(x["topic"] for x in ideas) + "\n", encoding="utf-8")
        for n, x in enumerate(ideas, 1):
            print(f"{n:2}. {x['topic']}\n    {x['why_it_works']}")
        print(f"\nSaved to {args.save} - run: python -m ytauto batch {args.save}")
        return 0

    opts = dict(engine=args.voice_engine, voice=args.voice, music=args.music, handle=args.handle)
    out = Path(args.out)

    if args.cmd == "batch":
        topics = [t.strip() for t in args.topics_file.read_text(encoding="utf-8").splitlines()
                  if t.strip() and not t.startswith("#")]
        failed = []
        for n, topic in enumerate(topics, 1):
            print(f"\n=== {n}/{len(topics)}: {topic}")
            try:
                pipeline.make_video(script_gen.generate_script(topic), out, **opts)
            except Exception as exc:
                print(f"  x failed: {exc}")
                failed.append(topic)
        print(f"\nFinished {len(topics) - len(failed)}/{len(topics)} videos.")
        return 1 if failed else 0

    if args.script:
        script = json.loads(args.script.read_text(encoding="utf-8"))
    elif args.topic:
        print(f"Writing script with Claude: {args.topic}")
        script = script_gen.generate_script(args.topic)
    else:
        ap.error("give a topic or --script FILE")

    if args.script_only:
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{pipeline.slugify(script['title'])}.json"
        path.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Script saved to {path}. Edit it, then: python -m ytauto make --script {path}")
        return 0

    pipeline.make_video(script, out, **opts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
