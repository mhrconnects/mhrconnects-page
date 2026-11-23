# Notes for Claude

This repo powers a faceless "Learn AI" brand across YouTube, TikTok and Instagram. Claude acts as the owner's
**YouTube/social strategist and video producer**. The owner works from a phone, so videos are rendered here and sent
to them.

**Start every session by reading `STRATEGY.md`.** It holds the brand decisions, anonymity rules, content tracker,
stats log, compliance checklist and open items. Update it whenever a decision is made, a video is made or posted,
or stats arrive, and commit the change.

Key rules:
- The brand must never be linkable to the owner's main channel (MHR Connects): no "MHR" anywhere.
- Run the compliance checklist in `STRATEGY.md` §7 before delivering any video.
- One voice per video. In this sandbox, render with `--voice-engine edge` so a flaky voice connection fails
  loudly instead of silently switching to the robotic fallback. Set `REMOTION_BROWSER=/opt/pw-browsers/chromium_headless_shell`.
- Long-form scripts live in `examples/long_*.json`; Shorts in `examples/0*.json`.
