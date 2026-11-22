"""Text-to-speech with word timings.

edge-tts gives free natural voices plus exact word timings (needs internet).
espeak-ng is an offline fallback; its word timings are estimated.
"""

import asyncio
import os
import re
import shutil
import subprocess
import wave
from pathlib import Path

from . import config

Word = tuple[str, float, float]  # text, start seconds, end seconds (relative to the clip)
_warned = False


def _to_wav(src: Path, dst: Path, pad_seconds: float) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
         "-af", f"apad=pad_dur={pad_seconds}", "-ar", "44100", "-ac", "1", str(dst)],
        check=True,
    )


def _wav_seconds(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def _attach_punctuation(narration: str, words: list[Word]) -> list[Word]:
    """edge-tts word boundaries drop punctuation; copy it back from the script so captions break naturally."""
    tokens = narration.split()
    out, j = [], 0
    norm = lambda s: re.sub(r"[^\w']", "", s.lower())
    for text, s, e in words:
        k = j
        while k < len(tokens) and norm(tokens[k]) != norm(text):
            k += 1
        if k < len(tokens) and k - j <= 2:
            out.append((tokens[k], s, e))
            j = k + 1
        else:
            out.append((text, s, e))
    return out


def _edge(text: str, out_mp3: Path, voice: str, rate: str) -> list[Word]:
    import edge_tts

    # edge-tts doesn't read proxy environment variables itself; pass one through if set
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None

    async def run() -> list[Word]:
        comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary", proxy=proxy)
        audio, words = bytearray(), []
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append((chunk["text"], start, start + chunk["duration"] / 1e7))
        out_mp3.write_bytes(bytes(audio))
        return words

    words = asyncio.run(run())
    if out_mp3.stat().st_size == 0:
        raise RuntimeError("edge-tts produced no audio")
    return _attach_punctuation(text, words)


def _espeak(text: str, out_wav: Path, voice: str) -> None:
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise RuntimeError(
            "No offline voice available. Install espeak-ng (apt install espeak-ng / brew install espeak-ng) "
            "or make sure edge-tts can reach the internet."
        )
    subprocess.run([exe, "-v", voice, "-s", "165", "-w", str(out_wav), text], check=True)


def estimate_words(text: str, speech_seconds: float) -> list[Word]:
    tokens = text.split()
    weights = [len(t) + 2 for t in tokens]
    total = sum(weights) or 1
    out, t = [], 0.05
    for tok, w in zip(tokens, weights):
        d = (speech_seconds - 0.1) * w / total
        out.append((tok, t, t + d))
        t += d
    return out


def synthesize(text: str, out_wav: Path, engine: str = "auto", voice: str | None = None,
               pad_seconds: float = 0.35) -> tuple[float, list[Word]]:
    """Speak `text` into a 44.1 kHz mono WAV. Returns (duration seconds, word timings)."""
    global _warned
    words: list[Word] | None = None
    raw = out_wav.with_suffix(".raw.mp3")
    used = engine
    if engine in ("auto", "edge"):
        try:
            words = _edge(text, raw, voice or config.EDGE_VOICE, config.EDGE_RATE)
            used = "edge"
        except Exception as exc:  # network blocked, service change, etc.
            if engine == "edge":
                raise
            if not _warned:
                print(f"  ! edge-tts unavailable ({type(exc).__name__}); using offline espeak-ng voice")
                _warned = True
            used = "espeak"
    if used == "espeak":
        raw = out_wav.with_suffix(".raw.wav")
        _espeak(text, raw, voice if engine == "espeak" and voice else config.ESPEAK_VOICE)

    _to_wav(raw, out_wav, pad_seconds)
    raw.unlink(missing_ok=True)
    duration = _wav_seconds(out_wav)
    if not words:
        words = estimate_words(text, duration - pad_seconds)
    return duration, words


def concat_wavs(parts: list[tuple[Path, float]], out_wav: Path) -> None:
    """Join WAVs, padding each with silence to exactly its target length (keeps audio frame-aligned)."""
    with wave.open(str(parts[0][0])) as first:
        params = first.getparams()
    with wave.open(str(out_wav), "wb") as out:
        out.setparams(params)
        for path, target in parts:
            with wave.open(str(path)) as w:
                data = w.readframes(w.getnframes())
                n = w.getnframes()
            want = int(round(target * params.framerate))
            out.writeframes(data[: want * params.sampwidth * params.nchannels])
            if want > n:
                out.writeframes(b"\x00" * (want - n) * params.sampwidth * params.nchannels)
