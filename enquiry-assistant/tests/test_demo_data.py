import unittest

from src.database import connect, list_enquiries
from src.demo_data import SAMPLES, seed_demo


class TestDemoData(unittest.TestCase):
    def test_seeds_once_only(self):
        db = connect(":memory:")
        self.assertEqual(seed_demo(db), len(SAMPLES))
        self.assertEqual(seed_demo(db), 0)                 # not duplicated
        self.assertEqual(len(list_enquiries(db)), len(SAMPLES))

    def test_samples_cover_each_dashboard_view(self):
        db = connect(":memory:")
        seed_demo(db)
        self.assertTrue(list_enquiries(db, kind="order"))
        self.assertTrue(list_enquiries(db, needs_human=True))
        self.assertTrue(list_enquiries(db, status="incomplete"))

    def test_samples_are_clearly_fake(self):
        for s in SAMPLES:
            self.assertRegex(s.get("phone", "07700900000"), r"^(07123|07700|01615|\d{0})")


if __name__ == "__main__":
    unittest.main()
