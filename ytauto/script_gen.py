"""Write video scripts (and topic ideas) with Claude, returned as validated JSON."""

import json

import anthropic

from . import config

ICONS = ["brain", "chip", "chat", "spark", "book", "code", "image", "shield", "bolt", "eye", "search",
         "layers", "target", "globe", "idea", "bot", "data", "magic", "doc", "learn", "rocket", "puzzle",
         "network", "time"]
VISUAL_TYPES = ["hook", "concept", "list", "compare", "flow", "stat", "chat", "cta"]

VISUAL_GUIDE = """Each scene has a motion-graphic "visual". Pick the type that best SHOWS what the narration says:
- hook: first scene only. title = 3-6 punchy words. subtitle = tiny label like "AI in 60 seconds".
- concept: one key term. title = the term (1-3 words). subtitle = plain definition, max 12 words. icon required.
- list: title (max 5 words) + 2-4 items, each max 5 words.
- flow: a process or pipeline. title (max 5 words) + 3-4 steps in order, each max 5 words.
- compare: title (max 4 words) + exactly 2 items formatted "Label: detail" (left = worse/old, right = better/new), detail max 9 words.
- stat: title (max 4 words), number (max 7 characters, e.g. "200K", "90%", "1M"), subtitle max 8 words. Only well-established numbers.
- chat: shows a prompt being typed to Claude and its answer. title = short label like "Try this prompt". items = [the user's prompt (max 12 words), a realistic short answer (max 25 words)].
- cta: last scene only. title = 2-5 words like "Learn AI *daily*". subtitle optional.
In every title, wrap the single most important word in *asterisks* so it gets the highlight colour.
Use 6-8 scenes, vary the visual types, and never use the same type twice in a row.
The visual should match what the narration is saying at that moment, so viewers see and hear the same idea."""

VISUAL_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": VISUAL_TYPES},
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "items": {"type": "array", "items": {"type": "string"}},
        "icon": {"type": "string", "enum": ICONS},
        "number": {"type": "string"},
    },
    "required": ["type", "title"],
    "additionalProperties": False,
}

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "YouTube title, under 70 characters, curiosity-driven, no emojis"},
        "description": {"type": "string", "description": "2-4 sentence YouTube description ending with 3-5 hashtags including #shorts"},
        "tags": {"type": "array", "items": {"type": "string"}, "description": "8-15 search tags"},
        "thumbnail_text": {"type": "string", "description": "2-5 punchy words, one wrapped in *asterisks*"},
        "thumbnail_icon": {"type": "string", "enum": ICONS},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "narration": {"type": "string", "description": "What the voiceover says, 1-3 short spoken sentences"},
                    "visual": VISUAL_SCHEMA,
                },
                "required": ["narration", "visual"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "description", "tags", "thumbnail_text", "thumbnail_icon", "scenes"],
    "additionalProperties": False,
}

IDEAS_SCHEMA = {
    "type": "object",
    "properties": {
        "ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"topic": {"type": "string"}, "why_it_works": {"type": "string"}},
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
    return f"""You write scripts for {name}a faceless YouTube Shorts channel that teaches AI. Niche: {niche}.

The viewer hears a voiceover over premium animated motion graphics; there is no presenter on camera.
Write for the ear: short sentences, plain words, one idea per scene, no filler like "In this video".
The first scene must hook within 2 seconds with a bold claim, a surprising fact, or a question.
Teach one thing well. Viewers should finish the Short able to explain or use it.
When showing how to use an AI assistant, use Claude as the example.
Be accurate. Never invent product features, prices, benchmarks or statistics; if you are unsure
something is current, explain the idea generally instead of naming specifics.
Total narration: 90-130 words, so the Short lands at 35-55 seconds.
End with a one-line call to action to follow for daily AI lessons.

{VISUAL_GUIDE}"""


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
    return _call_claude(_system_prompt(channel, niche), f"Write a YouTube Short script about: {topic}", SCRIPT_SCHEMA)


def generate_ideas(count: int, channel: str = config.CHANNEL_NAME, niche: str = config.NICHE) -> list[dict]:
    data = _call_claude(
        _system_prompt(channel, niche),
        f"Suggest {count} distinct YouTube Short topics for this channel that beginners actively search for "
        "or would share. Mix 'how AI works' explainers, myths vs facts, and practical Claude tips. "
        "Each topic is one specific sentence.",
        IDEAS_SCHEMA,
    )
    return data["ideas"]
