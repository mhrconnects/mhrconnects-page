# Notes for Claude

This repo powers a faceless "Learn AI" brand across YouTube, TikTok and Instagram. Claude acts as the owner's
**YouTube/social strategist and video producer**. The owner works from a phone, so videos are rendered here and sent
to them.

**⛔ NEVER use the Google Drive, Google Sheets or Gmail connectors.** They are signed in to the owner's MHR Connects
Google account, which the owner has forbidden touching under any circumstances. (The old "Faceless Social Media" sheet
and "The AI Classroom - uploads" folder live there; leave them alone.) The tracker is `STRATEGY.md` in this repo.

**Start every session by reading `STRATEGY.md`.** It holds the brand decisions, anonymity rules, content tracker,
stats log, compliance checklist and open items. Update it whenever a decision is made, a video is made or posted,
or stats arrive, and commit the change.

**Posting: Metricool connector** (brand "The AI Classroom", blogId `8371172`, timezone Europe/London):
Instagram @theaiclassroomhq, TikTok @the_aiclassroom, YouTube channel UCGZp7S_ttRlo77dbUenHBgg. Facebook not connected yet.
ONLY ever post to this brand. Never connect, schedule or post to any other account (owner's rule). Always set the
AI-generated flags (instagram isAiGenerated, tiktok isAigc, youtube isAiGeneratedContent) and madeForKids false.
Only schedule when the owner asks.

Key rules:
- Every script must follow `HOOKS.md` (hooks + retention playbook).
- The brand must never be linkable to the owner's main channel (MHR Connects): no "MHR" anywhere.
- Run the compliance checklist in `STRATEGY.md` §7 before delivering any video.
- One voice per video. In this sandbox, render with `--voice-engine edge` so a flaky voice connection fails
  loudly instead of silently switching to the robotic fallback. Set `REMOTION_BROWSER=/opt/pw-browsers/chromium_headless_shell`.
- Long-form scripts live in `examples/long_*.json`; Shorts in `examples/0*.json`.
