"""Demo clinics, doctors and open slots, so a fresh install has something to book.
All names are fictional."""
from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Clinic, Doctor, Slot

# Fictional clinics with dummy phone numbers.
CLINICS = [
    ("Lakeside Women's Clinic", "House 12, Road 5, Dhanmondi", 23.7465, 90.3760, "+880-2-0000-0001"),
    ("Green Valley Health Center", "Plot 8, Gulshan Avenue", 23.7925, 90.4078, "+880-2-0000-0002"),
    ("Riverside General Hospital", "12 Lake Road, Mirpur", 23.8223, 90.3654, "+880-2-0000-0003"),
]
DOCTORS = [
    ("Dr. Ayesha Rahman", "Gynecology", 0),
    ("Dr. Farhana Karim", "Gynecologic Oncology", 0),
    ("Dr. Nusrat Jahan", "Gynecology", 1),
    ("Dr. Imran Hossain", "General Medicine", 2),
    ("Dr. Sadia Islam", "Dermatology", 1),
    ("Dr. Tanvir Ahmed", "Dentistry", 2),
    ("Dr. Mehedi Hasan", "Neurology", 2),
    ("Dr. Rumana Chowdhury", "Orthopedics", 2),
    ("Dr. Shafiq Rahman", "Psychiatry", 1),
    ("Dr. Lamia Akter", "Gastroenterology", 2),
]
SLOT_HOURS = [10, 11, 15, 16]
DAYS_AHEAD = 14


def seed_demo_data(db: Session) -> None:
    if db.scalar(select(Clinic.id).limit(1)):
        return
    clinics = [Clinic(name=n, address=a, latitude=lat, longitude=lng, phone=ph) for n, a, lat, lng, ph in CLINICS]
    db.add_all(clinics)
    db.flush()
    today = datetime.now().date()
    for name, specialty, clinic_index in DOCTORS:
        doctor = Doctor(full_name=name, specialty=specialty, clinic_id=clinics[clinic_index].id)
        db.add(doctor)
        db.flush()
        for day in range(1, DAYS_AHEAD + 1):
            for hour in SLOT_HOURS:
                db.add(Slot(doctor_id=doctor.id, starts_at=datetime.combine(today + timedelta(days=day), time(hour))))
    db.commit()
