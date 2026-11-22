# Faceless "Learn AI" YouTube Shorts maker

Claude writes the scripts and ideas, a free AI voice reads them, and [Remotion](https://www.remotion.dev)
turns them into premium motion-graphics Shorts (1080×1920).

```
topic ──► Claude writes script + picks a visual per scene ──► voiceover with word timings
      ──► Remotion motion graphics ──► video.mp4, thumbnail.png, captions.srt, metadata.json
```

**What every video gets:** kinetic titles that slam in, glowing glass cards, a moving 3D grid floor,
floating particles, film grain, light-sweep transitions, word-by-word karaoke captions, a progress bar,
whoosh/pop sound effects (generated, so no copyright issues), and a matching thumbnail.

**Scene layouts Claude can choose from:**
`hook` (opening title) · `concept` (key term + animated icon) · `list` (numbered cards) ·
`flow` (step-by-step diagram) · `compare` (weak vs strong) · `stat` (counting number + ring) ·
`chat` (a prompt typed to Claude and the answer) · `cta` (follow button).

## Setup (once)

1. Install **Python 3.10+**, **Node.js 18+** and **ffmpeg**
   (Windows: `winget install Python.Python.3.12 OpenJS.NodeJS.LTS ffmpeg` · Mac: `brew install python node ffmpeg`).
2. Install the packages:
   ```bash
   pip install -r requirements.txt
   cd remotion && npm install && cd ..
   ```
   The first render downloads a small headless Chrome that Remotion uses to draw frames.
3. For Claude-written scripts, get an API key at https://console.anthropic.com and set it:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...        # Mac/Linux
   setx ANTHROPIC_API_KEY sk-ant-...          # Windows (then open a new terminal)
   ```

## Use it

```bash
# Ready-made scripts (no API key needed)
python -m ytauto make --script examples/01_tokens.json
python -m ytauto make --script examples/02_hallucinations.json
python -m ytauto make --script examples/03_prompt_formula.json

# Claude writes a new one
python -m ytauto make "What is a context window?"

# Review/edit the script before rendering
python -m ytauto make "How AI image generators work" --script-only
python -m ytauto make --script output/<file>.json

# Claude brainstorms 30 topics, then make them all
python -m ytauto ideas -n 30
python -m ytauto batch ideas.txt
```

### Long-form tutorials (5-7 min, 16:9)

```bash
# Ready-made "Claude Basics" tutorial
python -m ytauto make --script examples/long_01_claude_basics.json

# Claude writes a new long tutorial
python -m ytauto make "How to use Claude for studying" --long
```

Long videos add two scene types: `app` (a Claude-style chat window: a cursor clicks buttons, prompts type out,
answers stream in, files get attached) and `section` (chapter title cards). Scenes with a `"chapter"` name
become YouTube chapters in `metadata.json`'s description. The app window is a stylised recreation with no logos;
mixing in real screen recordings of claude.ai makes tutorials feel even more authentic.

Options: `--voice en-GB-RyanNeural` (see `edge-tts --list-voices`), `--music track.mp3`
(royalty-free only, e.g. YouTube Audio Library), `--handle @yourchannel`, `--no-sfx`, `--out folder`.
Set your channel name, handle, niche and voice in `ytauto/config.py`.

**Preview and tweak the design live:** `cd remotion && npm run studio` opens Remotion Studio in your browser.

## Script format

Each scene is `{ "narration": "...", "visual": { "type": "...", "title": "...", ... } }`.
Wrap one word of a title in `*asterisks*` to give it the gradient highlight. See `examples/` for every type.

## Before uploading

- Watch every video. Check facts: Claude is told not to invent anything, but always verify.
- In YouTube Studio set **"Altered or synthetic content" → Yes** (AI voice).
- Paste title/description/tags from `metadata.json` and upload `captions.srt` as subtitles.
- Remotion is free for individuals and companies of up to 3 people; larger companies need a licence
  (see remotion.dev/license).

## Project layout

| Path | What it does |
|---|---|
| `ytauto/script_gen.py` | Claude prompt + JSON schema for scripts and topic ideas |
| `ytauto/tts.py` | edge-tts voice with word timings, espeak-ng offline fallback |
| `ytauto/pipeline.py` | runs everything, calls Remotion, writes captions + metadata |
| `remotion/src/scenes/` | the 8 animated scene layouts |
| `remotion/src/layers/` | background, captions, transitions, progress bar |
| `remotion/src/theme.ts` | colours, fonts, animation curves |
