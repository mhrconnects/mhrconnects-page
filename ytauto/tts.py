"""Text-to-speech: edge-tts (free, natural voices, needs internet) with an offline espeak-ng fallback."""

import asyncio
import os
import shutil
import subprocess
import wave
from pathlib import Path

from . import config

_warned = False


def _to_wav(src: Path, dst: Path, pad_seconds: float) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
         "-af", f"apad=pad_dur={pad_seconds}", "-ar", "44100", "-ac", "1", str(dst)],
        check=True,
    )


def _edge(text: str, out_mp3: Path, voice: str, rate: str) -> None:
    import edge_tts

    # edge-tts doesn't read proxy environment variables itself; pass one through if set
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None

    async def run():
        await edge_tts.Communicate(text, voice, rate=rate, proxy=proxy).save(str(out_mp3))

    asyncio.run(run())
    if not out_mp3.exists() or out_mp3.stat().st_size == 0:
        raise RuntimeError("edge-tts produced no audio")


def _espeak(text: str, out_wav: Path, voice: str) -> None:
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise RuntimeError(
            "No offline voice available. Install espeak-ng (apt install espeak-ng / brew install espeak-ng) "
            "or make sure edge-tts can reach the internet."
        )
    subprocess.run([exe, "-v", voice, "-s", "165", "-w", str(out_wav), text], check=True)


def synthesize(text: str, out_wav: Path, engine: str = "auto", voice: str | None = None,
               pad_seconds: float = 0.3) -> float:
    """Speak `text` into a 44.1 kHz mono WAV and return its duration in seconds."""
    global _warned
    raw = out_wav.with_suffix(".raw" + (".mp3" if engine != "espeak" else ".wav"))
    used = engine
    if engine in ("auto", "edge"):
        try:
            _edge(text, raw, voice or config.EDGE_VOICE, config.EDGE_RATE)
            used = "edge"
        except Exception as exc:  # network blocked, service change, etc.
            if engine == "edge":
                raise
            if not _warned:
                print(f"  ! edge-tts unavailable ({type(exc).__name__}); falling back to offline espeak-ng voice")
                _warned = True
            used = "espeak"
            raw = out_wav.with_suffix(".raw.wav")
    if used == "espeak":
        _espeak(text, raw, voice if engine == "espeak" and voice else config.ESPEAK_VOICE)

    _to_wav(raw, out_wav, pad_seconds)
    raw.unlink(missing_ok=True)
    with wave.open(str(out_wav)) as w:
        return w.getnframes() / w.getframerate()


def concat_wavs(parts: list[Path], out_wav: Path) -> None:
    with wave.open(str(parts[0])) as first:
        params = first.getparams()
    with wave.open(str(out_wav), "wb") as out:
        out.setparams(params)
        for part in parts:
            with wave.open(str(part)) as w:
                out.writeframes(w.readframes(w.getnframes()))
