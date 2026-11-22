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


def chapters_text(scenes: list[dict], starts: list[float]) -> str:
    """YouTube chapter list ("0:00 Intro") built from scenes that carry a "chapter" name."""
    marks = [(t, sc["chapter"]) for sc, t in zip(scenes, starts) if sc.get("chapter")]
    if not marks:
        return ""
    if marks[0][0] > 0:
        marks.insert(0, (0.0, "Intro"))
    fmt = lambda t: f"{int(t // 60)}:{int(t % 60):02}"
    return "Chapters:\n" + "\n".join(f"{fmt(t)} {name}" for t, name in marks)


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
        parts, scene_props, words, starts = [], [], [], []
        offset = 0.0
        for i, scene in enumerate(scenes):
            wav = job_dir / f"scene{i:02}.wav"
            duration, scene_words = tts.synthesize(
                scene["narration"], wav, engine=engine, voice=voice,
                pad_seconds=0.55 if script.get("format") == "long" else 0.35,
                rate="+0%" if script.get("format") == "long" else None,  # calmer pace for tutorials
            )
            frames = math.ceil(duration * config.FPS)
            seconds = frames / config.FPS
            parts.append((wav, seconds))
            starts.append(offset)
            scene_props.append({"durationInFrames": frames, "visual": scene["visual"]})
            words += [{"text": t, "start": round(offset + s, 3), "end": round(offset + e, 3)} for t, s, e in scene_words]
            offset += seconds
        tts.concat_wavs(parts, job_dir / "voice_raw.wav")
        # Normalise speech loudness so the finished video sits near YouTube's -14 LUFS playback level
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(job_dir / "voice_raw.wav"),
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "1",
                        str(job_dir / "voice.wav")], check=True)
        (job_dir / "voice_raw.wav").unlink()
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
        long = script.get("format") == "long"
        _remotion(["render", "src/index.ts", "Long" if long else "Short", str(out_dir / "video.mp4"), f"--props={props_file}",
                   "--codec=h264", "--crf=21", f"--concurrency={os.cpu_count() or 2}"])

        print("[3/3] Thumbnail, captions and metadata")
        thumb_props = job_dir / "thumb.json"
        thumb_props.write_text(json.dumps({
            "title": script.get("thumbnail_text") or script["title"],
            "icon": script.get("thumbnail_icon", "brain"),
            "handle": handle or "",
        }), encoding="utf-8")
        _remotion(["still", "src/index.ts", "Thumbnail", str(out_dir / "thumbnail.png"), f"--props={thumb_props}"])
        write_srt(words, out_dir / "captions.srt")
        description = script["description"]
        chapters = chapters_text(scenes, starts)
        if chapters:
            description = f"{description}\n\n{chapters}"
        (out_dir / "metadata.json").write_text(json.dumps({
            "title": script["title"].replace("*", ""),
            "description": description,
            "tags": script["tags"],
            "categoryId": "27",  # Education
            "duration_seconds": round(offset, 1),
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)

    print(f"Done in {time.time() - started:.0f}s -> {out_dir}")
    if offset > 60 and script.get("format") != "long":
        print("  ! Over 60 seconds: shorten the script so YouTube treats it as a Short.")
    return out_dir
