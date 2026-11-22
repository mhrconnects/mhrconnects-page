"""Render animated text-slide video frames with Pillow and encode them with ffmpeg."""

import math
import random
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from . import config

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
]
PAN = 120  # extra background pixels used for the slow camera drift


def font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def clean(text: str) -> str:
    """Strip emoji and other characters most fonts can't draw."""
    return re.sub(r"[^\u0000-\uFFFF]|[\u2600-\u27BF\uFE0F]", "", text).strip()


def wrap(text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if fnt.getlength(trial) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


@dataclass
class Chunk:
    text: str
    start: float
    end: float


def caption_chunks(narration: str, start: float, duration: float, max_words: int = 3) -> list[Chunk]:
    """Split narration into short caption groups, timed in proportion to their length."""
    words = narration.split()
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= max_words or re.search(r"[.,!?;:]$", w):
            groups.append(" ".join(cur))
            cur = []
    if cur:
        groups.append(" ".join(cur))
    speech = max(duration - 0.3, 0.1)  # trailing pad from tts.synthesize
    weights = [len(g) + 3 for g in groups]
    total = sum(weights)
    chunks, t = [], start
    for g, wgt in zip(groups, weights):
        d = speech * wgt / total
        chunks.append(Chunk(g, t, t + d))
        t += d
    if chunks:
        chunks[-1].end = start + duration
    return chunks


def gradient_background(w: int, h: int, top, bottom, accent, seed: int) -> Image.Image:
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        k = y / (h - 1)
        draw.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    # soft glowing blobs
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    rnd = random.Random(seed)
    for _ in range(4):
        r = rnd.randint(220, 420)
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        gd.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(c * 0.35) for c in accent))
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    img = ImageChops.screen(img, glow)
    # subtle tech dot grid
    draw = ImageDraw.Draw(img)
    dot = tuple(min(255, c + 28) for c in top)
    for y in range(0, h, 60):
        for x in range(0, w, 60):
            draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=dot)
    return img


def text_block(lines: list[str], fnt, fill, stroke=6, stroke_fill=(0, 0, 0), line_gap=1.15,
               highlight_last: tuple | None = None) -> Image.Image:
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * line_gap)
    width = int(max(fnt.getlength(l) for l in lines)) + stroke * 2 + 8
    img = Image.new("RGBA", (width, lh * len(lines) + stroke * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        x = (width - fnt.getlength(line)) / 2
        color = highlight_last if highlight_last and i == len(lines) - 1 else fill
        d.text((x, stroke + i * lh), line, font=fnt, fill=color, stroke_width=stroke, stroke_fill=stroke_fill)
    return img


def headline_card(text: str, accent, max_width: int) -> Image.Image:
    fnt = font(96)
    lines = wrap(clean(text).upper(), fnt, max_width - 80)
    block = text_block(lines, fnt, (255, 255, 255), stroke=0)
    pad = 44
    card = Image.new("RGBA", (block.width + pad * 2, block.height + pad * 2), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, card.width - 1, card.height - 1], radius=36, fill=(0, 0, 0, 150),
                         outline=accent + (255,), width=6)
    card.alpha_composite(block, (pad, pad))
    return card


def caption_image(text: str, max_width: int) -> Image.Image:
    fnt = font(104)
    lines = wrap(clean(text).upper(), fnt, max_width)
    return text_block(lines, fnt, config.CAPTION_COLOR, stroke=10, highlight_last=config.CAPTION_HIGHLIGHT)


def ease_out(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


@dataclass
class SceneLayers:
    start: float
    end: float
    background: Image.Image
    headline: Image.Image
    accent: tuple
    chunks: list[Chunk]
    captions: list[Image.Image]
    pan_dir: tuple


def build_layers(scenes: list[dict], durations: list[float]) -> list[SceneLayers]:
    W, H = config.WIDTH, config.HEIGHT
    layers, t = [], 0.0
    for i, (scene, dur) in enumerate(zip(scenes, durations)):
        top, bottom, accent = config.THEMES[i % len(config.THEMES)]
        bg = gradient_background(W + PAN, H + PAN, top, bottom, accent, seed=i)
        chunks = caption_chunks(scene["narration"], t, dur)
        layers.append(SceneLayers(
            start=t, end=t + dur, background=bg,
            headline=headline_card(scene["on_screen_text"], accent, W - 120),
            accent=accent, chunks=chunks,
            captions=[caption_image(c.text, W - 140) for c in chunks],
            pan_dir=[(1, 1), (-1, 1), (1, -1), (-1, -1)][i % 4],
        ))
        t += dur
    return layers


def draw_frame(t: float, total: float, layer: SceneLayers, handle: str, handle_img: Image.Image) -> Image.Image:
    W, H = config.WIDTH, config.HEIGHT
    p = (t - layer.start) / max(layer.end - layer.start, 0.01)
    dx, dy = layer.pan_dir
    ox = int(PAN / 2 + dx * (p - 0.5) * PAN * 0.9)
    oy = int(PAN / 2 + dy * (p - 0.5) * PAN * 0.9)
    frame = layer.background.crop((ox, oy, ox + W, oy + H)).convert("RGBA")

    # headline slides down + fades in at the start of each scene
    local = t - layer.start
    k = ease_out(local / 0.45)
    hl = layer.headline
    if k < 1:
        hl = hl.copy()
        hl.putalpha(hl.getchannel("A").point(lambda a: int(a * k)))
    hx = (W - hl.width) // 2
    hy = int(360 - (1 - k) * 80 - hl.height / 2) + 100
    frame.alpha_composite(hl, (hx, max(hy, 140)))

    # active caption pops in
    for chunk, img in zip(layer.chunks, layer.captions):
        if chunk.start <= t < chunk.end:
            pop = 0.82 + 0.18 * ease_out((t - chunk.start) / 0.12)
            if pop < 1:
                img = img.resize((max(1, int(img.width * pop)), max(1, int(img.height * pop))), Image.BILINEAR)
            frame.alpha_composite(img, ((W - img.width) // 2, int(H * 0.66 - img.height / 2)))
            break

    d = ImageDraw.Draw(frame)
    # progress bar
    d.rectangle([0, 0, W, 14], fill=(0, 0, 0, 160))
    d.rectangle([0, 0, int(W * t / total), 14], fill=layer.accent + (255,))
    # channel handle watermark
    frame.alpha_composite(handle_img, ((W - handle_img.width) // 2, H - 260))
    return frame.convert("RGB")


def render_video(scenes: list[dict], durations: list[float], audio_wav: Path, out_mp4: Path,
                 handle: str = config.CHANNEL_HANDLE, music: Path | None = None) -> None:
    W, H, FPS = config.WIDTH, config.HEIGHT, config.FPS
    layers = build_layers(scenes, durations)
    total = sum(durations)
    handle_img = text_block([handle], font(46), (255, 255, 255, 200), stroke=3)

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(audio_wav)]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music),
                "-filter_complex",
                f"[2:a]volume={config.MUSIC_VOLUME}[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out_mp4)]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n_frames = math.ceil(total * FPS)
    li = 0
    try:
        for f in range(n_frames):
            t = f / FPS
            while li < len(layers) - 1 and t >= layers[li].end:
                li += 1
            proc.stdin.write(draw_frame(t, total, layers[li], handle, handle_img).tobytes())
            if f % (FPS * 5) == 0:
                print(f"  rendering {t:5.1f}s / {total:.1f}s", flush=True)
    finally:
        proc.stdin.close()
        proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg failed while encoding the video")


def render_thumbnail(text: str, out_png: Path, handle: str = config.CHANNEL_HANDLE) -> None:
    W, H = 1280, 720
    top, bottom, accent = config.THEMES[0]
    img = gradient_background(W, H, top, bottom, accent, seed=99).convert("RGBA")
    fnt = font(130)
    lines = wrap(clean(text).upper(), fnt, W - 140)
    block = text_block(lines, fnt, (255, 255, 255), stroke=10, highlight_last=config.CAPTION_HIGHLIGHT)
    if block.width > W - 60:
        block = block.resize((W - 60, int(block.height * (W - 60) / block.width)))
    img.alpha_composite(block, ((W - block.width) // 2, (H - block.height) // 2))
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 18, W, H], fill=accent + (255,))
    tag = text_block([handle], font(40), (255, 255, 255), stroke=3)
    img.alpha_composite(tag, (W - tag.width - 30, 24))
    img.convert("RGB").save(out_png)
