import unittest

from src.classifier import classify


class TestClassifier(unittest.TestCase):
    def check(self, message, category, human=None):
        r = classify(message)
        self.assertEqual(r.category, category, f"{message!r} -> {r}")
        if human is not None:
            self.assertEqual(r.needs_human, human)

    # --- each category ---
    def test_faq(self):
        self.check("What time do you close tonight?", "faq", human=False)
        self.check("Do you deliver to Hyde?", "faq", human=False)
        self.check("Is your food halal?", "faq", human=False)
        self.check("Do you take card?", "faq", human=False)

    def test_order(self):
        self.check("I'd like a large margherita please", "order", human=False)
        self.check("Can I get two pizzas for collection", "order")

    def test_booking(self):
        self.check("Can I book a table for 4 on Friday?", "booking", human=False)
        self.check("Reservation for a party of six", "booking")

    def test_complaint_goes_to_human(self):
        self.check("My pizza arrived cold", "complaint", human=True)
        self.check("I want a refund", "complaint", human=True)

    def test_allergy_goes_to_human(self):
        self.check("Is the base gluten free?", "allergy", human=True)
        self.check("My son has a nut allergy", "allergy", human=True)

    def test_unknown_goes_to_human(self):
        self.check("Do you sponsor football teams?", "unknown", human=True)
        self.check("", "unknown", human=True)
        self.check(None, "unknown", human=True)

    # --- bugs found by trying messy messages ---
    def test_table_without_for_is_booking(self):
        self.check("can I have a table tonight", "booking", human=False)

    def test_rude_is_complaint(self):
        self.check("my driver was rude", "complaint", human=True)

    # --- safety priority ---
    def test_allergy_beats_order(self):
        self.check("I want to order but I'm allergic to nuts", "allergy", human=True)

    def test_complaint_beats_order(self):
        self.check("I ordered a pizza and it was cold", "complaint", human=True)

    # --- robustness ---
    def test_case_and_curly_apostrophe(self):
        self.check("I’D LIKE A PIZZA", "order")

    def test_no_false_match_inside_words(self):
        # 'book' must not match 'facebook'
        self.check("Are you on facebook?", "unknown")

    def test_matched_rules_reported(self):
        self.assertTrue(classify("what time do you open").matched)


if __name__ == "__main__":
    unittest.main()
