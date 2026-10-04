"""Daily log helpers shared by the HTML pages and the JSON API."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SymptomLog

COPIED_FIELDS = ("period_flow", "pain_level", "pelvic_or_abdominal_pain", "bloating", "early_fullness", "urinary_urgency")


class LogError(Exception):
    """Raised when a log action breaks a business rule."""


def copy_previous_day(db: Session, user_id: int, target: date) -> SymptomLog:
    """'Same as yesterday': copy the previous day's values onto `target`. Notes are not copied."""
    if target > date.today():
        raise LogError("You cannot log a future date.")
    if db.scalar(select(SymptomLog.id).where(SymptomLog.user_id == user_id, SymptomLog.log_date == target)):
        raise LogError("You already have a log for this date.")
    previous = db.scalar(select(SymptomLog).where(
        SymptomLog.user_id == user_id, SymptomLog.log_date == target - timedelta(days=1)))
    if previous is None:
        raise LogError("There is no log for the previous day to copy.")

    log = SymptomLog(user_id=user_id, log_date=target, **{f: getattr(previous, f) for f in COPIED_FIELDS})
    db.add(log)
    db.commit()
    return log
