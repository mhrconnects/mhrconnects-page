import tempfile
import unittest
from pathlib import Path

from src.collector import Enquiry
from src.database import connect, save_enquiry, list_unnotified, get_enquiry
from src.notifier import (route, format_message, notify_new, OutboxChannel,
                          default_channels)


def row(**kw):
    base = dict(kind="order", category="order", message="a pizza", name="Jane",
                phone="07123456789", items="a pizza", fulfilment="collection")
    base.update(kw)
    db = connect(":memory:")
    return get_enquiry(db, save_enquiry(db, Enquiry(**base)))


class Boom:
    def send(self, subject, body):
        raise RuntimeError("down")


class TestNotifier(unittest.TestCase):
    def test_routing(self):
        self.assertEqual(route(row()), ["whatsapp"])
        self.assertEqual(route(row(kind="callback", category="complaint",
                                   needs_human=True)), ["email"])
        self.assertEqual(route(row(kind="callback", category="allergy",
                                   needs_human=True)), ["whatsapp", "email"])
        self.assertEqual(route(row(needs_human=True)), ["whatsapp", "email"])
        self.assertEqual(route(row(status="incomplete", kind="callback",
                                   category="unknown", needs_human=True)), ["email"])

    def test_format_message(self):
        s, b = format_message(row(needs_human=True, notes=["check nuts"],
                                  address="1 High St OL6 1AA", fulfilment="delivery"))
        self.assertIn("NEW ORDER", s)
        self.assertIn("NEEDS A PERSON", s)
        for text in ["Jane", "07123456789", "a pizza", "Delivery",
                     "1 High St OL6 1AA", "Note: check nuts"]:
            self.assertIn(text, b)

    def test_notify_writes_files_and_marks_sent_once(self):
        with tempfile.TemporaryDirectory() as d:
            db = connect(":memory:")
            save_enquiry(db, Enquiry("order", "order", "x", name="A", items="x"))
            save_enquiry(db, Enquiry("callback", "complaint", "cold", name="B",
                                     needs_human=True))
            ch = default_channels(d)
            self.assertEqual(notify_new(db, ch), {"sent": 2, "failed": 0})
            files = sorted(p.name for p in Path(d).glob("*.txt"))
            self.assertEqual(len(files), 2)
            self.assertTrue(any("whatsapp" in f for f in files))
            self.assertTrue(any("email" in f for f in files))
            self.assertEqual(list_unnotified(db), [])
            self.assertEqual(notify_new(db, ch), {"sent": 0, "failed": 0})  # no duplicates
            self.assertEqual(len(list(Path(d).glob("*.txt"))), 2)

    def test_failure_is_retried_not_lost(self):
        with tempfile.TemporaryDirectory() as d:
            db = connect(":memory:")
            save_enquiry(db, Enquiry("order", "order", "x", name="A", items="x"))
            bad = {"whatsapp": Boom(), "email": Boom()}
            self.assertEqual(notify_new(db, bad), {"sent": 0, "failed": 1})
            self.assertEqual(len(list_unnotified(db)), 1)
            self.assertEqual(notify_new(db, default_channels(d)),
                             {"sent": 1, "failed": 0})

    def test_old_database_is_upgraded(self):
        import sqlite3
        from src.database import SCHEMA
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "old.db"
            c = sqlite3.connect(p)
            c.executescript(SCHEMA)  # schema without notified_at
            c.execute("INSERT INTO enquiries (created_at,kind,category,message) "
                      "VALUES ('2026-01-01T00:00:00+00:00','order','order','hi')")
            c.commit(); c.close()
            db = connect(p)
            self.assertEqual(len(list_unnotified(db)), 1)  # old row kept, now unnotified
            db.close()


if __name__ == "__main__":
    unittest.main()
