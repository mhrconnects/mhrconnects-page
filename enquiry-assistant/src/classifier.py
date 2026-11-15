"""Enquiry classifier: decides what KIND of message a customer sent.

This is deliberately simple keyword matching (no AI yet) so you can see
exactly why each decision was made. Later we can swap in Claude behind the
same classify() function without changing the rest of the system.
"""
import re
from dataclasses import dataclass, field

# Order matters: earlier categories win when a message matches several.
# Safety-critical categories come first.
PRIORITY = ["allergy", "complaint", "booking", "order", "faq"]

# Each pattern is a regular expression. \b means "word boundary" so that
# 'book' matches 'book' and 'booking' but not 'facebook'.
RULES = {
    "allergy": [
        r"\ballerg\w*", r"\bgluten\b", r"\bnuts?\b", r"\bpeanuts?\b",
        r"\bcoeliac\b", r"\bceliac\b", r"\blactose\b", r"\bintoleran\w*",
        r"\bdairy.free\b", r"\banaphyla\w*",
    ],
    "complaint": [
        r"\bcomplain\w*", r"\brefund\w*", r"\bcold\b", r"\bwrong\b",
        r"\bmissing\b", r"\bterrible\b", r"\bdisgusting\b", r"\bunhappy\b",
        r"\bwhere is my\b", r"\bnever arrived\b", r"\bstill waiting\b",
        r"\blate\b", r"\bmoney back\b", r"\bnot happy\b", r"\brude\b",
    ],
    "booking": [
        r"\bbook\w*", r"\breserv\w*", r"\btables?\b", r"\bparty of\b",
    ],
    "order": [
        r"\border\b", r"\bi.d like\b", r"\bi would like\b", r"\bi want\b",
        r"\bcan i (get|have)\b", r"\bcould i (get|have)\b",
        r"\bpizzas?\b", r"\bmargherita\b", r"\bpasta\b", r"\bcollection\b",
        r"\bdeliver me\b",
    ],
    "faq": [
        r"\bopen\w*", r"\bclos\w+", r"\bhours?\b", r"\bwhat time\b",
        r"\bdeliver\w*", r"\bmenu\b", r"\bprice\w*", r"\bhow much\b",
        r"\bhalal\b", r"\bvegetarian\b", r"\bvegan\b", r"\bpay\w*",
        r"\bcard\b", r"\bcash\b", r"\bphone\b", r"\baddress\b",
        r"\bwhere are you\b", r"\bminimum\b",
    ],
}

# Categories that must always be handled by a person.
HUMAN_CATEGORIES = {"allergy", "complaint", "unknown"}

_COMPILED = {
    cat: [re.compile(p) for p in patterns] for cat, patterns in RULES.items()
}


@dataclass
class Classification:
    category: str
    matched: list = field(default_factory=list)  # which rules fired (for debugging)
    needs_human: bool = False


def _normalise(message):
    """Lower-case and tidy the text so matching is predictable."""
    text = message.lower().replace("’", "'")  # curly apostrophe -> '
    return re.sub(r"\s+", " ", text).strip()


def classify(message):
    """Return a Classification for one customer message."""
    text = _normalise(message or "")
    hits = {}
    for category in PRIORITY:
        found = [p.pattern for p in _COMPILED[category] if p.search(text)]
        if found:
            hits[category] = found

    if not hits:
        return Classification("unknown", [], needs_human=True)

    # First category in PRIORITY order that matched wins.
    for category in PRIORITY:
        if category in hits:
            return Classification(
                category, hits[category],
                needs_human=category in HUMAN_CATEGORIES)


if __name__ == "__main__":
    print("Type a customer message (blank line to quit).")
    while True:
        msg = input("> ")
        if not msg:
            break
        r = classify(msg)
        flag = "  -> HUMAN NEEDED" if r.needs_human else ""
        print(f"  {r.category}{flag}")
