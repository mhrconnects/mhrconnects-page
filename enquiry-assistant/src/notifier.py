"""Notifier: tells the business about new enquiries.

Routing rules (edit route() to change them):
  order                      -> WhatsApp
  allergy, or order flagged  -> WhatsApp AND email (urgent)
  everything else            -> email

Channels are pluggable. OutboxChannel writes each message to a text file in
data/outbox/ so you can see exactly what the owner would receive, at zero
cost. A real WhatsApp/email sender only needs a send(subject, body) method.
"""
from datetime import datetime, timezone
from pathlib import Path

from src.database import (channel_sent, list_unnotified, mark_notified,
                          record_notification)

DEFAULT_OUTBOX = Path(__file__).resolve().parent.parent / "data" / "outbox"


def route(e):
    """Which channels should hear about this enquiry? e is a database row."""
    urgent = e["category"] == "allergy" or (e["kind"] == "order" and e["needs_human"])
    if urgent:
        return ["whatsapp", "email"]
    return ["whatsapp"] if e["kind"] == "order" else ["email"]


def format_message(e):
    """Return (subject, body) for an enquiry row."""
    tag = "NEW ORDER" if e["kind"] == "order" else f"CALLBACK ({e['category']})"
    if e["needs_human"]:
        tag += " - NEEDS A PERSON"
    if e["status"] == "incomplete":
        tag += " [INCOMPLETE]"
    lines = [f"Enquiry #{e['id']} at {e['created_at']}",
             f"Name: {e['name'] or '(not given)'}",
             f"Phone: {e['phone'] or '(not given)'}"]
    if e["items"]:
        lines.append(f"Order: {e['items']}")
    if e["fulfilment"]:
        lines.append(f"{e['fulfilment'].capitalize()}")
    if e["address"]:
        lines.append(f"Address: {e['address']}")
    lines.append(f"Customer said: {e['message']}")
    lines += [f"Note: {n}" for n in e["notes"]]
    return f"{tag} - Fire Away Ashton", "\n".join(lines)


class OutboxChannel:
    """Demo channel: writes the message to data/outbox/ as a text file."""

    def __init__(self, name, folder=DEFAULT_OUTBOX):
        self.name, self.folder = name, Path(folder)

    def send(self, subject, body):
        self.folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        path = self.folder / f"{stamp}-{self.name}.txt"
        path.write_text(f"TO: {self.name}\nSUBJECT: {subject}\n\n{body}\n",
                        encoding="utf-8")
        return path


def default_channels(folder=DEFAULT_OUTBOX):
    """Real WhatsApp if configured in .env, otherwise the demo outbox."""
    from src.whatsapp import whatsapp_from_env
    return {"whatsapp": whatsapp_from_env() or OutboxChannel("whatsapp", folder),
            "email": OutboxChannel("email", folder)}


def notify_new(conn, channels=None):
    """Send every not-yet-notified enquiry. Returns {'sent': n, 'failed': n}.

    Delivery is recorded per channel, so if WhatsApp fails but email works,
    only WhatsApp is retried next time (no duplicate emails). An enquiry is
    marked notified once ALL its channels have succeeded.
    """
    channels = channels or default_channels()
    sent = failed = 0
    for e in list_unnotified(conn):
        subject, body = format_message(e)
        ok = True
        for name in route(e):
            if channel_sent(conn, e["id"], name):
                continue
            try:
                channels[name].send(subject, body)
                record_notification(conn, e["id"], name)
            except Exception:
                ok = False
        if ok:
            mark_notified(conn, e["id"])
            sent += 1
        else:
            failed += 1
    return {"sent": sent, "failed": failed}
