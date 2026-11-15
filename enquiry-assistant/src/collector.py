"""Details collector: runs a short conversation to gather customer details.

Flow:
  * FAQ / booking question  -> just answer, collect nothing.
  * Order enquiry           -> ask what/how/where/name/phone.
  * Allergy / complaint / unknown / unanswerable question
                            -> ask for name + phone so a human can call back.

The result is an Enquiry record. Step 5 will store it in the database.
Nothing here is saved to disk yet.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.classifier import classify
from src.knowledge import load_knowledge
from src.responder import Response, respond, _ok

MAX_INPUT = 500  # never process absurdly long messages

CANCEL = re.compile(r"\b(cancel|stop|never ?mind|forget it|no thanks)\b")
MENU_WORDS = re.compile(
    r"\b(pizzas?|margherita|pepperoni|pasta|cheesy|amalfi|veggie supreme|"
    r"vegan supreme|meal deal|double deal|date night|full house|wings|"
    r"dough balls|garlic bread|chips|dessert|drink)\b")
# Looks like a question: has a "?" or starts with a question word.
QUESTION = re.compile(
    r"\?|^(?:do|does|did|is|are|am|can|could|will|would|what|how|when|where|"
    r"which|who|why|have|has|any)\b")
SIDE_NOTES = {
    "allergy": "Customer asked about allergens/dietary needs during the chat: staff must confirm.",
    "complaint": "Customer raised a complaint during the chat: staff to follow up.",
    "human": "Customer asked to speak to a person during the chat.",
}
POSTCODE = re.compile(r"\b([A-Za-z]{1,2}\d[A-Za-z\d]?)\s*(\d[A-Za-z]{2})\b")
NAME_PREFIX = re.compile(
    r"^(my name is|name is|it'?s|its|i am|i'm|this is|call me)\s+", re.I)


@dataclass
class Enquiry:
    kind: str                 # "order" or "callback"
    category: str             # what the classifier decided
    message: str              # the customer's first message
    name: str = ""
    phone: str = ""
    items: str = ""
    fulfilment: str = ""      # "collection" or "delivery"
    address: str = ""
    postcode: str = ""
    needs_human: bool = False
    status: str = "complete"  # "complete" or "incomplete"
    notes: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(
        timezone.utc).isoformat(timespec="seconds"))


@dataclass
class Turn:
    reply: str
    done: bool = False                 # True when an enquiry was finished
    enquiry: Enquiry = None
    response: Response = None          # the responder's answer, if any


# ---------- validators: each returns (value, error_message) ----------
def normalise_phone(text):
    """Return a UK phone number as digits (e.g. 01615264777) or None."""
    s = re.sub(r"[\s\-().]", "", text or "")
    if s.startswith("+44") or s.startswith("0044"):
        rest = s[3:] if s.startswith("+44") else s[4:]
        s = rest if rest.startswith("0") else "0" + rest
    # Mobiles (07...) are exactly 11 digits; landlines (01/02/03) are 10 or 11.
    if re.fullmatch(r"07\d{9}|0[123]\d{8,9}", s):
        return s
    return None


def parse_name(text):
    raw = (text or "").strip().replace("’", "'")
    raw = NAME_PREFIX.sub("", raw).strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z' \-]{1,49}", raw):
        return None
    return raw.title() if raw == raw.lower() else raw


def parse_postcode(text):
    m = POSTCODE.search(text or "")
    return f"{m.group(1).upper()} {m.group(2).upper()}" if m else None


def _v_items(text):
    if 3 <= len(text) <= 300:
        return text, None
    return None, "Sorry, could you tell me what you'd like to order?"


def _v_fulfilment(text):
    t = text.lower()
    if re.search(r"\bdeliver\w*|\bbring\b", t):
        return "delivery", None
    if re.search(r"\bcollect\w*|\bpick.?up\b|\bcome\b", t):
        return "collection", None
    return None, "Sorry, is that for collection or delivery?"


def _v_name(text):
    n = parse_name(text)
    return (n, None) if n else (None, "Sorry, I didn't catch your name. Could you type it again?")


def _v_phone(text):
    p = normalise_phone(text)
    return (p, None) if p else (None, "That doesn't look like a UK phone number. Could you check it? For example 07123 456789.")


def _v_address(text):
    if parse_postcode(text) and len(text) >= 8:
        return text, None
    return None, "Please include your full address with the postcode, e.g. 12 High Street, Ashton-under-Lyne OL6 1AA."


VALIDATORS = {"items": _v_items, "fulfilment": _v_fulfilment,
              "name": _v_name, "phone": _v_phone, "address": _v_address}
QUESTIONS = {
    "items": "What would you like to order?",
    "fulfilment": "Is that for collection or delivery?",
    "address": "What's the delivery address (including postcode)?",
    "name": "What's your name?",
    "phone": "And the best phone number to reach you on?",
}
FIELD_LABEL = {"items": "order", "fulfilment": "collection/delivery choice",
               "address": "delivery address", "name": "name", "phone": "phone number"}


class Conversation:
    """One customer chat. Call handle(message) for each message they send."""

    def __init__(self, kb=None, max_attempts=2):
        self.kb = kb or load_knowledge()
        self.max_attempts = max_attempts
        self._reset()

    def _reset(self):
        self.enquiry = None
        self.field = None
        self.attempts = 0

    # ---- public ----
    def handle(self, message):
        message = (message or "").strip()[:MAX_INPUT]
        if self.enquiry is not None:
            return self._collect(message)

        r = respond(message, self.kb)
        if r.category == "order":
            return self._start_order(message, r)
        if r.needs_human:
            return self._start_callback(message, r)
        return Turn(r.reply, False, None, r)

    # ---- starting ----
    def _start_order(self, message, r):
        e = Enquiry("order", "order", message)
        if MENU_WORDS.search(message.lower()):
            e.items = message  # they already told us what they want
        self.enquiry = e
        b = self.kb["business"]
        intro = "Happy to help! I'll pass your order request to the team."
        if _ok(b.get("website"), b.get("phone")):
            intro += (f" (You can also order online at {b['website']} "
                      f"or call {b['phone']}.)")
        return self._ask_next(intro, r)

    def _start_callback(self, message, r):
        self.enquiry = Enquiry("callback", r.category, message,
                               needs_human=True)
        e_note = {"allergy": "Allergy/dietary question: staff must answer.",
                  "complaint": "Complaint: staff to follow up."}.get(r.category)
        if e_note:
            self.enquiry.notes.append(e_note)
        lead = r.reply + " To make sure someone gets back to you,"
        self.field = "name"
        return Turn(f"{lead} what's your name?", False, None, r)

    # ---- collecting ----
    def _next_field(self):
        e = self.enquiry
        if e.kind == "order":
            if not e.items:
                return "items"
            if not e.fulfilment:
                return "fulfilment"
            if e.fulfilment == "delivery" and not e.address:
                return "address"
        if not e.name:
            return "name"
        if not e.phone:
            return "phone"
        return None

    def _ask_next(self, prefix, response=None):
        self.field = self._next_field()
        self.attempts = 0
        return Turn(f"{prefix} {QUESTIONS[self.field]}".strip(), False, None, response)

    def _collect(self, text):
        if CANCEL.search(text.lower()):
            self._reset()
            return Turn("No problem, I've cancelled that. Message us any time.")

        side = self._side_topic(text)
        if side:
            return self._handle_side(side, text)

        e, fld = self.enquiry, self.field
        value, error = VALIDATORS[fld](text)

        if value is None:
            self.attempts += 1
            if self.attempts >= self.max_attempts:
                return self._finish_incomplete(fld)
            return Turn(error)

        setattr(e, fld, value)
        extra = ""
        if fld == "address":
            e.postcode = parse_postcode(text)
            e.notes.append("Delivery area to be confirmed by staff.")
        if fld in ("items", "name") and classify(value).category in ("allergy",):
            e.needs_human = True
            e.notes.append("Customer mentioned an allergy: staff must confirm.")
            extra = "I've noted your allergy mention; a team member will double-check with you. "

        if self._next_field():
            return self._ask_next(extra.strip())
        return self._finish_complete(extra)

    # ---- side questions in the middle of a chat ----
    def _side_topic(self, text):
        """If the customer asked something else instead of answering, say what."""
        cat = classify(text).category
        asking = bool(QUESTION.search(text.lower().strip()))
        if cat in ("complaint", "human"):
            return cat
        if cat == "allergy" and (asking or self.field != "items"):
            return cat   # (an allergy written inside their order is kept as the order)
        if cat in ("faq", "booking") and asking:
            return cat
        if cat == "chitchat":
            return cat
        return None

    def _handle_side(self, cat, text):
        """Answer the side question, then go back to the question we were asking."""
        e = self.enquiry
        r = respond(text, self.kb)
        if cat in SIDE_NOTES:
            e.needs_human = True
            if SIDE_NOTES[cat] not in e.notes:
                e.notes.append(SIDE_NOTES[cat])
        what = "order" if e.kind == "order" else "enquiry"
        return Turn(f"{r.reply} Back to your {what}: {QUESTIONS[self.field]}",
                    False, None, r)

    # ---- finishing ----
    def _finish_complete(self, extra=""):
        e = self.enquiry
        e.status = "complete"
        phone = self.kb["business"]["phone"]
        if e.kind == "order":
            summary = [f"Order: {e.items}", f"{e.fulfilment.capitalize()}"]
            if e.address:
                summary.append(f"To: {e.address}")
            reply = (f"{extra}Thanks, {e.name}. I've sent your order request to "
                     f"the team. A team member will contact you on {e.phone} to "
                     "confirm. Your order is NOT confirmed until they do.\n"
                     + "\n".join(f"- {s}" for s in summary))
        else:
            reply = (f"{extra}Thanks, {e.name}. A team member will call you back "
                     f"on {e.phone}.")
            if _ok(phone):
                reply += f" If it's urgent, call us on {phone}."
        return self._end(reply, e)

    def _finish_incomplete(self, fld):
        e = self.enquiry
        e.status = "incomplete"
        e.needs_human = True
        e.notes.append(f"Customer did not give a valid {FIELD_LABEL[fld]}.")
        phone = self.kb["business"]["phone"]
        reply = "No problem, I'll pass what I have to the team."
        if _ok(phone):
            reply += f" If it's urgent, please call us on {phone}."
        return self._end(reply, e)

    def _end(self, reply, enquiry):
        self._reset()
        return Turn(reply, True, enquiry)


if __name__ == "__main__":
    from dataclasses import asdict
    import json
    from src.database import connect, save_enquiry, DEFAULT_DB
    from src.notifier import notify_new
    db = connect()
    conv = Conversation()
    print("Fire Away Ashton assistant (DEMO: use fake details). Blank line to quit.")
    print(f"Finished enquiries are saved to {DEFAULT_DB}")
    while True:
        msg = input("\nCustomer> ")
        if not msg:
            break
        t = conv.handle(msg)
        print(f"Assistant> {t.reply}")
        if t.done:
            row_id = save_enquiry(db, t.enquiry)
            print(f"\n[ENQUIRY SAVED as #{row_id}] notifications: {notify_new(db)}")
            print(json.dumps(asdict(t.enquiry), indent=2))
