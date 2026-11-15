import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.collector import Enquiry
from src.database import (connect, save_enquiry, get_enquiry, list_enquiries,
                          mark_handled, delete_older_than)


def make(**kw):
    base = dict(kind="order", category="order", message="a pizza",
                name="Jane", phone="07123456789", items="a pizza",
                fulfilment="collection")
    base.update(kw)
    return Enquiry(**base)


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = connect(":memory:")

    def test_save_and_get_round_trip(self):
        e = make(needs_human=True, notes=["note one", "note two"])
        i = save_enquiry(self.db, e)
        got = get_enquiry(self.db, i)
        self.assertEqual(got["name"], "Jane")
        self.assertEqual(got["phone"], "07123456789")
        self.assertEqual(got["notes"], ["note one", "note two"])
        self.assertIs(got["needs_human"], True)
        self.assertIs(got["handled"], False)

    def test_get_missing_returns_none(self):
        self.assertIsNone(get_enquiry(self.db, 999))

    def test_filters(self):
        save_enquiry(self.db, make())
        save_enquiry(self.db, make(kind="callback", category="complaint",
                                   needs_human=True))
        save_enquiry(self.db, make(status="incomplete", needs_human=True))
        self.assertEqual(len(list_enquiries(self.db)), 3)
        self.assertEqual(len(list_enquiries(self.db, kind="order")), 2)
        self.assertEqual(len(list_enquiries(self.db, needs_human=True)), 2)
        self.assertEqual(len(list_enquiries(self.db, status="incomplete")), 1)
        self.assertEqual(len(list_enquiries(
            self.db, kind="order", needs_human=True)), 1)

    def test_newest_first_and_limit(self):
        for n in ["a", "b", "c"]:
            save_enquiry(self.db, make(name=n, created_at=f"2026-01-0{ord(n)-96}T00:00:00+00:00"))
        rows = list_enquiries(self.db, limit=2)
        self.assertEqual([r["name"] for r in rows], ["c", "b"])

    def test_mark_handled(self):
        i = save_enquiry(self.db, make())
        self.assertTrue(mark_handled(self.db, i))
        self.assertTrue(get_enquiry(self.db, i)["handled"])
        self.assertEqual(len(list_enquiries(self.db, handled=False)), 0)
        self.assertFalse(mark_handled(self.db, 999))

    def test_retention_deletes_only_old(self):
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        old = (now - timedelta(days=91)).isoformat(timespec="seconds")
        recent = (now - timedelta(days=10)).isoformat(timespec="seconds")
        save_enquiry(self.db, make(name="Old", created_at=old))
        save_enquiry(self.db, make(name="Recent", created_at=recent))
        self.assertEqual(delete_older_than(self.db, 90, now=now), 1)
        names = [r["name"] for r in list_enquiries(self.db)]
        self.assertEqual(names, ["Recent"])

    def test_sql_injection_is_stored_as_plain_text(self):
        nasty = "Robert'); DROP TABLE enquiries;--"
        i = save_enquiry(self.db, make(message=nasty, items=nasty))
        self.assertEqual(get_enquiry(self.db, i)["message"], nasty)
        self.assertEqual(len(list_enquiries(self.db)), 1)  # table still there

    def test_unicode_and_empty_fields(self):
        i = save_enquiry(self.db, make(message="Café £13.99 🍕", name="Zoë"))
        got = get_enquiry(self.db, i)
        self.assertEqual((got["message"], got["name"]), ("Café £13.99 🍕", "Zoë"))
        j = save_enquiry(self.db, make(items="", address=""))
        self.assertEqual(get_enquiry(self.db, j)["address"], "")

    def test_data_persists_in_a_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sub" / "test.db"   # folder created automatically
            c1 = connect(path)
            save_enquiry(c1, make(name="Persist"))
            c1.close()
            c2 = connect(path)                    # reopen
            self.assertEqual(list_enquiries(c2)[0]["name"], "Persist")
            c2.close()


if __name__ == "__main__":
    unittest.main()
