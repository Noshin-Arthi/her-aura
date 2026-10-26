"""API tests: doctors near me, profiles, reviews. Map provider replaced by fixture files."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.models import Appointment, Slot
from app.services import osm

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
DHANMONDI = {"lat": 23.7461, "lng": 90.3742}


@pytest.fixture(autouse=True)
def map_fixtures(monkeypatch):
    monkeypatch.setenv("OSM_FIXTURE", str(FIXTURES / "overpass_dhaka.json"))
    monkeypatch.setenv("NOMINATIM_FIXTURE", str(FIXTURES / "nominatim_dhanmondi.json"))


def past_visit(db, patient_id, doctor_name="Dr. Sadia Islam", status="booked", hours_ago=24):
    from app.models import Doctor
    doctor = db.query(Doctor).filter_by(full_name=doctor_name).one()
    slot = Slot(doctor_id=doctor.id, starts_at=datetime.now() - timedelta(hours=hours_ago), is_booked=True)
    db.add(slot)
    db.flush()
    appt = Appointment(patient_id=patient_id, slot_id=slot.id, status=status, reason="rash")
    db.add(appt)
    db.commit()
    return doctor.id, appt.id


def me(client):
    return client.get("/api/me").json()["id"]


# ---------- nearby ----------
def test_nearby_requires_login(client):
    assert client.get("/api/nearby", params=DHANMONDI).status_code == 401


def test_nearby_returns_her_aura_and_external_with_distances(logged_in_client):
    body = logged_in_client.get("/api/nearby", params={**DHANMONDI, "specialty": "Dermatology"}).json()
    assert [d["specialty"] for d in body["her_aura"]] == ["Dermatology"]
    assert all(d["distance_km"] >= 0 and "score" not in d for d in body["her_aura"] + body["external"])
    names = [p["name"] for p in body["external"]]
    assert "Sample Skin Clinic" in names and "Far Away Hospital" not in names   # outside the radius
    assert body["attribution"].startswith("Map data ©")


def test_rating_sort_puts_rated_doctors_first(logged_in_client):
    body = logged_in_client.get("/api/nearby", params={**DHANMONDI, "sort": "rating"}).json()
    ratings = [d["rating"] for d in body["her_aura"]]
    rated = [r for r in ratings if r is not None]
    assert rated and ratings[: len(rated)] == rated          # all rated before any unrated


def test_distance_sort(logged_in_client):
    body = logged_in_client.get("/api/nearby", params={**DHANMONDI, "sort": "distance"}).json()
    distances = [d["distance_km"] for d in body["her_aura"]]
    assert distances == sorted(distances)


@pytest.mark.parametrize("params", [{"lat": 91, "lng": 90}, {**DHANMONDI, "sort": "price"}])
def test_nearby_validation(logged_in_client, params):
    assert logged_in_client.get("/api/nearby", params=params).status_code == 422


def test_provider_failure_still_returns_her_aura_doctors(logged_in_client, monkeypatch):
    def broken(*a, **k):
        raise osm.ProviderError("Map service unavailable: TimeoutException")
    monkeypatch.setattr(osm, "nearby_places", broken)
    body = logged_in_client.get("/api/nearby", params=DHANMONDI).json()
    assert body["her_aura"] and body["external"] == [] and "unavailable" in body["provider_error"]


def test_geocode(client):
    assert client.get("/api/geocode", params={"q": "Dhanmondi"}).json()["lat"] == pytest.approx(23.7461)


# ---------- profile + reviews ----------
def test_profile_shows_details_sample_reviews_and_empty_history(logged_in_client):
    doctors = logged_in_client.get("/api/doctors", params={"specialty": "Dentistry"}).json()
    body = logged_in_client.get(f"/api/doctors/{doctors[0]['id']}").json()
    assert body["qualifications"] and body["years_experience"] > 0
    assert body["review_count"] == 4 and all(r["sample"] for r in body["reviews"])
    assert body["history"] == []


def test_patient_can_review_after_a_past_visit(logged_in_client, db):
    doctor_id, appt_id = past_visit(db, me(logged_in_client))
    before = logged_in_client.get(f"/api/doctors/{doctor_id}").json()
    assert before["history"][0]["can_review"] is True
    after = logged_in_client.post(f"/api/doctors/{doctor_id}/reviews",
                                  json={"appointment_id": appt_id, "rating": 4, "comment": "Clear advice"}).json()
    assert after["review_count"] == before["review_count"] + 1
    assert after["history"][0]["can_review"] is False
    mine = [r for r in after["reviews"] if not r["sample"]]
    assert mine[0]["reviewer"] == "Test" and mine[0]["rating"] == 4      # first name only


@pytest.mark.parametrize("case, detail", [
    ("future", "after your visit"),
    ("cancelled", "Cancelled"),
    ("twice", "already reviewed"),
    ("wrong_doctor", "had an appointment with"),
])
def test_review_rules(logged_in_client, db, case, detail):
    patient = me(logged_in_client)
    if case == "future":
        doctor_id, appt_id = past_visit(db, patient, hours_ago=-48)
    elif case == "cancelled":
        doctor_id, appt_id = past_visit(db, patient, status="cancelled")
    else:
        doctor_id, appt_id = past_visit(db, patient)
    if case == "twice":
        logged_in_client.post(f"/api/doctors/{doctor_id}/reviews", json={"appointment_id": appt_id, "rating": 5})
    if case == "wrong_doctor":
        doctor_id += 1
    r = logged_in_client.post(f"/api/doctors/{doctor_id}/reviews", json={"appointment_id": appt_id, "rating": 5})
    assert r.status_code == 409 and detail in r.json()["detail"]


def test_cannot_review_someone_elses_visit(client, new_user_payload, db):
    client.post("/api/auth/register", json=new_user_payload)
    doctor_id, appt_id = past_visit(db, me(client))
    client.post("/api/auth/logout")
    client.post("/api/auth/register", json={**new_user_payload, "email": "intruder@example.com"})
    assert client.post(f"/api/doctors/{doctor_id}/reviews", json={"appointment_id": appt_id, "rating": 1}).status_code == 409


@pytest.mark.parametrize("rating", [0, 6])
def test_rating_range(logged_in_client, db, rating):
    doctor_id, appt_id = past_visit(db, me(logged_in_client))
    assert logged_in_client.post(f"/api/doctors/{doctor_id}/reviews",
                                 json={"appointment_id": appt_id, "rating": rating}).status_code == 422


def test_seeding_profiles_is_idempotent(db):
    from app.models import DoctorProfile, DoctorReview
    from app.services.doctors import seed_profiles
    counts = (db.query(DoctorProfile).count(), db.query(DoctorReview).count())
    seed_profiles(db)
    assert (db.query(DoctorProfile).count(), db.query(DoctorReview).count()) == counts
