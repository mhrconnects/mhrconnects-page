import unittest

from src.collector import (Conversation, normalise_phone, parse_name,
                           parse_postcode)


def run(*messages):
    """Send messages to a fresh conversation; return all turns."""
    c = Conversation()
    return c, [c.handle(m) for m in messages]


class TestValidators(unittest.TestCase):
    def test_phone_valid_formats(self):
        self.assertEqual(normalise_phone("0161 526 4777"), "01615264777")
        self.assertEqual(normalise_phone("07123-456-789"), "07123456789")
        self.assertEqual(normalise_phone("+44 7123 456789"), "07123456789")
        self.assertEqual(normalise_phone("+44 (0)7123 456789"), "07123456789")
        self.assertEqual(normalise_phone("0044 7123 456789"), "07123456789")

    def test_phone_invalid(self):
        for bad in ["12345", "abc", "", None, "0800", "07123 45678",
                    "07123456789012", "call me"]:
            self.assertIsNone(normalise_phone(bad), bad)

    def test_name(self):
        self.assertEqual(parse_name("my name is jane smith"), "Jane Smith")
        self.assertEqual(parse_name("It's Bob"), "Bob")
        self.assertEqual(parse_name("O'Brien"), "O'Brien")
        self.assertEqual(parse_name("McDonald"), "McDonald")
        self.assertEqual(parse_name("Anne-Marie"), "Anne-Marie")

    def test_name_rejects_junk(self):
        for bad in ["", "a", "12345", "bob; DROP TABLE x", "<script>", "x" * 80]:
            self.assertIsNone(parse_name(bad), bad)

    def test_postcode(self):
        self.assertEqual(parse_postcode("95 Penny Meadow ol6 6ep"), "OL6 6EP")
        self.assertEqual(parse_postcode("flat 2, OL66EP"), "OL6 6EP")
        self.assertIsNone(parse_postcode("12 High Street"))


class TestFlows(unittest.TestCase):
    def test_faq_collects_nothing(self):
        _, (t,) = run("what time do you close")
        self.assertFalse(t.done)
        self.assertIsNone(t.enquiry)
        self.assertIn("4:00 PM", t.reply)

    def test_booking_collects_nothing(self):
        _, (t,) = run("can I book a table for 4")
        self.assertIsNone(t.enquiry)
        self.assertIn("not taken", t.reply)

    def test_full_delivery_order(self):
        _, turns = run("I'd like a large margherita", "delivery",
                       "12 High Street Ashton OL6 1AA", "my name is jane smith",
                       "07123 456 789")
        e = turns[-1].enquiry
        self.assertTrue(turns[-1].done)
        self.assertEqual((e.kind, e.status, e.fulfilment), ("order", "complete", "delivery"))
        self.assertEqual((e.name, e.phone, e.postcode),
                         ("Jane Smith", "07123456789", "OL6 1AA"))
        self.assertIn("large margherita", e.items)
        self.assertIn("NOT confirmed", turns[-1].reply)
        self.assertFalse(e.needs_human)

    def test_collection_order_skips_address(self):
        _, turns = run("I want to order", "two cheesy pizzas", "collection",
                       "Sam", "07123456789")
        e = turns[-1].enquiry
        self.assertEqual(e.fulfilment, "collection")
        self.assertEqual(e.address, "")
        self.assertEqual(e.items, "two cheesy pizzas")

    def test_menu_words_skip_item_question(self):
        _, (t,) = run("I'd like a large margherita")
        self.assertIn("collection or delivery", t.reply)

    def test_no_menu_words_asks_for_items(self):
        _, (t,) = run("I want to order")
        self.assertIn("What would you like to order", t.reply)

    def test_complaint_becomes_callback(self):
        _, turns = run("my pizza arrived cold", "bob", "0161 526 4777")
        e = turns[-1].enquiry
        self.assertEqual((e.kind, e.category), ("callback", "complaint"))
        self.assertTrue(e.needs_human)
        self.assertEqual(e.phone, "01615264777")

    def test_allergy_becomes_callback_and_no_guess(self):
        _, turns = run("is the base gluten free?", "ann", "07123456789")
        e = turns[-1].enquiry
        self.assertEqual(e.category, "allergy")
        self.assertTrue(e.needs_human)
        self.assertNotIn("gluten-free base", turns[0].reply.lower())

    def test_unanswerable_faq_becomes_callback(self):
        _, turns = run("what's your email", "Tom", "07123456789")
        self.assertEqual(turns[-1].enquiry.kind, "callback")


class TestSafetyAndEdgeCases(unittest.TestCase):
    def test_allergy_mentioned_in_items_flags_human(self):
        _, turns = run("I want to order", "a pizza, I have a nut allergy",
                       "collection", "Sam", "07123456789")
        e = turns[-1].enquiry
        self.assertTrue(e.needs_human)
        self.assertTrue(any("allergy" in n.lower() for n in e.notes))

    def test_retry_then_success(self):
        _, turns = run("I want to order", "two pizzas", "collection", "Sam",
                       "12345", "07123456789")
        self.assertIn("doesn't look like", turns[4].reply)
        self.assertEqual(turns[-1].enquiry.status, "complete")

    def test_two_bad_phones_gives_incomplete(self):
        _, turns = run("I want to order", "two pizzas", "collection", "Sam",
                       "abc", "def")
        e = turns[-1].enquiry
        self.assertTrue(turns[-1].done)
        self.assertEqual(e.status, "incomplete")
        self.assertTrue(e.needs_human)
        self.assertEqual(e.phone, "")

    def test_cancel_stops_and_stores_nothing(self):
        _, turns = run("I want to order", "cancel")
        self.assertIsNone(turns[-1].enquiry)
        self.assertIn("cancelled", turns[-1].reply)

    def test_delivery_without_postcode_is_rejected(self):
        _, turns = run("I'd like a pizza", "delivery", "12 High Street")
        self.assertIn("postcode", turns[2].reply.lower())

    def test_conversation_resets_after_finishing(self):
        c, _ = run("I want to order", "two pizzas", "collection", "Sam",
                   "07123456789")
        t = c.handle("what time do you close")
        self.assertIn("4:00 PM", t.reply)
        self.assertIsNone(t.enquiry)

    def test_long_and_empty_input_are_safe(self):
        c = Conversation()
        self.assertTrue(c.handle("x" * 100000).reply)
        self.assertTrue(c.handle("").reply)
        self.assertTrue(c.handle(None).reply)

    def test_no_reply_leaks_todo(self):
        c = Conversation()
        for m in ["email", "gluten", "refund", "order", "hours", "kids meal"]:
            self.assertNotIn("TODO", c.handle(m).reply, m)
            c._reset()


if __name__ == "__main__":
    unittest.main()
