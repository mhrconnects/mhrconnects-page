"""Glue: script -> voiceover -> video + thumbnail + upload metadata."""

import json
import re
import shutil
import time
from pathlib import Path

from . import config, render, tts


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "video"


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def write_srt(scenes: list[dict], durations: list[float], out: Path) -> None:
    lines, idx, t = [], 1, 0.0
    for scene, dur in zip(scenes, durations):
        for c in render.caption_chunks(scene["narration"], t, dur, max_words=6):
            lines += [str(idx), f"{srt_time(c.start)} --> {srt_time(c.end)}", c.text, ""]
            idx += 1
        t += dur
    out.write_text("\n".join(lines), encoding="utf-8")


def make_video(script: dict, out_root: Path, engine: str = "auto", voice: str | None = None,
               music: Path | None = None, handle: str = config.CHANNEL_HANDLE) -> Path:
    started = time.time()
    out_dir = out_root / f"{time.strftime('%Y%m%d-%H%M%S')}-{slugify(script['title'])}"
    work = out_dir / "work"
    work.mkdir(parents=True, exist_ok=True)
    (out_dir / "script.json").write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

    scenes = script["scenes"]
    print(f"[1/3] Voiceover for {len(scenes)} scenes")
    parts, durations = [], []
    for i, scene in enumerate(scenes):
        wav = work / f"scene{i:02}.wav"
        durations.append(tts.synthesize(scene["narration"], wav, engine=engine, voice=voice))
        parts.append(wav)
    voice_wav = work / "voice.wav"
    tts.concat_wavs(parts, voice_wav)
    print(f"      total length {sum(durations):.1f}s")

    print("[2/3] Rendering video")
    video = out_dir / "video.mp4"
    render.render_video(scenes, durations, voice_wav, video, handle=handle, music=music)

    print("[3/3] Thumbnail, captions and metadata")
    render.render_thumbnail(script.get("thumbnail_text") or script["title"], out_dir / "thumbnail.png", handle)
    write_srt(scenes, durations, out_dir / "captions.srt")
    metadata = {
        "title": script["title"],
        "description": script["description"],
        "tags": script["tags"],
        "categoryId": "28",  # Science & Technology
        "duration_seconds": round(sum(durations), 1),
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.rmtree(work)
    print(f"Done in {time.time() - started:.0f}s -> {out_dir}")
    if sum(durations) > 60:
        print("  ! Over 60 seconds: YouTube may not treat this as a Short. Trim the script.")
    return out_dir
