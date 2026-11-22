"""Default settings for the faceless video pipeline. Override most of them from the CLI."""

import os

# Channel branding. Fill these in once you've created your channel.
# Leave CHANNEL_HANDLE empty ("") to show no watermark on videos.
CHANNEL_NAME = ""          # e.g. "Learn AI Daily"
CHANNEL_HANDLE = ""        # e.g. "@learnaidaily"
NICHE = (
    "Learn AI: how AI actually works explained simply (tokens, training, prompts, context, agents), "
    "and practical ways to use Claude to learn, study, work and create"
)

# Claude model used to write scripts and ideas
MODEL = "claude-opus-5-5"

# Video
FPS = 30

# Voice. edge-tts is free and sounds natural; list voices with `edge-tts --list-voices`.
EDGE_VOICE = "en-US-AndrewNeural"
EDGE_RATE = "+8%"          # slightly faster delivery suits Shorts
ESPEAK_VOICE = "en-us"     # offline fallback voice (robotic, but works without internet)

# Background music volume relative to the voice (0.0 - 1.0)
MUSIC_VOLUME = 0.12

# Remotion renders with its own downloaded Chrome. Set REMOTION_BROWSER to use another one.
BROWSER_EXECUTABLE = os.environ.get("REMOTION_BROWSER", "")
