"""US-05 AC3: many patients book the same slot at the same moment, exactly one wins.

Each thread uses its own DB session (like separate web requests). A Barrier releases them
together so they really race. The guard is the atomic UPDATE ... WHERE is_booked = false
in app/services/scheduling.py: only one UPDATE can match the row.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier

from sqlalchemy import text

from app.db import SessionLocal
from app.models import Slot, User
from app.security import hash_password
from app.services.scheduling import BookingError, book_slot

PATIENTS = 10


def test_only_one_of_ten_simultaneous_bookings_succeeds(db):
    slot = Slot(doctor_id=1, starts_at=datetime.now() + timedelta(days=3))
    users = [User(email=f"race{i}@example.com", full_name=f"Racer {i}", password_hash=hash_password("x" * 8))
             for i in range(PATIENTS)]
    db.add_all([slot, *users])
    db.commit()
    slot_id, user_ids = slot.id, [u.id for u in users]

    barrier = Barrier(PATIENTS)

    def attempt(user_id: int) -> str:
        with SessionLocal() as session:
            barrier.wait()  # all threads start booking together
            try:
                book_slot(session, user_id, slot_id, "race")
                return "booked"
            except BookingError:
                return "rejected"

    with ThreadPoolExecutor(max_workers=PATIENTS) as pool:
        results = list(pool.map(attempt, user_ids))

    assert results.count("booked") == 1, results
    assert results.count("rejected") == PATIENTS - 1

    # Prove it in the data, not just in the return values.
    count = db.execute(text("SELECT COUNT(*) FROM appointments WHERE slot_id = :s AND status = 'booked'"),
                       {"s": slot_id}).scalar_one()
    assert count == 1
