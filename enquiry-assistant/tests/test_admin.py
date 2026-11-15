import base64
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from src.collector import Enquiry
from src.database import connect, save_enquiry
from src.webapp import ChatApp, make_server

PW = "test-pass-123"


def auth(user="admin", pw=PW):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


class TestAdmin(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "t.db"
        db = connect(self.db)
        self.id1 = save_enquiry(db, Enquiry("order", "order", "pizza", name="Jane", items="pizza"))
        self.id2 = save_enquiry(db, Enquiry("callback", "complaint", "cold", name="Bob", needs_human=True))
        db.close()
        self.start(PW)

    def start(self, password):
        if hasattr(self, "server"):
            self.server.shutdown(); self.server.server_close()
        app = ChatApp(self.db, Path(self.tmp.name) / "out", admin_password=password)
        self.server = make_server(port=0, app=app)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.tmp.cleanup()

    def call(self, path, headers=None, body=None):
        req = urllib.request.Request(self.base + path, headers=headers or {},
                                     data=None if body is None else json.dumps(body).encode())
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read() or b"null") if "json" in r.headers["Content-Type"] else r.read()
        except urllib.error.HTTPError as e:
            return e.code, None

    def test_login_required_everywhere(self):
        for p in ["/admin", "/api/admin/enquiries"]:
            self.assertEqual(self.call(p)[0], 401, p)
        self.assertEqual(self.call("/api/admin/handled", body={"id": 1},
                                   headers={"X-Requested-With": "admin"})[0], 401)

    def test_wrong_credentials_rejected(self):
        self.assertEqual(self.call("/api/admin/enquiries", auth(pw="wrong"))[0], 401)
        self.assertEqual(self.call("/api/admin/enquiries", auth(user="root"))[0], 401)
        self.assertEqual(self.call("/api/admin/enquiries", {"Authorization": "Basic !!!"})[0], 401)
        self.assertEqual(self.call("/api/admin/enquiries", {"Authorization": "garbage"})[0], 401)

    def test_disabled_when_no_password_set(self):
        self.start(None)
        self.assertEqual(self.call("/api/admin/enquiries", auth())[0], 503)
        self.start("")
        self.assertEqual(self.call("/admin", auth(pw=""))[0], 503)

    def test_views(self):
        _, rows = self.call("/api/admin/enquiries?view=all", auth())
        self.assertEqual({r["name"] for r in rows}, {"Jane", "Bob"})
        _, rows = self.call("/api/admin/enquiries?view=orders", auth())
        self.assertEqual([r["name"] for r in rows], ["Jane"])
        _, rows = self.call("/api/admin/enquiries?view=human", auth())
        self.assertEqual([r["name"] for r in rows], ["Bob"])
        _, rows = self.call("/api/admin/enquiries?view=nonsense", auth())
        self.assertEqual(len(rows), 2)   # unknown view falls back to "to do"

    def test_mark_handled_removes_from_todo(self):
        h = {**auth(), "X-Requested-With": "admin", "Content-Type": "application/json"}
        self.assertEqual(self.call("/api/admin/handled", h, {"id": self.id1})[0], 200)
        _, rows = self.call("/api/admin/enquiries?view=open", auth())
        self.assertEqual([r["name"] for r in rows], ["Bob"])
        self.assertEqual(self.call("/api/admin/handled", h, {"id": 9999})[0], 404)

    def test_csrf_header_required_for_changes(self):
        self.assertEqual(self.call("/api/admin/handled", auth(), {"id": self.id1})[0], 403)
        _, rows = self.call("/api/admin/enquiries?view=open", auth())
        self.assertEqual(len(rows), 2)   # nothing changed

    def test_bad_ids_rejected(self):
        h = {**auth(), "X-Requested-With": "admin"}
        for bad in [{"id": "x"}, {"nope": 1}, {"id": None}]:
            self.assertEqual(self.call("/api/admin/handled", h, bad)[0], 400, bad)

    def test_admin_page_served_after_login(self):
        status, body = self.call("/admin", auth())
        self.assertEqual(status, 200)
        self.assertIn(b"Enquiries dashboard", body)

    def test_chat_still_public(self):
        req = urllib.request.Request(self.base + "/api/chat", data=json.dumps(
            {"session": "", "message": "hi"}).encode())
        self.assertEqual(urllib.request.urlopen(req).status, 200)


if __name__ == "__main__":
    unittest.main()
