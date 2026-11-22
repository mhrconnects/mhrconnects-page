"""Write video scripts (and topic ideas) with Claude, returned as validated JSON."""

import json

import anthropic

from . import config

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "YouTube title, under 70 characters, curiosity-driven, no emojis"},
        "description": {"type": "string", "description": "2-4 sentence YouTube description ending with 3-5 hashtags including #shorts"},
        "tags": {"type": "array", "items": {"type": "string"}, "description": "8-15 search tags"},
        "thumbnail_text": {"type": "string", "description": "2-5 punchy words for the thumbnail"},
        "scenes": {
            "type": "array",
            "description": "5-8 scenes. Scene 1 is the hook, the last scene is a short call to action.",
            "items": {
                "type": "object",
                "properties": {
                    "narration": {"type": "string", "description": "What the voiceover says, 1-3 short spoken sentences"},
                    "on_screen_text": {"type": "string", "description": "Headline shown on screen, max 6 words, no emojis"},
                },
                "required": ["narration", "on_screen_text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "description", "tags", "thumbnail_text", "scenes"],
    "additionalProperties": False,
}

IDEAS_SCHEMA = {
    "type": "object",
    "properties": {
        "ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "why_it_works": {"type": "string"},
                },
                "required": ["topic", "why_it_works"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["ideas"],
    "additionalProperties": False,
}


def _system_prompt(channel: str, niche: str) -> str:
    name = f'"{channel}", ' if channel else ""
    return f"""You write scripts for {name}a faceless YouTube Shorts channel. Niche: {niche}.

The viewer hears a voiceover over animated text slides; there is no presenter on camera.
Write for the ear: short sentences, plain words, one idea per scene, no filler like "In this video".
The first scene must hook within 2 seconds with a bold claim, a surprising fact, or a question.
Give concrete, accurate, actionable details (real tool names, real steps). Never invent features,
prices, or statistics; if you are unsure something is current, describe it generally instead.
Never promise specific earnings or "get rich quick" results; say what the work involves.
Total narration should be 110-150 words so the Short lands at 40-58 seconds.
End with a one-line call to action asking viewers to follow for more tips."""


def _call_claude(system: str, user: str, schema: dict) -> dict:
    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=config.MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # if the request is declined, the API retries it on a suitable fallback model
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}},
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined this request: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Claude's reply was cut off (max_tokens); try a narrower topic.")
    text = "".join(block.text for block in response.content if block.type == "text")
    return json.loads(text)


def generate_script(topic: str, channel: str = config.CHANNEL_NAME, niche: str = config.NICHE) -> dict:
    return _call_claude(
        _system_prompt(channel, niche),
        f"Write a YouTube Short script about: {topic}",
        SCRIPT_SCHEMA,
    )


def generate_ideas(count: int, channel: str = config.CHANNEL_NAME, niche: str = config.NICHE) -> list[dict]:
    data = _call_claude(
        _system_prompt(channel, niche),
        f"Suggest {count} distinct YouTube Short topics for this channel that people actively search for "
        "or share. Mix evergreen how-tos with tool spotlights. Each topic is one specific sentence.",
        IDEAS_SCHEMA,
    )
    return data["ideas"]
