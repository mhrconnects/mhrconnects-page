import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from src.collector import Enquiry
from src.database import connect, save_enquiry, list_unnotified
from src.notifier import OutboxChannel, notify_new
from src.whatsapp import WhatsAppChannel, whatsapp_from_env, load_env

TOKEN = "SECRET-TOKEN-123"


class FakeMeta:
    """A local stand-in for Meta's server. Nothing real is ever contacted."""

    def __init__(self, status=200):
        self.status, self.requests = status, []
        outer = self

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.requests.append((self.path, dict(self.headers), body))
                self.send_response(outer.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"messages":[{"id":"wamid.X"}]}')

            def log_message(self, *a):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), H)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}/v21.0"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def stop(self):
        self.server.shutdown(); self.server.server_close()


class TestWhatsApp(unittest.TestCase):
    def setUp(self):
        self.meta = FakeMeta()

    def tearDown(self):
        self.meta.stop()

    def channel(self, **kw):
        return WhatsAppChannel(TOKEN, "123456789", "+44 7123 456789",
                               api_base=self.meta.base, **kw)

    def test_sends_text_message_correctly(self):
        self.channel().send("NEW ORDER", "Name: Jane\nPhone: 0712")
        path, headers, body = self.meta.requests[0]
        self.assertEqual(path, "/v21.0/123456789/messages")
        self.assertEqual(headers["Authorization"], f"Bearer {TOKEN}")
        self.assertEqual(body["to"], "447123456789")      # digits only
        self.assertEqual(body["type"], "text")
        self.assertIn("NEW ORDER\nName: Jane", body["text"]["body"])

    def test_template_mode_flattens_newlines(self):
        self.channel(template="new_enquiry").send("S", "line1\nline2\n\nline3")
        body = self.meta.requests[0][2]
        self.assertEqual(body["type"], "template")
        self.assertEqual(body["template"]["name"], "new_enquiry")
        text = body["template"]["components"][0]["parameters"][0]["text"]
        self.assertNotIn("\n", text)
        self.assertIn("line1 | line2", text)

    def test_api_error_raises_without_leaking_token(self):
        self.meta.status = 401
        with self.assertRaises(RuntimeError) as c:
            self.channel().send("s", "b")
        self.assertNotIn(TOKEN, str(c.exception))
        self.assertIn("401", str(c.exception))

    def test_unreachable_server_raises_cleanly(self):
        ch = WhatsAppChannel(TOKEN, "123456789", "447123456789",
                             api_base="http://127.0.0.1:1/v21.0", timeout=2)
        with self.assertRaises(RuntimeError) as c:
            ch.send("s", "b")
        self.assertNotIn(TOKEN, str(c.exception))

    def test_invalid_settings_rejected(self):
        for kw in [dict(token="", phone_number_id="1", to="447123456789"),
                   dict(token="t", phone_number_id="abc", to="447123456789"),
                   dict(token="t", phone_number_id="1", to="123"),
                   dict(token="t", phone_number_id="1", to="")]:
            with self.assertRaises(ValueError):
                WhatsAppChannel(**kw)

    def test_from_env(self):
        self.assertIsNone(whatsapp_from_env({}))
        self.assertIsNone(whatsapp_from_env({"WHATSAPP_TOKEN": "t"}))
        ch = whatsapp_from_env({"WHATSAPP_TOKEN": "t", "WHATSAPP_PHONE_NUMBER_ID": "1",
                                "WHATSAPP_TO": "447123456789",
                                "WHATSAPP_TEMPLATE": "tpl"})
        self.assertEqual(ch.template, "tpl")

    def test_load_env_parses_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".env"
            p.write_text('# c\nA=1\nB = "two"\n\nbad line\nC=\n')
            self.assertEqual(load_env(p), {"A": "1", "B": "two", "C": ""})
            self.assertEqual(load_env(Path(d) / "missing"), {})


class TestNotifierWithWhatsApp(unittest.TestCase):
    def test_whatsapp_failure_retries_without_duplicate_email(self):
        meta = FakeMeta(status=500)
        try:
            with tempfile.TemporaryDirectory() as d:
                db = connect(":memory:")
                # allergy => goes to BOTH whatsapp and email
                save_enquiry(db, Enquiry("callback", "allergy", "nuts?", name="A",
                                         phone="07123456789", needs_human=True))
                wa = WhatsAppChannel(TOKEN, "1", "447123456789", api_base=meta.base)
                ch = {"whatsapp": wa, "email": OutboxChannel("email", d)}
                self.assertEqual(notify_new(db, ch), {"sent": 0, "failed": 1})
                self.assertEqual(len(list(Path(d).glob("*-email.txt"))), 1)
                meta.status = 200                                  # WhatsApp recovers
                self.assertEqual(notify_new(db, ch), {"sent": 1, "failed": 0})
                self.assertEqual(len(list(Path(d).glob("*-email.txt"))), 1)  # no duplicate
                self.assertEqual(len(meta.requests), 2)
                self.assertEqual(list_unnotified(db), [])
        finally:
            meta.stop()


if __name__ == "__main__":
    unittest.main()
