"""Database tables (SQLAlchemy ORM)."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="patient")  # patient | doctor
    plan: Mapped[str] = mapped_column(String(20), default="free")     # free | premium
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    symptom_logs: Mapped[list["SymptomLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient", cascade="all, delete-orphan")


class Clinic(Base):
    __tablename__ = "clinics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    address: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(80), default="Dhaka")
    phone: Mapped[str] = mapped_column(String(30), default="")
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)

    doctors: Mapped[list["Doctor"]] = relationship(back_populates="clinic")


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    specialty: Mapped[str] = mapped_column(String(80))  # e.g. Gynecology, Gynecologic Oncology
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"))

    clinic: Mapped[Clinic] = relationship(back_populates="doctors")
    slots: Mapped[list["Slot"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")


class Slot(Base):
    """A bookable time slot for one doctor."""
    __tablename__ = "slots"
    __table_args__ = (UniqueConstraint("doctor_id", "starts_at", name="uq_slot_doctor_time"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)

    doctor: Mapped[Doctor] = relationship(back_populates="slots")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id"))
    reason: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(20), default="booked")  # booked | cancelled | completed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    patient: Mapped[User] = relationship(back_populates="appointments")
    slot: Mapped[Slot] = relationship()


class SymptomLog(Base):
    """One day's health log. Pain is 0-10. Flow: none | light | medium | heavy."""
    __tablename__ = "symptom_logs"
    __table_args__ = (UniqueConstraint("user_id", "log_date", name="uq_log_user_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    log_date: Mapped[date] = mapped_column(Date)
    period_flow: Mapped[str] = mapped_column(String(10), default="none")
    pain_level: Mapped[int] = mapped_column(Integer, default=0)
    pelvic_or_abdominal_pain: Mapped[bool] = mapped_column(Boolean, default=False)
    bloating: Mapped[bool] = mapped_column(Boolean, default=False)
    early_fullness: Mapped[bool] = mapped_column(Boolean, default=False)
    urinary_urgency: Mapped[bool] = mapped_column(Boolean, default=False)
    bbt_celsius: Mapped[float | None] = mapped_column(nullable=True)  # basal body temperature, taken on waking
    notes: Mapped[str] = mapped_column(Text, default="")

    user: Mapped[User] = relationship(back_populates="symptom_logs")


class HealthIssueLog(Base):
    """Any health complaint: headache, toothache, rash, hair fall, fatigue... Severity is 1-10."""
    __tablename__ = "health_issue_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    log_date: Mapped[date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(String(40))  # see app/services/health_suggestions.py CATEGORIES
    severity: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class SleepLog(Base):
    """One night's sleep. Quality is 1 (very poor) to 5 (very good)."""
    __tablename__ = "sleep_logs"
    __table_args__ = (UniqueConstraint("user_id", "log_date", name="uq_sleep_user_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    log_date: Mapped[date] = mapped_column(Date)  # the morning you woke up
    hours: Mapped[float] = mapped_column()
    quality: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(Text, default="")


class MindfulnessSession(Base):
    """A completed day of the beginner mindfulness programme."""
    __tablename__ = "mindfulness_sessions"
    __table_args__ = (UniqueConstraint("user_id", "program_day", name="uq_mind_user_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    program_day: Mapped[int] = mapped_column(Integer)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class AdUnlock(Base):
    """A rewarded ad: started, then claimed after it played to the end, unlocking one article for 24 hours."""
    __tablename__ = "ad_unlocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    article_slug: Mapped[str] = mapped_column(String(80))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    unlocked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EmotionalCheckIn(Base):
    """Daily emotional-load check-in. Mood 1-5, stress 1-10, energy 1-5. Areas: comma-separated keys."""
    __tablename__ = "emotional_checkins"
    __table_args__ = (UniqueConstraint("user_id", "log_date", name="uq_emotional_user_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    log_date: Mapped[date] = mapped_column(Date)
    mood: Mapped[int] = mapped_column(Integer)
    stress: Mapped[int] = mapped_column(Integer)
    energy: Mapped[int] = mapped_column(Integer)
    areas: Mapped[str] = mapped_column(String(200), default="")
    handoff: Mapped[str] = mapped_column(String(300), default="")   # one thing I could hand off
    notes: Mapped[str] = mapped_column(Text, default="")
