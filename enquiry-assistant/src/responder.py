"""Responder: turns a customer message into a safe reply.

Golden rule: every fact in a reply comes from data/business.json.
If the needed fact is missing or still marked 'TODO', we do NOT guess;
we hand over to a human instead.
"""
import re
from dataclasses import dataclass, field

from src.classifier import classify
from src.knowledge import load_knowledge, DAYS

DAY_PATTERNS = {
    "monday": r"\bmon(day)?\b", "tuesday": r"\btue(s|sday)?\b",
    "wednesday": r"\bwed(nesday)?\b", "thursday": r"\bthu(rs|rsday)?\b",
    "friday": r"\bfri(day)?\b", "saturday": r"\bsat(urday)?\b",
    "sunday": r"\bsun(day)?\b",
}

# Which FAQ topic is the customer asking about? First match wins.
TOPICS = [
    ("halal", [r"\bhalal\b"]),
    ("vegan", [r"\bvegan\b"]),
    ("vegetarian", [r"\bvegetarian\b", r"\bveggie\b"]),
    ("deals", [r"\bdeals?\b", r"\boffers?\b", r"\bspecials?\b", r"\bdiscount\w*"]),
    ("payment", [r"\bpay\w*", r"\bcard\b", r"\bcash\b", r"\bapple pay\b",
                 r"\bgoogle pay\b", r"\bcontactless\b"]),
    ("collection", [r"\bcollect\w*", r"\bpick.?up\b"]),
    ("delivery", [r"\bdeliver\w*", r"\bminimum\b"]),
    ("hours", [r"\bopen\w*", r"\bclos\w+", r"\bhours?\b", r"\bwhat time\b"]),
    ("menu", [r"\bmenu\b", r"\bprice\w*", r"\bhow much\b", r"\bcost\w*"]),
    ("contact", [r"\bphone\b", r"\bnumber\b", r"\baddress\b", r"\bwhere\b",
                 r"\blocation\b", r"\bemail\b"]),
]
_TOPICS = [(t, [re.compile(p) for p in ps]) for t, ps in TOPICS]


@dataclass
class Response:
    category: str
    reply: str
    needs_human: bool
    topic: str = ""
    matched: list = field(default_factory=list)


# ---------- helpers ----------
def _is_todo(value):
    return isinstance(value, str) and value.strip().upper().startswith("TODO")


def _ok(*values):
    """True only if every value exists and is not a TODO placeholder."""
    return all(v and not _is_todo(v) for v in values)


def _sentence(text):
    text = text.strip()
    return text if text and text[-1] in ".!?" else text + "."


def _handoff(kb, why="that"):
    phone = kb["business"]["phone"]
    tail = f" You can also call us on {phone}." if _ok(phone) else ""
    return f"I'll get a team member to confirm {why} for you.{tail}"


def _detect_topic(text):
    for topic, patterns in _TOPICS:
        if any(p.search(text) for p in patterns):
            return topic
    return None


def _days_mentioned(text):
    return [d for d in DAYS if re.search(DAY_PATTERNS[d], text)]


# ---------- topic answers (return None when facts are missing) ----------
def _hours(kb, text):
    hours = kb["opening_hours"]
    if not all(_ok(hours.get(d)) for d in DAYS):
        return None
    asked = _days_mentioned(text)
    if asked:
        d = asked[0]
        return (f"On {d.capitalize()} we're open {hours[d]}. "
                "Closing times are after midnight, so that's the following morning.")
    groups = {}
    for d in DAYS:
        groups.setdefault(hours[d], []).append(d[:3].capitalize())
    parts = [f"{', '.join(days)}: {h}" for h, days in groups.items()]
    return ("We're open seven days a week. " + ". ".join(parts) +
            ". Closing times are after midnight, so that's the following morning.")


def _delivery(kb, text):
    o = kb["ordering"]
    if not _ok(o["delivery_available"], o["delivery_area"]):
        return None
    reply = [_sentence(o["delivery_available"]),
             "We cover: " + _sentence(o["delivery_area"])]
    if _ok(o["delivery_charge"]):
        reply.append("Delivery charge: " + _sentence(o["delivery_charge"]))
    if _ok(o["minimum_order"]):
        reply.append("Minimum order: " + _sentence(o["minimum_order"]))
    if _ok(o["delivery_time"]):
        reply.append(_sentence(o["delivery_time"]))
    return " ".join(reply)


def _collection(kb, text):
    t = kb["ordering"]["collection_time"]
    return _sentence(t) if _ok(t) else None


def _payment(kb, text):
    p = kb["payments"]
    return _sentence(p) if _ok(p) else None


def _dietary(key):
    def answer(kb, text):
        v = kb["dietary"][key]
        return _sentence(v) if _ok(v) else None
    return answer


def _deals(kb, text):
    deals = kb.get("deals") or []
    if not deals or any(_is_todo(d) for d in deals):
        return None
    return "Our current deals:\n- " + "\n- ".join(deals)


def _menu(kb, text):
    cats = kb.get("menu_categories") or []
    items = kb.get("menu_highlights") or []
    if not cats or not items or any(_is_todo(i) for i in items):
        return None
    site = kb["business"].get("website", "")
    more = f" See the full menu at {site}." if _ok(site) else ""
    return ("Our menu has: " + ", ".join(cats) + ". Popular items:\n- " +
            "\n- ".join(items) + "\n" + more.strip())


def _contact(kb, text):
    b = kb["business"]
    if "email" in text:  # they asked for the email specifically
        e = b.get("email")
        return f"Our email address is {e}." if _ok(e) else None
    if not _ok(b["address"], b["phone"]):
        return None
    return f"You can find us at {b['address']}. Our phone number is {b['phone']}."


ANSWERS = {
    "hours": _hours, "delivery": _delivery, "collection": _collection,
    "payment": _payment, "halal": _dietary("halal"),
    "vegetarian": _dietary("vegetarian"), "vegan": _dietary("vegan"),
    "deals": _deals, "menu": _menu, "contact": _contact,
}


# ---------- main entry point ----------
def respond(message, kb=None):
    kb = kb or load_knowledge()
    c = classify(message)
    text = (message or "").lower()
    phone = kb["business"]["phone"]

    if c.category == "allergy":
        policy = kb["allergens"]["policy"]
        if _ok(policy):
            reply = _sentence(policy)
        else:
            reply = ("Thanks for asking. For allergy and dietary-safety questions "
                     "we always want a team member to confirm the answer, so we "
                     "never guess.")
        reply += " " + _handoff(kb, "the details")
        return Response("allergy", reply, True, "allergy", c.matched)

    if c.category == "complaint":
        reply = ("I'm sorry to hear that. I'm passing this to a team member "
                 "who will look into it.")
        if _ok(phone):
            reply += f" You can also call us on {phone}."
        return Response("complaint", reply, True, "complaint", c.matched)

    if c.category == "booking":
        b = kb["bookings"]
        if _ok(b["how_to_book"]):
            return Response("booking", _sentence(b["how_to_book"]), False,
                            "booking", c.matched)
        return Response("booking", _handoff(kb, "booking details"), True,
                        "booking", c.matched)

    if c.category == "order":
        o = kb["ordering"]
        if _ok(o["methods"]):
            reply = "Happy to help with an order! " + _sentence(o["methods"])
            if _ok(o["collection_time"]):
                reply += " Collection: " + _sentence(o["collection_time"])
            return Response("order", reply, False, "order", c.matched)
        return Response("order", _handoff(kb, "your order"), True,
                        "order", c.matched)

    if c.category == "faq":
        topic = _detect_topic(text)
        answer = ANSWERS[topic](kb, text) if topic else None
        if answer:
            return Response("faq", answer, False, topic, c.matched)
        return Response("faq", _handoff(kb), True, topic or "", c.matched)

    return Response("unknown", _handoff(kb), True, "", c.matched)


if __name__ == "__main__":
    kb = load_knowledge()
    print(f"{kb['business']['name']} assistant. Blank line to quit.")
    while True:
        msg = input("\nCustomer> ")
        if not msg:
            break
        r = respond(msg, kb)
        flag = "  [HUMAN NEEDED]" if r.needs_human else ""
        print(f"[{r.category}/{r.topic or '-'}]{flag}\n{r.reply}")
