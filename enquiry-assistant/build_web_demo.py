"""Builds dist/fireaway-demo.html: the whole assistant in ONE self-contained
page that runs in a browser (no server, nothing stored or sent).

    python3 build_web_demo.py

Rules and business facts are exported from the Python modules so there is a
single source of truth; web_demo/engine.js is checked against Python by
tests/test_js_parity.py.
"""
import json
from pathlib import Path

from src import classifier, collector, responder
from src.demo_data import SAMPLES
from src.knowledge import DAYS, load_knowledge

ROOT = Path(__file__).resolve().parent


def build_data():
    return {
        "rules": classifier.RULES,
        "priority": classifier.PRIORITY,
        "weak_order": [p.pattern for p in classifier.WEAK_ORDER],
        "chitchat": classifier.CHITCHAT.pattern,
        "human_categories": sorted(classifier.HUMAN_CATEGORIES),
        "topics": [[t, ps] for t, ps in responder.TOPICS],
        "day_patterns": responder.DAY_PATTERNS,
        "menu_words": collector.MENU_WORDS.pattern,
        "cancel": collector.CANCEL.pattern,
        "postcode": collector.POSTCODE.pattern,
        "name_prefix": collector.NAME_PREFIX.pattern,
        "max_input": collector.MAX_INPUT,
        "days": DAYS,
        "kb": load_knowledge(),
        "samples": SAMPLES,
    }


def build(out=ROOT / "dist" / "fireaway-demo.html"):
    template = (ROOT / "web_demo" / "template.html").read_text(encoding="utf-8")
    engine = (ROOT / "web_demo" / "engine.js").read_text(encoding="utf-8")
    data = json.dumps(build_data(), ensure_ascii=False).replace("</", "<\\/")
    html = template.replace("/*ENGINE*/", engine).replace("/*DATA*/", data)
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    p = build()
    print(f"Built {p} ({p.stat().st_size // 1024} KB)")
