"""Appointment booking rules. Business logic lives here, not in the routes."""
from datetime import datetime, timedelta

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Appointment, Slot

CANCEL_CUTOFF_HOURS = 2


class BookingError(Exception):
    """Raised when a booking or cancellation breaks a business rule."""


def book_slot(db: Session, patient_id: int, slot_id: int, reason: str, now: datetime | None = None) -> Appointment:
    now = now or datetime.now()
    slot = db.get(Slot, slot_id)
    if slot is None:
        raise BookingError("Slot not found")
    if slot.starts_at <= now:
        raise BookingError("Cannot book a slot in the past")

    # Atomic claim: only one request can flip is_booked from False to True.
    # This prevents double booking when two patients click at the same moment.
    result = db.execute(
        update(Slot).where(Slot.id == slot_id, Slot.is_booked.is_(False)).values(is_booked=True)
    )
    if result.rowcount != 1:
        db.rollback()
        raise BookingError("Slot is already booked")

    appointment = Appointment(patient_id=patient_id, slot_id=slot_id, reason=reason)
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def cancel_appointment(db: Session, patient_id: int, appointment_id: int, now: datetime | None = None) -> Appointment:
    now = now or datetime.now()
    appointment = db.get(Appointment, appointment_id)
    if appointment is None or appointment.patient_id != patient_id:
        raise BookingError("Appointment not found")
    if appointment.status != "booked":
        raise BookingError("Only booked appointments can be cancelled")
    if appointment.slot.starts_at - now < timedelta(hours=CANCEL_CUTOFF_HOURS):
        raise BookingError(f"Appointments can only be cancelled at least {CANCEL_CUTOFF_HOURS} hours before")

    appointment.status = "cancelled"
    appointment.slot.is_booked = False
    db.commit()
    return appointment
