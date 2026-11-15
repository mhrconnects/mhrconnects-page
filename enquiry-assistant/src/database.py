"""Database: stores finished enquiries in a single SQLite file.

SQLite needs no server and no account; the whole database is one file
(data/enquiries.db). That file contains customer names and phone numbers,
so it is excluded from Git by .gitignore. Never commit it.

All queries use '?' placeholders (never string-joining), which prevents
SQL injection from whatever a customer types.
"""
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "enquiries.db"
DEFAULT_RETENTION_DAYS = 90  # privacy: delete old enquiries after this long

SCHEMA = """
CREATE TABLE IF NOT EXISTS enquiries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL,
    kind        TEXT NOT NULL,
    category    TEXT NOT NULL,
    message     TEXT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    phone       TEXT NOT NULL DEFAULT '',
    items       TEXT NOT NULL DEFAULT '',
    fulfilment  TEXT NOT NULL DEFAULT '',
    address     TEXT NOT NULL DEFAULT '',
    postcode    TEXT NOT NULL DEFAULT '',
    needs_human INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'complete',
    notes       TEXT NOT NULL DEFAULT '[]',
    handled     INTEGER NOT NULL DEFAULT 0,
    handled_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_enquiries_created ON enquiries(created_at);
CREATE TABLE IF NOT EXISTS notifications (
    enquiry_id INTEGER NOT NULL,
    channel    TEXT NOT NULL,
    sent_at    TEXT NOT NULL,
    PRIMARY KEY (enquiry_id, channel)
);
"""


def connect(path=DEFAULT_DB):
    """Open (and if needed create) the database. Use ':memory:' for tests."""
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(enquiries)")]
    if "notified_at" not in cols:  # upgrade older databases
        conn.execute("ALTER TABLE enquiries ADD COLUMN notified_at TEXT")
        conn.commit()
    return conn


def _to_dict(row):
    if row is None:
        return None
    d = dict(row)
    d["notes"] = json.loads(d["notes"])
    d["needs_human"] = bool(d["needs_human"])
    d["handled"] = bool(d["handled"])
    return d


def save_enquiry(conn, enquiry):
    """Store an Enquiry (from collector.py). Returns the new row id."""
    cur = conn.execute(
        """INSERT INTO enquiries
           (created_at, kind, category, message, name, phone, items,
            fulfilment, address, postcode, needs_human, status, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (enquiry.created_at, enquiry.kind, enquiry.category, enquiry.message,
         enquiry.name, enquiry.phone, enquiry.items, enquiry.fulfilment,
         enquiry.address, enquiry.postcode, int(enquiry.needs_human),
         enquiry.status, json.dumps(enquiry.notes)))
    conn.commit()
    return cur.lastrowid


def get_enquiry(conn, enquiry_id):
    row = conn.execute("SELECT * FROM enquiries WHERE id = ?",
                       (enquiry_id,)).fetchone()
    return _to_dict(row)


def list_enquiries(conn, kind=None, needs_human=None, status=None,
                   handled=None, limit=100):
    """Newest first. Any filter left as None is ignored."""
    where, params = [], []
    if kind is not None:
        where.append("kind = ?"); params.append(kind)
    if needs_human is not None:
        where.append("needs_human = ?"); params.append(int(needs_human))
    if status is not None:
        where.append("status = ?"); params.append(status)
    if handled is not None:
        where.append("handled = ?"); params.append(int(handled))
    sql = "SELECT * FROM enquiries"
    if where:
        sql += " WHERE " + " AND ".join(where)   # only fixed text, no user input
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(max(1, min(int(limit), 1000)))
    return [_to_dict(r) for r in conn.execute(sql, params)]


def mark_handled(conn, enquiry_id):
    """Staff have dealt with this one. Returns True if a row was updated."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cur = conn.execute(
        "UPDATE enquiries SET handled = 1, handled_at = ? WHERE id = ?",
        (now, enquiry_id))
    conn.commit()
    return cur.rowcount == 1


def list_unnotified(conn):
    rows = conn.execute("SELECT * FROM enquiries WHERE notified_at IS NULL "
                        "ORDER BY id").fetchall()
    return [_to_dict(r) for r in rows]


def channel_sent(conn, enquiry_id, channel):
    row = conn.execute("SELECT 1 FROM notifications WHERE enquiry_id = ? "
                       "AND channel = ?", (enquiry_id, channel)).fetchone()
    return row is not None


def record_notification(conn, enquiry_id, channel):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute("INSERT OR IGNORE INTO notifications VALUES (?,?,?)",
                 (enquiry_id, channel, now))
    conn.commit()


def mark_notified(conn, enquiry_id):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute("UPDATE enquiries SET notified_at = ? WHERE id = ?",
                 (now, enquiry_id))
    conn.commit()


def delete_older_than(conn, days=DEFAULT_RETENTION_DAYS, now=None):
    """Privacy clean-up: delete enquiries older than `days`. Returns count."""
    now = now or datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).isoformat(timespec="seconds")
    cur = conn.execute("DELETE FROM enquiries WHERE created_at < ?", (cutoff,))
    conn.commit()
    return cur.rowcount


if __name__ == "__main__":
    conn = connect()
    rows = list_enquiries(conn)
    print(f"{len(rows)} stored enquiries ({DEFAULT_DB})")
    for r in rows:
        flag = "HUMAN" if r["needs_human"] else "     "
        print(f"#{r['id']:<3} {r['created_at']} {flag} {r['kind']:8} "
              f"{r['category']:9} {r['status']:10} {r['name'] or '-':12} "
              f"{r['phone'] or '-'}")
