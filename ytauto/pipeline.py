"""Glue: script -> voiceover with word timings -> Remotion motion graphics -> MP4 + thumbnail + metadata."""

import json
import math
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from . import config, tts

REMOTION_DIR = Path(__file__).resolve().parent.parent / "remotion"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("*", "")).strip("-")[:60] or "video"


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def write_srt(words: list[dict], out: Path, per_line: int = 6) -> None:
    lines = []
    for n, i in enumerate(range(0, len(words), per_line), 1):
        chunk = words[i:i + per_line]
        lines += [str(n), f"{srt_time(chunk[0]['start'])} --> {srt_time(chunk[-1]['end'])}",
                  " ".join(w["text"] for w in chunk), ""]
    out.write_text("\n".join(lines), encoding="utf-8")


def _remotion(args: list[str]) -> None:
    if not (REMOTION_DIR / "node_modules").exists():
        raise RuntimeError(f"Remotion isn't installed yet. Run:  cd {REMOTION_DIR} && npm install")
    cmd = ["npx", "remotion", *args, "--log=error"]
    if config.BROWSER_EXECUTABLE:
        cmd.append(f"--browser-executable={config.BROWSER_EXECUTABLE}")
    subprocess.run(cmd, cwd=REMOTION_DIR, check=True, shell=False)


def make_video(script: dict, out_root: Path, engine: str = "auto", voice: str | None = None,
               music: Path | None = None, handle: str = config.CHANNEL_HANDLE, sfx: bool = True) -> Path:
    started = time.time()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_dir = (out_root / f"{stamp}-{slugify(script['title'])}").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    job = f"jobs/{stamp}"
    job_dir = REMOTION_DIR / "public" / job
    job_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "script.json").write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        scenes = script["scenes"]
        print(f"[1/3] Voiceover for {len(scenes)} scenes")
        parts, scene_props, words = [], [], []
        offset = 0.0
        for i, scene in enumerate(scenes):
            wav = job_dir / f"scene{i:02}.wav"
            duration, scene_words = tts.synthesize(scene["narration"], wav, engine=engine, voice=voice)
            frames = math.ceil(duration * config.FPS)
            seconds = frames / config.FPS
            parts.append((wav, seconds))
            scene_props.append({"durationInFrames": frames, "visual": scene["visual"]})
            words += [{"text": t, "start": round(offset + s, 3), "end": round(offset + e, 3)} for t, s, e in scene_words]
            offset += seconds
        tts.concat_wavs(parts, job_dir / "voice.wav")
        for wav, _ in parts:
            wav.unlink()
        print(f"      total length {offset:.1f}s")

        props = {"scenes": scene_props, "words": words, "audio": f"{job}/voice.wav", "sfx": sfx,
                 "handle": handle or "", "musicVolume": config.MUSIC_VOLUME}
        if music:
            shutil.copy(music, job_dir / f"music{music.suffix}")
            props["music"] = f"{job}/music{music.suffix}"
        props_file = job_dir / "props.json"
        props_file.write_text(json.dumps(props), encoding="utf-8")

        print("[2/3] Rendering motion graphics (Remotion)")
        _remotion(["render", "src/index.ts", "Short", str(out_dir / "video.mp4"), f"--props={props_file}",
                   "--codec=h264", "--crf=18", f"--concurrency={os.cpu_count() or 2}"])

        print("[3/3] Thumbnail, captions and metadata")
        thumb_props = job_dir / "thumb.json"
        thumb_props.write_text(json.dumps({
            "title": script.get("thumbnail_text") or script["title"],
            "icon": script.get("thumbnail_icon", "brain"),
            "handle": handle or "",
        }), encoding="utf-8")
        _remotion(["still", "src/index.ts", "Thumbnail", str(out_dir / "thumbnail.png"), f"--props={thumb_props}"])
        write_srt(words, out_dir / "captions.srt")
        (out_dir / "metadata.json").write_text(json.dumps({
            "title": script["title"].replace("*", ""),
            "description": script["description"],
            "tags": script["tags"],
            "categoryId": "27",  # Education
            "duration_seconds": round(offset, 1),
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)

    print(f"Done in {time.time() - started:.0f}s -> {out_dir}")
    if offset > 60:
        print("  ! Over 60 seconds: shorten the script so YouTube treats it as a Short.")
    return out_dir
