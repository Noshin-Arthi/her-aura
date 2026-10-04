"""SQL-level checks: prove what the UI/API did by querying the database directly.
These are the kind of queries a QA engineer runs to verify data, so they use raw SQL on purpose."""
from datetime import date

from sqlalchemy import text


def test_booking_writes_consistent_rows(logged_in_client, db):
    doctor = logged_in_client.get("/api/doctors").json()[0]
    slot = logged_in_client.get(f"/api/doctors/{doctor['id']}/slots").json()[0]
    logged_in_client.post("/api/appointments", json={"slot_id": slot["id"], "reason": "Pelvic pain"})

    row = db.execute(text("""
        SELECT a.status, a.reason, s.is_booked, d.full_name
        FROM appointments a
        JOIN slots s   ON s.id = a.slot_id
        JOIN doctors d ON d.id = s.doctor_id
        WHERE a.slot_id = :slot_id
    """), {"slot_id": slot["id"]}).one()
    assert row.status == "booked" and row.reason == "Pelvic pain"
    assert row.is_booked == 1
    assert row.full_name == doctor["full_name"]


def test_no_slot_has_two_active_appointments(logged_in_client, db):
    duplicates = db.execute(text("""
        SELECT slot_id, COUNT(*) AS n
        FROM appointments
        WHERE status = 'booked'
        GROUP BY slot_id
        HAVING COUNT(*) > 1
    """)).all()
    assert duplicates == []


def test_no_orphan_appointments(db):
    # Anti-join: appointments whose slot no longer exists.
    orphans = db.execute(text("""
        SELECT a.id FROM appointments a
        LEFT JOIN slots s ON s.id = a.slot_id
        WHERE s.id IS NULL
    """)).all()
    assert orphans == []


def test_password_is_stored_hashed(client, new_user_payload, db):
    client.post("/api/auth/register", json=new_user_payload)
    stored = db.execute(text("SELECT password_hash FROM users WHERE email = :e"),
                        {"e": new_user_payload["email"]}).scalar_one()
    assert stored != new_user_payload["password"]
    assert stored.startswith("pbkdf2_sha256$")


def test_log_saved_with_exact_values(logged_in_client, db):
    logged_in_client.post("/api/logs", json={"log_date": date.today().isoformat(), "pain_level": 7, "period_flow": "heavy"})
    row = db.execute(text("SELECT pain_level, period_flow FROM symptom_logs")).one()
    assert (row.pain_level, row.period_flow) == (7, "heavy")
