"""Default settings for the faceless video pipeline. Override most of them from the CLI."""

# Channel branding. Fill these in once you've created your channel.
# Leave CHANNEL_HANDLE empty ("") to show no watermark on videos.
CHANNEL_NAME = ""          # e.g. "AI Money Moves"
CHANNEL_HANDLE = ""        # e.g. "@aimoneymoves"
NICHE = ("Using AI to make money and save time: AI side hustles, freelancing with AI, "
         "AI tools for small business, and practical AI productivity tips")

# Claude model used to write scripts
MODEL = "claude-opus-5-5"

# Video format (YouTube Shorts = vertical 9:16)
WIDTH = 1080
HEIGHT = 1920
FPS = 30

# Voice. edge-tts is free and sounds natural; list voices with `edge-tts --list-voices`.
EDGE_VOICE = "en-US-AndrewNeural"
EDGE_RATE = "+8%"          # slightly faster delivery suits Shorts
ESPEAK_VOICE = "en-us"     # offline fallback voice (robotic, but works without internet)

# Background music volume relative to the voice (0.0 - 1.0)
MUSIC_VOLUME = 0.12

# Colour themes (top gradient, bottom gradient, accent). One is picked per scene.
THEMES = [
    ((14, 18, 48), (52, 12, 84), (0, 229, 255)),
    ((6, 30, 40), (10, 70, 80), (124, 255, 178)),
    ((40, 10, 30), (90, 20, 50), (255, 196, 0)),
    ((10, 14, 30), (24, 44, 96), (255, 92, 138)),
]
CAPTION_COLOR = (255, 255, 255)
CAPTION_HIGHLIGHT = (255, 221, 0)
