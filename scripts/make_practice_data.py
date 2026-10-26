"""Build practice.db: the real Her Aura schema filled with realistic fake data, for SQL practice.

  python scripts/make_practice_data.py            # writes ./practice.db (git-ignored, like every *.db)
  sqlite3 practice.db                             # or open it in DBeaver / DB Browser for SQLite

Deterministic (fixed random seed), so everyone gets the same rows and the same query answers.
Every name is fictional. Re-running deletes and rebuilds the file.
"""
import os
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parent.parent
DB_FILE = ROOT / "practice.db"
os.environ["DATABASE_URL"] = f"sqlite:///{DB_FILE.as_posix()}"   # must be set before importing app.db
sys.path.insert(0, str(ROOT))

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    Appointment, Doctor, DoctorReview, EmotionalCheckIn, HealthIssueLog, Slot, SleepLog, SymptomLog, User,
)
from app.security import hash_password  # noqa: E402
from app.seed import SLOT_HOURS, seed_demo_data  # noqa: E402
from app.services.doctors import seed_profiles  # noqa: E402
from app.services.health_suggestions import CATEGORIES  # noqa: E402

rng = random.Random(2026)
FIRST = ["Ayesha", "Fatema", "Nadia", "Sumaiya", "Tasnim", "Rima", "Mitu", "Lamia", "Sadia", "Farzana",
         "Nusrat", "Jannat", "Tania", "Shirin", "Rupa", "Mim", "Priya", "Anika", "Riya", "Samira"]
LAST = ["Rahman", "Islam", "Hossain", "Akter", "Khan", "Chowdhury", "Ahmed", "Begum", "Sultana", "Karim"]
REASONS = ["Checkup", "Pelvic pain", "Irregular cycle", "Follow-up", "Headache", "Skin rash", "Toothache", ""]


def main() -> None:
    engine.dispose()
    DB_FILE.unlink(missing_ok=True)
    Base.metadata.create_all(engine)
    today = date.today()
    with SessionLocal() as db:
        seed_demo_data(db)          # 3 clinics, 10 doctors, future slots
        seed_profiles(db)           # profiles + a few sample reviews

        # Past slots too, so there are completed visits and history to query.
        for doctor in db.query(Doctor).all():
            for back in range(1, 61):
                for hour in SLOT_HOURS:
                    if rng.random() < 0.5:
                        db.add(Slot(doctor_id=doctor.id, starts_at=datetime.combine(today - timedelta(days=back), time(hour))))
        db.commit()

        users = []
        for i in range(20):
            name = f"{FIRST[i]} {rng.choice(LAST)}"
            users.append(User(email=f"{FIRST[i].lower()}{i}@example.com", full_name=name,
                              password_hash=hash_password("Practice123!"),
                              plan="premium" if i % 5 == 0 else "free",
                              created_at=datetime.combine(today - timedelta(days=rng.randint(10, 120)), time(9))))
        users.append(User(email="dr.demo@example.com", full_name="Demo Doctor Account", role="doctor",
                          password_hash=hash_password("Practice123!")))
        users.append(User(email="newbie@example.com", full_name="No Activity Yet", password_hash=hash_password("Practice123!")))
        db.add_all(users)
        db.commit()
        patients = [u for u in users if u.role == "patient" and u.email != "newbie@example.com"]

        # Appointments: past ones are completed or cancelled, future ones booked or cancelled.
        slots = db.query(Slot).all()
        rng.shuffle(slots)
        now = datetime.now()
        for slot in slots[:220]:
            patient = rng.choice(patients)
            if slot.starts_at < now:
                status = rng.choices(["completed", "cancelled"], weights=[8, 2])[0]
            else:
                status = rng.choices(["booked", "cancelled"], weights=[7, 3])[0]
            if status in ("booked", "completed"):
                slot.is_booked = True
            db.add(Appointment(patient_id=patient.id, slot_id=slot.id, reason=rng.choice(REASONS), status=status,
                               created_at=slot.starts_at - timedelta(days=rng.randint(1, 10))))
        db.commit()

        # Real reviews for some completed visits (one per appointment).
        for appt in db.query(Appointment).filter(Appointment.status == "completed").all():
            if rng.random() < 0.35:
                db.add(DoctorReview(doctor_id=appt.slot.doctor_id, patient_id=appt.patient_id, appointment_id=appt.id,
                                    rating=rng.choices([1, 2, 3, 4, 5], weights=[1, 1, 3, 6, 7])[0],
                                    comment=rng.choice(["Very helpful", "Long wait", "Explained clearly", "OK", ""])))
        db.commit()

        # Daily logs over the last 60 days (unique per user per day).
        categories = list(CATEGORIES)
        for u in patients:
            active_days = sorted(rng.sample(range(60), rng.randint(5, 40)))
            for back in active_days:
                d = today - timedelta(days=back)
                db.add(SymptomLog(user_id=u.id, log_date=d, pain_level=rng.randint(0, 9),
                                  period_flow=rng.choices(["none", "light", "medium", "heavy"], weights=[10, 2, 2, 1])[0],
                                  bloating=rng.random() < 0.3, pelvic_or_abdominal_pain=rng.random() < 0.2,
                                  bbt_celsius=round(rng.uniform(36.1, 37.1), 2) if rng.random() < 0.4 else None))
                if rng.random() < 0.6:
                    db.add(SleepLog(user_id=u.id, log_date=d, hours=round(rng.uniform(4, 9.5), 1), quality=rng.randint(1, 5)))
                if rng.random() < 0.5:
                    db.add(EmotionalCheckIn(user_id=u.id, log_date=d, mood=rng.randint(1, 5), stress=rng.randint(1, 10),
                                            energy=rng.randint(1, 5), areas=",".join(rng.sample(["work", "family", "money", "health", "home"], 2))))
                for _ in range(rng.choices([0, 1, 2], weights=[5, 4, 1])[0]):   # several issues on one day are allowed
                    db.add(HealthIssueLog(user_id=u.id, log_date=d, category=rng.choice(categories),
                                          severity=rng.randint(1, 10), notes=""))
        db.commit()

        counts = {t.name: db.scalar(select(func.count()).select_from(t)) for t in Base.metadata.sorted_tables}
    engine.dispose()
    print(f"Wrote {DB_FILE.name}")
    for name, n in counts.items():
        print(f"  {name:<22} {n:>6} rows")


if __name__ == "__main__":
    main()
