"""One-command demo (no accounts, keys or cost). From this folder run:

    python3 run_demo.py

Chat page : http://127.0.0.1:8000/
Dashboard : http://127.0.0.1:8000/admin   (user: admin  password: demo)
Uses its own demo database + outbox, with FAKE sample enquiries. Alerts are
written to data/demo_outbox/ instead of being sent anywhere.
"""
from pathlib import Path

from src.database import connect
from src.demo_data import seed_demo
from src.webapp import ChatApp, make_server

DATA = Path(__file__).resolve().parent / "data"

if __name__ == "__main__":
    db_path = DATA / "demo.db"
    conn = connect(db_path)
    print(f"Seeded {seed_demo(conn)} fake sample enquiries.")
    conn.close()
    app = ChatApp(db_path, DATA / "demo_outbox", admin_password="demo")
    server = make_server(app=app)
    print("Chat:      http://127.0.0.1:8000/")
    print("Dashboard: http://127.0.0.1:8000/admin  (admin / demo)")
    print("Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
