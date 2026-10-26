"""Doctor profiles, reviews and the combined "near me" list."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Appointment, Doctor, DoctorProfile, DoctorReview
from app.services import geo, osm

# Fictional profiles for the fictional demo doctors (seeded once, also on an existing live database).
PROFILES = {
    "Dr. Ayesha Rahman": ("MBBS, FCPS (Obstetrics & Gynaecology)", 12, "Bangla, English", "Focuses on menstrual health, PCOS and preventive gynecological care."),
    "Dr. Farhana Karim": ("MBBS, MS (Gynecologic Oncology)", 15, "Bangla, English", "Specialist in early detection and treatment of ovarian and cervical cancers."),
    "Dr. Nusrat Jahan": ("MBBS, DGO", 8, "Bangla, English, Hindi", "General gynecology, pregnancy planning and menopause care."),
    "Dr. Imran Hossain": ("MBBS, FCPS (Medicine)", 10, "Bangla, English", "First point of contact for fevers, fatigue, check-ups and referrals."),
    "Dr. Sadia Islam": ("MBBS, DDV (Dermatology)", 9, "Bangla, English", "Skin rashes, acne, hair fall and allergic skin conditions."),
    "Dr. Tanvir Ahmed": ("BDS, MS (Conservative Dentistry)", 11, "Bangla, English", "Toothache, root canal treatment and preventive dental care."),
    "Dr. Mehedi Hasan": ("MBBS, MD (Neurology)", 13, "Bangla, English", "Recurring headaches, migraine and nerve-related symptoms."),
    "Dr. Rumana Chowdhury": ("MBBS, MS (Orthopedics)", 14, "Bangla, English", "Joint and back pain, sports injuries and posture problems."),
    "Dr. Shafiq Rahman": ("MBBS, FCPS (Psychiatry)", 16, "Bangla, English", "Stress, low mood, anxiety and sleep problems."),
    "Dr. Lamia Akter": ("MBBS, FCPS (Gastroenterology)", 9, "Bangla, English", "Stomach pain, digestion and liver health."),
}
# A few clearly labelled sample reviews so the demo shows ratings. Shown with a "Sample review" tag.
SAMPLE_REVIEWS = {
    "Dr. Ayesha Rahman": [(5, "Explained everything clearly and didn't rush."), (4, "Helpful, though the wait was long."), (5, "Very caring.")],
    "Dr. Sadia Islam": [(4, "Good advice for my skin rash."), (5, "Hair fall improved after the treatment plan.")],
    "Dr. Tanvir Ahmed": [(5, "Painless root canal!"), (5, "Very professional."), (4, "Good, a bit expensive."), (5, "Highly recommend.")],
    "Dr. Imran Hossain": [(4, "Quick and thorough check-up.")],
}


def seed_profiles(db: Session) -> None:
    """Idempotent: adds missing profiles and sample reviews. Safe to run on every start."""
    doctors = {d.full_name: d for d in db.scalars(select(Doctor))}
    have_profiles = set(db.scalars(select(DoctorProfile.doctor_id)))
    for name, (qual, years, langs, bio) in PROFILES.items():
        d = doctors.get(name)
        if d and d.id not in have_profiles:
            db.add(DoctorProfile(doctor_id=d.id, qualifications=qual, years_experience=years, languages=langs, bio=bio))
    if not db.scalar(select(DoctorReview.id).where(DoctorReview.is_sample.is_(True)).limit(1)):
        for name, reviews in SAMPLE_REVIEWS.items():
            d = doctors.get(name)
            if d:
                db.add_all(DoctorReview(doctor_id=d.id, rating=r, comment=c, reviewer_name="Sample patient", is_sample=True)
                           for r, c in reviews)
    db.commit()


def rating_stats(db: Session) -> tuple[dict[int, tuple[float, int]], float]:
    """Per doctor (average, count), plus the overall mean used by the weighted rating."""
    rows = db.execute(select(DoctorReview.doctor_id, func.avg(DoctorReview.rating), func.count(DoctorReview.id))
                      .group_by(DoctorReview.doctor_id)).all()
    stats = {doc_id: (float(avg), int(n)) for doc_id, avg, n in rows}
    overall = db.scalar(select(func.avg(DoctorReview.rating)))
    return stats, float(overall) if overall is not None else geo.DEFAULT_MEAN


class ReviewError(Exception):
    """Raised when a review isn't allowed."""


def add_review(db: Session, patient_id: int, doctor_id: int, appointment_id: int, rating: int, comment: str,
               reviewer_name: str, now: datetime | None = None) -> DoctorReview:
    now = now or datetime.now()
    if not 1 <= rating <= 5:
        raise ReviewError("Rating must be between 1 and 5.")
    appt = db.get(Appointment, appointment_id)
    if appt is None or appt.patient_id != patient_id or appt.slot.doctor_id != doctor_id:
        raise ReviewError("You can only review doctors you had an appointment with.")
    if appt.status == "cancelled":
        raise ReviewError("Cancelled appointments can't be reviewed.")
    if appt.slot.starts_at > now:
        raise ReviewError("You can review this doctor after your visit.")
    if db.scalar(select(DoctorReview.id).where(DoctorReview.appointment_id == appointment_id)):
        raise ReviewError("You already reviewed this visit.")
    review = DoctorReview(doctor_id=doctor_id, patient_id=patient_id, appointment_id=appointment_id,
                          rating=rating, comment=comment[:1000], reviewer_name=reviewer_name.split(" ")[0])
    db.add(review)
    db.commit()
    return review


def her_aura_doctors(db: Session, lat: float, lng: float, specialty: str | None) -> list[dict]:
    stats, mean = rating_stats(db)
    query = select(Doctor)
    if specialty:
        query = query.where(Doctor.specialty == specialty)
    out = []
    for d in db.scalars(query):
        avg, count = stats.get(d.id, (None, 0))
        c = d.clinic
        if c.latitude is None or c.longitude is None:
            continue
        out.append({
            "source": "her_aura", "id": d.id, "name": d.full_name, "specialty": d.specialty, "clinic": c.name,
            "address": c.address, "phone": c.phone, "lat": c.latitude, "lng": c.longitude,
            "distance_km": round(geo.haversine_km(lat, lng, c.latitude, c.longitude), 1),
            "rating": round(avg, 1) if avg is not None else None, "review_count": count,
            "score": geo.weighted_rating(avg, count, mean), "profile_url": f"/doctors/{d.id}",
            "directions_url": osm.directions_url(c.latitude, c.longitude),
        })
    return out


def external_places(lat: float, lng: float, specialty: str | None, radius_km: float) -> list[dict]:
    out = []
    for p in osm.nearby_places(lat, lng, radius_km):
        if not osm.matches_specialty(p, specialty):
            continue
        dist = geo.haversine_km(lat, lng, p["lat"], p["lng"])
        if dist > radius_km:
            continue
        out.append({**p, "source": "openstreetmap", "distance_km": round(dist, 1), "rating": None,
                    "review_count": 0, "score": None, "directions_url": osm.directions_url(p["lat"], p["lng"])})
    return out
