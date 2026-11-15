import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from src.database import connect, list_enquiries
from src.webapp import ChatApp, make_server


def post(base, payload, raw=None):
    data = raw if raw is not None else json.dumps(payload).encode()
    req = urllib.request.Request(base + "/api/chat", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


class TestWeb(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "t.db"
        self.out = Path(self.tmp.name) / "outbox"
        self.server = make_server(port=0, app=ChatApp(self.db, self.out))
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.tmp.cleanup()

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as r:
            return r.status, r.headers, r.read()

    def test_pages_and_security_headers(self):
        for path in ["/", "/static/app.js", "/static/style.css", "/health"]:
            status, headers, _ = self.get(path)
            self.assertEqual(status, 200, path)
            self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
            self.assertIn("default-src 'self'", headers["Content-Security-Policy"])

    def test_unknown_path_404_and_no_path_traversal(self):
        for path in ["/nope", "/static/../src/webapp.py", "/..%2fdata/business.json"]:
            with self.assertRaises(urllib.error.HTTPError) as c:
                self.get(path)
            self.assertEqual(c.exception.code, 404, path)

    def test_faq_answer(self):
        status, d = post(self.base, {"session": "", "message": "are you open on friday?"})
        self.assertEqual(status, 200)
        self.assertIn("2:00 AM", d["reply"])
        self.assertTrue(d["session"])
        self.assertFalse(d["done"])

    def test_full_order_saved_and_notified(self):
        sid = ""
        for m in ["can I get a large margherita", "collection", "Jane",
                  "07123 456 789"]:
            status, d = post(self.base, {"session": sid, "message": m})
            sid = d["session"]
        self.assertTrue(d["done"])
        self.assertIn("NOT confirmed", d["reply"])
        db = connect(self.db)
        rows = list_enquiries(db); db.close()
        self.assertEqual((len(rows), rows[0]["name"]), (1, "Jane"))
        self.assertEqual(len(list(self.out.glob("*-whatsapp.txt"))), 1)

    def test_sessions_are_separate(self):
        _, a = post(self.base, {"session": "", "message": "I want to order"})
        _, b = post(self.base, {"session": "", "message": "what time do you close"})
        self.assertNotEqual(a["session"], b["session"])
        _, a2 = post(self.base, {"session": a["session"], "message": "two pizzas"})
        self.assertIn("collection or delivery", a2["reply"])   # A still mid-order

    def test_forged_session_gets_new_chat(self):
        status, d = post(self.base, {"session": "forged", "message": "hello"})
        self.assertEqual(status, 200)
        self.assertNotEqual(d["session"], "forged")

    def test_bad_requests_rejected(self):
        self.assertEqual(post(self.base, None, raw=b"not json")[0], 400)
        self.assertEqual(post(self.base, {"message": 123})[0], 400)
        self.assertEqual(post(self.base, {"nothing": 1})[0], 400)
        self.assertEqual(post(self.base, None, raw=b"x" * 5000)[0], 413)

    def test_html_is_not_interpreted_server_side(self):
        _, d = post(self.base, {"session": "", "message": "<script>alert(1)</script>"})
        self.assertEqual(d["done"], False)  # handled as plain text, no crash

    def test_long_message_is_truncated_not_crashing(self):
        status, _ = post(self.base, {"session": "", "message": "a" * 3000})
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
