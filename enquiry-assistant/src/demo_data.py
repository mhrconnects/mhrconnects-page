"""Fake sample enquiries so the demo dashboard isn't empty. All FAKE data."""
from datetime import datetime, timedelta, timezone

from src.collector import Enquiry
from src.database import list_enquiries, save_enquiry

SAMPLES = [
    dict(kind="order", category="order", message="two cheesy pizzas please", name="Jane Smith",
         phone="07123456789", items="two cheesy pizzas please", fulfilment="delivery",
         address="12 High Street, Ashton-under-Lyne OL6 1AA",
         notes=["Delivery area to be confirmed by staff."]),
    dict(kind="order", category="order", message="large margherita", name="Ali Khan",
         phone="07700900111", items="large margherita", fulfilment="collection"),
    dict(kind="callback", category="allergy", message="is the base gluten free? my son is coeliac",
         name="Mark Taylor", phone="01615550123", needs_human=True,
         notes=["Allergy/dietary question: staff must answer."]),
    dict(kind="callback", category="complaint", message="my pizza arrived cold",
         name="Sam Jones", phone="07700900123", needs_human=True,
         notes=["Complaint: staff to follow up."]),
    dict(kind="order", category="order", message="can I get a meal deal 1", name="Priya",
         status="incomplete", needs_human=True, items="a meal deal 1", fulfilment="collection",
         notes=["Customer did not give a valid phone number."]),
]


def seed_demo(conn):
    """Add the samples once. Returns how many were added (0 if data exists)."""
    if list_enquiries(conn, limit=1):
        return 0
    now = datetime.now(timezone.utc)
    for i, s in enumerate(SAMPLES):
        created = (now - timedelta(minutes=12 * (len(SAMPLES) - i))).isoformat(timespec="seconds")
        save_enquiry(conn, Enquiry(created_at=created, **s))
    return len(SAMPLES)
