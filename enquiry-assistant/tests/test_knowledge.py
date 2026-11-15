import json
import tempfile
import unittest
from pathlib import Path

from src.knowledge import (load_knowledge, missing_sections,
                           missing_days, find_todos)


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
        self.assertIn("opening_hours.monday", find_todos(self.kb))

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
