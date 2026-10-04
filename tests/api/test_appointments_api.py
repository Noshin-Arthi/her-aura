"""API tests: doctors, slots and booking rules."""
from datetime import datetime, timedelta

from app.models import Slot


def first_open_slot(client):
    doctor = client.get("/api/doctors").json()[0]
    return doctor, client.get(f"/api/doctors/{doctor['id']}/slots").json()[0]


def test_doctors_are_listed_with_clinic(client):
    doctors = client.get("/api/doctors").json()
    assert len(doctors) >= 3
    assert all(d["clinic_name"] for d in doctors)


def test_filter_doctors_by_specialty(client):
    doctors = client.get("/api/doctors", params={"specialty": "Gynecologic Oncology"}).json()
    assert doctors and all(d["specialty"] == "Gynecologic Oncology" for d in doctors)


def test_book_slot_removes_it_from_open_slots(logged_in_client):
    doctor, slot = first_open_slot(logged_in_client)
    response = logged_in_client.post("/api/appointments", json={"slot_id": slot["id"], "reason": "Checkup"})
    assert response.status_code == 201
    assert response.json()["status"] == "booked"
    open_ids = [s["id"] for s in logged_in_client.get(f"/api/doctors/{doctor['id']}/slots").json()]
    assert slot["id"] not in open_ids


def test_double_booking_is_rejected(logged_in_client):
    _, slot = first_open_slot(logged_in_client)
    logged_in_client.post("/api/appointments", json={"slot_id": slot["id"]})
    second = logged_in_client.post("/api/appointments", json={"slot_id": slot["id"]})
    assert second.status_code == 409
    assert second.json()["detail"] == "Slot is already booked"


def test_cannot_book_past_slot(logged_in_client, db):
    past = Slot(doctor_id=1, starts_at=datetime.now() - timedelta(hours=1))
    db.add(past)
    db.commit()
    assert logged_in_client.post("/api/appointments", json={"slot_id": past.id}).status_code == 409


def test_cancel_frees_the_slot(logged_in_client):
    doctor, slot = first_open_slot(logged_in_client)
    appointment = logged_in_client.post("/api/appointments", json={"slot_id": slot["id"]}).json()
    cancelled = logged_in_client.post(f"/api/appointments/{appointment['id']}/cancel")
    assert cancelled.json()["status"] == "cancelled"
    open_ids = [s["id"] for s in logged_in_client.get(f"/api/doctors/{doctor['id']}/slots").json()]
    assert slot["id"] in open_ids


def test_cannot_cancel_within_two_hours(logged_in_client, db):
    soon = Slot(doctor_id=1, starts_at=datetime.now() + timedelta(hours=1))
    db.add(soon)
    db.commit()
    appointment = logged_in_client.post("/api/appointments", json={"slot_id": soon.id}).json()
    assert logged_in_client.post(f"/api/appointments/{appointment['id']}/cancel").status_code == 409
