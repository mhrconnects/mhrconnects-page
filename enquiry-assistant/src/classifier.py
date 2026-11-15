"""Enquiry classifier: decides what KIND of message a customer sent.

This is deliberately simple keyword matching (no AI yet) so you can see
exactly why each decision was made. Later we can swap in Claude behind the
same classify() function without changing the rest of the system.
"""
import re
from dataclasses import dataclass, field

# Order matters: earlier categories win when a message matches several.
# Safety-critical categories come first.
PRIORITY = ["allergy", "complaint", "human", "booking", "order", "faq"]

# Each pattern is a regular expression. \b means "word boundary" so that
# 'book' matches 'book' and 'booking' but not 'facebook'.
RULES = {
    "allergy": [
        r"\ballerg\w*", r"\bgluten\b", r"\bnuts?\b", r"\bpeanuts?\b",
        r"\bcoeliac\b", r"\bceliac\b", r"\blactose\b", r"\bintoleran\w*",
        r"\bdairy.free\b", r"\banaphyla\w*", r"\bdairy\b", r"\bmilk\b", r"\bsesame\b",
        r"\bshellfish\b", r"\bcrustacean\w*", r"\bmollus\w*", r"\bsoya?\b",
        r"\beggs?\b", r"\bmustard\b", r"\bcelery\b", r"\bsulphite\w*",
        r"\blupin\b", r"\bwheat\b", r"\bmay contain\b", r"\btraces?\b",
        r"\bcross.?contamin\w*", r"\bcan'?t eat\b", r"\bcannot eat\b",
        r"\bfree from\b",
    ],
    "complaint": [
        r"\bcomplain\w*", r"\brefund\w*", r"\bcold\b", r"\bwrong\b",
        r"\bmissing\b", r"\bterrible\b", r"\bdisgusting\b", r"\bunhappy\b",
        r"\bwhere is my\b", r"\bnever arrived\b", r"\bstill waiting\b",
        r"\b(is|was|are|were|it'?s|so|very|really|too|running|came|arrived|delivered) late\b",
        r"\blate (delivery|order|again)\b", r"\bmoney back\b", r"\bnot happy\b",
        r"\brude\b", r"\bhorrible\b", r"\bburn(t|ed)\b", r"\braw\b",
        r"\bundercooked\b", r"\bovercooked\b", r"\bovercharg\w*",
        r"\b(charged|billed) twice\b", r"\bdouble.charged\b", r"\bworst\b",
        r"\bawful\b", r"\bpoor\b", r"\bdisappoint\w*", r"\brip(ped)? off\b",
        r"\bnever (got|received|came|arrived|turned up|showed)\b",
        r"\bwait(ing|ed)?\b.{0,25}\d+ ?(hours?|hrs?|mins?|minutes?)\b",
        r"\bfreezing\b", r"\bfrozen\b", r"\bturned up\b",
        r"\bdid(n'?t| not) (arrive|come|turn up|get)\b", r"\b(not|hasn'?t|haven'?t) arrived\b",
        r"\bwhere'?s my\b", r"\bwhere is (it|the driver)\b",
        r"\bbeen \d+ ?(hours?|hrs?|mins?|minutes?)\b", r"\btaking (forever|ages)\b",
        r"\bdirty\b", r"\bsoggy\b", r"\bstale\b", r"\bfood poison\w*",
        r"\bmade me (sick|ill)\b", r"\bhair in\b", r"\bforgot\w*", r"\bleft out\b", r"\bstill no\b",
        r"\bafter \d+ ?(hours?|hrs?|mins?|minutes?)\b",
    ],
    "human": [
        r"\b(speak|talk|chat) (to|with)\b", r"\bmanager\b", r"\bowner\b",
        r"\bhuman\b", r"\breal person\b", r"\bcatering\b",
        r"\bparty (booking|order|platter|tray)\b", r"\bwedding\b",
        r"\bbirthday\b", r"\bevent\b", r"\bcall me\b",
    ],
    "booking": [
        r"\bbook\w*", r"\breserv\w*", r"\btables?\b", r"\bparty of\b",
    ],
    "order": [
        r"\border(s|ing)?\b", r"\bi.d like\b", r"\bi wanna\b", r"\bi.?ll (have|get|take)\b",
        r"\bcan we (get|have)\b", r"\bcan i grab\b", r"\bget me\b", r"\bi need (a|an|some|two|three|\d)\b", r"\bi would like\b", r"\bi want\b",
        r"\bcan i (get|have)\b(?! (the|a|your) menu)",
        r"\bcould i (get|have)\b(?! (the|a|your) menu)",
        r"\bdeliver me\b",
    ],
    "faq": [
        r"\bopen\w*", r"\bclos\w+", r"\bhours?\b", r"\bwhat time\b",
        r"\bdeliver\w*", r"\bmenu\b", r"\bprice\w*", r"\bhow much\b",
        r"\bhalal\b", r"\bvegetarian\b", r"\bveggie\b", r"\bvegan\b", r"\bpay\w*",
        r"\bcard\b", r"\bcash\b", r"\bphone\b", r"\baddress\b",
        r"\bwhere are you\b", r"\bminimum\b", r"\bdeals?\b", r"\boffers?\b",
        r"\bspecials?\b", r"\bemail\b", r"\bcards?\b", r"\bnumber\b", r"\bstudent\b", r"\bwhere ?abouts\b", r"\b(visa|mastercard|amex|debit|credit)\b", r"\bpost ?code\b",
        r"\bdiscount\w*", r"\bvoucher\w*", r"\bcoupon\w*", r"\bapple pay\b", r"\bgoogle pay\b", r"\bhow long\b", r"\bcontactless\b",
    ],
}

# Menu words only suggest an order when nothing else matched. This stops
# "Do you do vegan pizzas?" (a question) being treated as an order.
WEAK_ORDER = [
    re.compile(p) for p in
    (r"\bpizzas?\b", r"\bmargherita\b", r"\bpasta\b", r"\bcollection\b",
     r"\bpepperonis?\b", r"\bpick.?up\b", r"\bcheesy\b", r"\bamalfi\b", r"\bsupreme\b",
     r"\bcoke\b", r"\bfanta\b", r"\bsprite\b", r"\bgarlic bread\b")
]

# Whole message is just a greeting / thanks / goodbye -> friendly reply.
_CHAT_WORD = (r"(?:hi|hello|hey|hiya|heya|yo|good (?:morning|afternoon|evening)|"
              r"thanks|thank you|thankyou|thx|ta|cheers|ok|okay|k|bye|goodbye|"
              r"see you|cya|great|perfect|lovely|nice one|no thanks|"
              r"there|mate|all|guys|so much|a lot|very much|again|pal|bro)")
CHITCHAT = re.compile(rf"{_CHAT_WORD}(?: {_CHAT_WORD})*")

# Categories that must always be handled by a person.
HUMAN_CATEGORIES = {"allergy", "complaint", "human", "unknown"}

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
    if CHITCHAT.fullmatch(re.sub(r"[^a-z0-9' ]", "", text).strip()):
        return Classification("chitchat", [], needs_human=False)
    # "minimum order" is a question about delivery, not an order.
    order_text = text.replace("minimum order", "")
    hits = {}
    for category in PRIORITY:
        subject = order_text if category == "order" else text
        found = [p.pattern for p in _COMPILED[category] if p.search(subject)]
        if found:
            hits[category] = found

    if not hits:
        weak = [p.pattern for p in WEAK_ORDER if p.search(text)]
        if weak:
            return Classification("order", weak, needs_human=False)
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
