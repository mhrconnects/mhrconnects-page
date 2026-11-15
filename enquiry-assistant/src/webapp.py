"""Web chat server (standard library only; nothing to install).

    python3 -m src.webapp            ->  http://127.0.0.1:8000

POST /api/chat  {"session": "...", "message": "..."}  ->  {"session", "reply", "done"}
Finished enquiries are saved to the database and the notifier is run.
Each browser gets its own conversation, kept in memory (lost on restart).
"""
import json
import secrets
import threading
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from src.collector import Conversation, MAX_INPUT
from src.database import DEFAULT_DB, connect, save_enquiry
from src.knowledge import load_knowledge
from src.notifier import DEFAULT_OUTBOX, default_channels, notify_new

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
STATIC = {"/": ("index.html", "text/html; charset=utf-8"),
          "/static/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/static/style.css": ("style.css", "text/css; charset=utf-8")}
MAX_BODY = 4096
MAX_SESSIONS = 500
HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
}


class ChatApp:
    def __init__(self, db_path=DEFAULT_DB, outbox=DEFAULT_OUTBOX):
        self.kb = load_knowledge()
        self.db_path, self.outbox = db_path, outbox
        self.sessions = OrderedDict()
        self.lock = threading.Lock()

    def chat(self, session_id, message):
        with self.lock:
            conv = self.sessions.get(session_id)
            if conv is None:                      # unknown/missing id -> new chat
                session_id = secrets.token_urlsafe(16)
                conv = Conversation(self.kb)
                self.sessions[session_id] = conv
                while len(self.sessions) > MAX_SESSIONS:
                    self.sessions.popitem(last=False)   # drop the oldest
            self.sessions.move_to_end(session_id)
            turn = conv.handle(message)
            if turn.done and turn.enquiry is not None:
                db = connect(self.db_path)
                try:
                    save_enquiry(db, turn.enquiry)
                    notify_new(db, default_channels(self.outbox))
                finally:
                    db.close()
            return session_id, turn


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in HEADERS.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj).encode())

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/health":
                return self._json(200, {"ok": True})
            if path in STATIC:
                name, ctype = STATIC[path]
                return self._send(200, (WEB_DIR / name).read_bytes(), ctype)
            self._json(404, {"error": "not found"})

        def do_POST(self):
            if self.path.split("?")[0] != "/api/chat":
                return self._json(404, {"error": "not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return self._json(400, {"error": "bad length"})
            if length <= 0 or length > MAX_BODY:
                return self._json(413 if length > MAX_BODY else 400,
                                  {"error": "bad size"})
            try:
                data = json.loads(self.rfile.read(length))
                message = data["message"]
                session = data.get("session", "")
                if not isinstance(message, str) or not isinstance(session, str):
                    raise ValueError
            except (ValueError, KeyError, TypeError):
                return self._json(400, {"error": "invalid request"})
            sid, turn = app.chat(session, message[:MAX_INPUT])
            self._json(200, {"session": sid, "reply": turn.reply, "done": turn.done})

        def log_message(self, *args):   # don't log requests (privacy)
            pass

    return Handler


def make_server(host="127.0.0.1", port=8000, app=None):
    return ThreadingHTTPServer((host, port), make_handler(app or ChatApp()))


if __name__ == "__main__":
    server = make_server()
    print("Chat running at http://127.0.0.1:8000  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
