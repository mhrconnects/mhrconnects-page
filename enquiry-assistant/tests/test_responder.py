import copy
import unittest

from src.knowledge import load_knowledge
from src.responder import respond


class TestResponder(unittest.TestCase):
    def setUp(self):
        self.kb = load_knowledge()

    def r(self, msg, kb=None):
        return respond(msg, kb or self.kb)

    # ---- answers come from the approved file ----
    def test_specific_day_hours(self):
        r = self.r("are you open on friday?")
        self.assertIn("4:00 PM - 2:00 AM", r.reply)
        self.assertFalse(r.needs_human)

    def test_general_hours_groups_days(self):
        r = self.r("what time do you close")
        self.assertIn("Fri, Sat: 4:00 PM - 2:00 AM", r.reply)
        self.assertIn("4:00 PM - 1:00 AM", r.reply)

    def test_halal_vegan_vegetarian(self):
        self.assertIn("halal", self.r("is it halal?").reply.lower())
        self.assertIn("vegan", self.r("do you do vegan pizzas").reply.lower())
        self.assertEqual(self.r("any veggie options").topic, "vegetarian")

    def test_payment_and_contact(self):
        self.assertIn("Apple Pay", self.r("can I pay by card").reply)
        self.assertIn("95 Penny Meadow", self.r("what's your address").reply)

    def test_deals_and_menu(self):
        self.assertIn("£7.99", self.r("any deals?").reply)
        self.assertIn("£13.99", self.r("how much is a pizza").reply)
        self.assertIn("£13.99", self.r("can I have the menu").reply)

    def test_collection_time(self):
        r = self.r("how long for collection")
        self.assertEqual(r.topic, "collection")
        self.assertIn("10 to 20 minutes", r.reply)

    # ---- never over-promise ----
    def test_delivery_never_says_yes_to_a_named_area(self):
        r = self.r("do you deliver to Hyde?")
        self.assertNotIn("Yes", r.reply)
        self.assertIn("postcode", r.reply)
        self.assertFalse(r.needs_human)

    # ---- bookings and orders ----
    def test_booking_explains_no_bookings(self):
        r = self.r("can I book a table for 6")
        self.assertEqual(r.category, "booking")
        self.assertIn("not taken", r.reply)

    def test_order_gives_ways_to_order(self):
        r = self.r("I'd like a large margherita")
        self.assertEqual(r.category, "order")
        self.assertIn("0161 526 4777", r.reply)

    # ---- safety ----
    def test_allergy_always_human_and_no_gluten_claim(self):
        r = self.r("is the base gluten free?")
        self.assertTrue(r.needs_human)
        self.assertNotIn("gluten-free base", r.reply.lower())
        self.assertIn("0161 526 4777", r.reply)

    def test_allergy_beats_order(self):
        self.assertTrue(self.r("order a pizza, I have a nut allergy").needs_human)

    def test_complaint_apologises_and_escalates(self):
        r = self.r("my pizza arrived cold")
        self.assertTrue(r.needs_human)
        self.assertIn("sorry", r.reply.lower())

    def test_unknown_escalates(self):
        r = self.r("do you do kids meals")
        self.assertTrue(r.needs_human)
        self.assertIn("team member", r.reply)

    # ---- TODO facts are never shown ----
    def test_todo_email_is_never_leaked(self):
        r = self.r("what's your email")
        self.assertNotIn("TODO", r.reply)
        self.assertTrue(r.needs_human)

    def test_todo_in_hours_triggers_handoff(self):
        kb = copy.deepcopy(self.kb)
        kb["opening_hours"]["monday"] = "TODO: confirm"
        r = self.r("what time do you open", kb)
        self.assertTrue(r.needs_human)
        self.assertNotIn("TODO", r.reply)

    def test_no_reply_ever_contains_todo(self):
        msgs = ["hours", "delivery", "email", "deals", "menu", "halal",
                "gluten", "refund", "address", "pay", "kids meal", "?", ""]
        for m in msgs:
            self.assertNotIn("TODO", self.r(m).reply, m)

    def test_empty_and_none_messages(self):
        self.assertTrue(self.r("").needs_human)
        self.assertTrue(self.r(None).needs_human)


if __name__ == "__main__":
    unittest.main()
