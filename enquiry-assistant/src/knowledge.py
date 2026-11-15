"""Loads the business-approved facts and checks they are complete.

Why this exists: the assistant must never invent facts. Everything it says
comes from data/business.json, which the business owner approves.
"""
import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "business.json"

REQUIRED_SECTIONS = [
    "business", "opening_hours", "ordering", "bookings",
    "menu_highlights", "allergens", "payments",
    "refunds_and_complaints", "faqs", "escalation_topics",
]
DAYS = ["monday", "tuesday", "wednesday", "thursday",
        "friday", "saturday", "sunday"]


def load_knowledge(path=DEFAULT_PATH):
    """Read the JSON file and return it as a Python dictionary."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def missing_sections(data):
    """Return required sections that are absent."""
    return [s for s in REQUIRED_SECTIONS if s not in data]


def missing_days(data):
    """Return days of the week with no opening-hours entry."""
    hours = data.get("opening_hours", {})
    return [d for d in DAYS if d not in hours]


def find_todos(data, _prefix=""):
    """Walk the whole file and list every value still marked 'TODO'."""
    found = []
    if isinstance(data, dict):
        for key, value in data.items():
            found += find_todos(value, f"{_prefix}{key}.")
    elif isinstance(data, list):
        for i, value in enumerate(data):
            found += find_todos(value, f"{_prefix}{i}.")
    elif isinstance(data, str) and data.startswith("TODO"):
        found.append(_prefix.rstrip("."))
    return found


if __name__ == "__main__":
    kb = load_knowledge()
    todos = find_todos(kb)
    print(f"Loaded knowledge for: {kb['business']['name']}")
    print(f"Unconfirmed (TODO) fields: {len(todos)}")
    for t in todos:
        print("  -", t)
