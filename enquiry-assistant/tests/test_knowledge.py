import json
import tempfile
import unittest
from pathlib import Path

from src.knowledge import (load_knowledge, missing_sections,
                           missing_days, find_todos, items_to_verify)


class TestKnowledge(unittest.TestCase):
    def setUp(self):
        self.kb = load_knowledge()

    def test_file_loads_with_business_name(self):
        self.assertEqual(self.kb["business"]["name"], "Fire Away Ashton")

    def test_all_required_sections_present(self):
        self.assertEqual(missing_sections(self.kb), [])

    def test_all_seven_days_present(self):
        self.assertEqual(missing_days(self.kb), [])

    def test_allergens_always_escalate(self):
        # Safety rule: allergy questions always go to a human.
        self.assertTrue(self.kb["allergens"]["always_escalate"])

    def test_find_todos_detects_placeholders(self):
        self.assertIn("allergens.policy", find_todos(self.kb))
        self.assertEqual(find_todos({"a": {"b": "TODO: x"}}), ["a.b"])

    def test_gluten_free_stays_unconfirmed(self):
        # Safety rule: never state gluten-free until the owner confirms.
        self.assertIn("dietary.gluten_free", find_todos(self.kb))

    def test_real_details_present(self):
        self.assertEqual(self.kb["business"]["phone"], "0161 526 4777")
        self.assertIn("95 Penny Meadow", self.kb["business"]["address"])
        self.assertEqual(self.kb["opening_hours"]["friday"], "4:00 PM - 2:00 AM")
        self.assertEqual(self.kb["opening_hours"]["sunday"], "4:00 PM - 1:00 AM")
        self.assertEqual(self.kb["bookings"]["takes_table_bookings"], "No")

    def test_no_todo_in_opening_hours_or_phone(self):
        todos = find_todos(self.kb)
        self.assertFalse([t for t in todos if t.startswith("opening_hours")])
        self.assertNotIn("business.phone", todos)

    def test_verification_list_exists(self):
        self.assertTrue(items_to_verify(self.kb))

    def test_find_todos_empty_when_confirmed(self):
        self.assertEqual(find_todos({"a": {"b": "08:00"}, "c": ["x"]}), [])

    def test_missing_section_is_detected(self):
        self.assertIn("faqs", missing_sections({"business": {}}))

    def test_invalid_json_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.json"
            p.write_text("{not json")
            with self.assertRaises(json.JSONDecodeError):
                load_knowledge(p)


if __name__ == "__main__":
    unittest.main()
