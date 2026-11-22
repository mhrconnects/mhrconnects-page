# Faceless YouTube Shorts automation

A faceless video pipeline for an "AI to make money" channel: AI side hustles, freelancing with AI,
AI tools for small business. Set your channel name and handle in `ytauto/config.py`.

```
topic ──► Claude writes script ──► AI voiceover ──► animated 1080×1920 video ──► video.mp4
                                                                              thumbnail.png
                                                                              captions.srt
                                                                              metadata.json (title, description, tags)
```

Each video: a hook, 4–6 tip scenes, a call to action, word-by-word pop-up captions, a progress bar,
a slow background drift, and your `@handle` watermark (optional). A 40-second Short renders in about 20 seconds.

## Setup (once)

1. Install **Python 3.10+** and **ffmpeg** (Windows: `winget install ffmpeg` · Mac: `brew install ffmpeg`).
2. Install the Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Get an Anthropic API key from https://console.anthropic.com and set it:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...        # Mac/Linux
   setx ANTHROPIC_API_KEY sk-ant-...          # Windows (then open a new terminal)
   ```
4. Optional: install `espeak-ng` as an offline backup voice. The main voice (Microsoft Edge neural
   voices via `edge-tts`) is free but needs internet.

## Use it

```bash
# Try it without an API key, using the included sample script
python -m ytauto make --script examples/sample_script.json

# One video from a topic
python -m ytauto make "How to use ChatGPT to plan your week in 5 minutes"

# Review the script first, edit the JSON, then render
python -m ytauto make "Best free AI image tools" --script-only
python -m ytauto make --script output/<file>.json

# Brainstorm 20 topics, then make all of them
python -m ytauto ideas -n 20
python -m ytauto batch ideas.txt
```

Useful options: `--voice en-GB-RyanNeural` (list voices with `edge-tts --list-voices`),
`--music track.mp3` (royalty-free only, e.g. from the YouTube Audio Library),
`--handle @yourhandle`, `--out folder`.

Channel name, niche, colours, voice and model live in `ytauto/config.py`.

## Uploading

Upload `video.mp4` in YouTube Studio, paste the title/description/tags from `metadata.json`,
and upload `captions.srt` under Subtitles. When uploading, set **"Altered or synthetic content"**
to *Yes* because the voice is AI-generated. YouTube requires this disclosure for realistic AI voices.

Always watch each video before posting. Claude is told not to invent facts, but AI tools change fast,
so check that tool names, features and prices are still correct.

## Project layout

| File | What it does |
|---|---|
| `ytauto/script_gen.py` | Claude prompt + JSON schema for scripts and topic ideas |
| `ytauto/tts.py` | edge-tts voiceover, espeak-ng offline fallback |
| `ytauto/render.py` | draws frames (Pillow) and encodes with ffmpeg; thumbnail |
| `ytauto/pipeline.py` | ties it together, writes captions + metadata |
| `ytauto/config.py` | branding, voice, colours, video size |
