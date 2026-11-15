"""The browser demo (web_demo/engine.js) must behave exactly like the Python
assistant. Runs the same inputs through both and compares every reply."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from build_web_demo import build_data
from src.classifier import classify
from src.collector import (Conversation, normalise_phone, parse_name,
                           parse_postcode)
from src.responder import respond
from tests.corpus import CORPUS

ROOT = Path(__file__).resolve().parent.parent

CHATS = [
    ["I'd like a large margherita", "delivery", "12 High Street Ashton OL6 1AA",
     "my name is jane smith", "12345", "07123 456 789"],
    ["I want to order", "two cheesy pizzas and a coke", "collection", "Sam", "abc", "def"],
    ["my pizza arrived cold", "bob", "0161 526 4777"],
    ["is the base gluten free?", "ann", "07123456789"],
    ["I want to order", "a pizza, I have a nut allergy", "collection", "Sam", "+44 7123 456789"],
    ["I want to order", "cancel"],
    ["can I speak to the manager", "Zoe", "01615550123"],
    ["what's your email", "Tom", "07123456789"],
    ["hi", "thanks", "bye"],
    ["I'd like a pizza", "delivery", "12 High Street", "12 High Street OL6 1AA", "O'Brien", "07123456789"],
]
PHONES = ["0161 526 4777", "07123-456-789", "+44 7123 456789", "+44 (0)7123 456789",
          "0044 7123 456789", "12345", "abc", "", "07123 45678", "07123456789012", "0800"]
NAMES = ["my name is jane smith", "It's Bob", "O'Brien", "McDonald", "Anne-Marie",
         "", "a", "12345", "bob; DROP TABLE x", "<script>", "x" * 80, "jane  smith"]
POSTCODES = ["95 Penny Meadow ol6 6ep", "flat 2, OL66EP", "12 High Street", "SK14 2AB"]
EXTRA = ["", "?", "do you deliver to Hyde?", "what time do you close", "are you open on friday",
         "any deals", "can I have the menu", "is it halal", "I want a refund", "table for 4",
         "cheers mate", "<b>hi</b>", "WHAT'S YOUR ADDRESS", "can i pay by card"]


@unittest.skipUnless(shutil.which("node"), "node not installed")
class TestParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.messages = [m for m, _ in CORPUS] + EXTRA
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "data.json").write_text(json.dumps(build_data()))
            (Path(d) / "cases.json").write_text(json.dumps({
                "messages": cls.messages, "chats": CHATS, "phones": PHONES,
                "names": NAMES, "postcodes": POSTCODES}))
            out = subprocess.run(["node", str(ROOT / "tests" / "parity.js"),
                                  str(Path(d) / "data.json"), str(Path(d) / "cases.json")],
                                 capture_output=True, text=True, check=True).stdout
        cls.js = json.loads(out)

    def test_js_returned_a_result_for_every_input(self):
        self.assertEqual(len(self.js["messages"]), len(self.messages))
        self.assertEqual([len(c) for c in self.js["chats"]], [len(c) for c in CHATS])
        self.assertGreater(len(self.messages), 150)

    def test_every_message_matches(self):
        for m, got in zip(self.messages, self.js["messages"]):
            c, r = classify(m), respond(m)
            want = [c.category, c.needs_human, r.reply, r.needs_human, r.topic]
            self.assertEqual(got, want, m)

    def test_scripted_conversations_match(self):
        for chat, got in zip(CHATS, self.js["chats"]):
            conv = Conversation()
            for msg, g in zip(chat, got):
                t = conv.handle(msg)
                e = t.enquiry
                want = [t.reply, t.done, e and [e.kind, e.category, e.name, e.phone,
                        e.items, e.fulfilment, e.address, e.postcode,
                        e.needs_human, e.status, e.notes]]
                self.assertEqual(g, want, (chat, msg))

    def test_validators_match(self):
        self.assertEqual(self.js["phones"], [normalise_phone(p) for p in PHONES])
        self.assertEqual(self.js["names"], [parse_name(n) for n in NAMES])
        self.assertEqual(self.js["postcodes"], [parse_postcode(p) for p in POSTCODES])


if __name__ == "__main__":
    unittest.main()
