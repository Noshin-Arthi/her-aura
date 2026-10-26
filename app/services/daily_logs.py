"""Daily log helpers shared by the HTML pages and the JSON API."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SymptomLog

MAX_PERIOD_DAYS = 15
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


def log_period(db: Session, user_id: int, start: date, end: date | None, flow: str, today: date) -> tuple[date, date]:
    """Record one period from `start` to `end` as daily flow logs. No end date means it is still going (until today).

    Days inside the range keep any flow already logged; days without a log get `flow`. Flow days directly
    touching the range on either side are cleared, so entering new dates corrects an earlier entry.
    """
    end_day = end or today
    if flow not in ("light", "medium", "heavy"):
        raise LogError("Please choose a flow.")
    if start > today or end_day > today:
        raise LogError("You cannot log a future date.")
    if end_day < start:
        raise LogError("The end date cannot be before the start date.")
    if (end_day - start).days + 1 > MAX_PERIOD_DAYS:
        raise LogError(f"A period can be at most {MAX_PERIOD_DAYS} days. Please check the dates.")

    logs = {l.log_date: l for l in db.scalars(select(SymptomLog).where(SymptomLog.user_id == user_id))}
    day = start
    while day <= end_day:
        log = logs.get(day)
        if log is None:
            db.add(SymptomLog(user_id=user_id, log_date=day, period_flow=flow))
        elif log.period_flow == "none":
            log.period_flow = flow
        day += timedelta(days=1)
    for edge, step in ((end_day, 1), (start, -1)):
        day = edge + timedelta(days=step)
        while day in logs and logs[day].period_flow != "none":
            logs[day].period_flow = "none"
            day += timedelta(days=step)
    db.commit()
    return start, end_day
