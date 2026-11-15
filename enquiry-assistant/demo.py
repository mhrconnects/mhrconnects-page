"""Scripted demo: plays realistic customer chats through the whole system.

Run from the enquiry-assistant folder:   python3 demo.py
All names and phone numbers below are FAKE.
"""
from src.collector import Conversation

CHATS = {
    "1. Quick question (answered instantly, nothing collected)": [
        "hi are u open on sunday?",
    ],
    "2. Halal + deals (answered from approved info only)": [
        "is your food halal",
        "any deals on?",
    ],
    "3. Delivery order (details collected step by step)": [
        "hi can I get a large margherita please",
        "delivery",
        "12 High Street, Ashton-under-Lyne OL6 1AA",
        "my name is Jane Smith",
        "07123 456 789",
    ],
    "4. Allergy question (never guessed, goes to a human)": [
        "is the base gluten free? my son is coeliac",
        "Mark",
        "0161 555 0123",
    ],
    "5. Complaint (apology + callback request)": [
        "my pizza arrived cold",
        "Sam",
        "07700 900123",
    ],
    "6. Table booking (politely explained)": [
        "can I book a table for 6 on friday",
    ],
}

for title, messages in CHATS.items():
    print("=" * 72)
    print(title)
    print("=" * 72)
    conv = Conversation()
    last = None
    for msg in messages:
        last = conv.handle(msg)
        print(f"\n  Customer : {msg}")
        print("  Assistant: " + last.reply.replace("\n", "\n             "))
    if last.done:
        e = last.enquiry
        flag = "YES - needs a person" if e.needs_human else "no"
        print(f"\n  >> ENQUIRY RECORD: {e.kind} | {e.status} | human needed: {flag}")
        print(f"     {e.name} | {e.phone} | {e.fulfilment or '-'} | notes: {e.notes or '-'}")
    print()
