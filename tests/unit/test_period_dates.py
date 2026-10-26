"""Period start and end dates: grouping flow days into periods, and logging a period by its dates."""
from dataclasses import dataclass
from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.models import SymptomLog, User
from app.services.cycle import cycle_phase
from app.services.daily_logs import LogError, log_period
from app.services.health_insights import average_period_length, period_ranges

TODAY = date(2026, 10, 20)


@dataclass
class Log:
    log_date: date
    period_flow: str = "medium"


def flow_days(start: date, days: int) -> list[Log]:
    return [Log(start + timedelta(days=i)) for i in range(days)]


def test_consecutive_flow_days_form_one_period():
    logs = flow_days(date(2026, 9, 1), 5) + flow_days(date(2026, 9, 29), 4)
    assert period_ranges(logs) == [(date(2026, 9, 1), date(2026, 9, 5)), (date(2026, 9, 29), date(2026, 10, 2))]
    assert average_period_length(logs) == 4.5


def test_days_without_flow_are_ignored():
    logs = flow_days(date(2026, 9, 1), 3) + [Log(date(2026, 9, 4), "none")]
    assert period_ranges(logs) == [(date(2026, 9, 1), date(2026, 9, 3))]
    assert average_period_length([]) is None


@pytest.mark.parametrize("today, phase", [
    (date(2026, 10, 2), "Period"),
    (date(2026, 10, 10), "Between periods"),
    (date(2026, 10, 25), "Pre-period week"),
    (date(2026, 10, 30), "Period due"),
])
def test_cycle_phase(today, phase):
    assert cycle_phase(date(2026, 10, 1), date(2026, 10, 5), date(2026, 10, 29), today) == phase


@pytest.fixture
def user_id(db):
    user = User(email="period@example.com", full_name="Period Test", password_hash="x")
    db.add(user)
    db.commit()
    return user.id


def flows(db, user_id) -> dict[date, str]:
    return {l.log_date: l.period_flow for l in db.scalars(select(SymptomLog).where(SymptomLog.user_id == user_id))}


def test_log_period_with_end_date(db, user_id):
    log_period(db, user_id, date(2026, 10, 1), date(2026, 10, 5), "heavy", TODAY)
    saved = flows(db, user_id)
    assert len(saved) == 5 and set(saved.values()) == {"heavy"}


def test_ongoing_period_runs_until_today_then_end_date_trims_it(db, user_id):
    log_period(db, user_id, date(2026, 10, 15), None, "medium", TODAY)
    assert max(d for d, f in flows(db, user_id).items() if f != "none") == TODAY

    log_period(db, user_id, date(2026, 10, 15), date(2026, 10, 18), "medium", TODAY)
    saved = flows(db, user_id)
    assert saved[date(2026, 10, 18)] == "medium"
    assert saved[date(2026, 10, 19)] == "none" and saved[TODAY] == "none"


def test_existing_daily_log_keeps_its_flow_and_symptoms(db, user_id):
    db.add(SymptomLog(user_id=user_id, log_date=date(2026, 10, 2), period_flow="light", bloating=True))
    db.commit()
    log_period(db, user_id, date(2026, 10, 1), date(2026, 10, 3), "heavy", TODAY)
    day_two = db.scalar(select(SymptomLog).where(SymptomLog.user_id == user_id, SymptomLog.log_date == date(2026, 10, 2)))
    assert day_two.period_flow == "light" and day_two.bloating is True


@pytest.mark.parametrize("start, end, message", [
    (date(2026, 10, 5), date(2026, 10, 1), "before the start"),
    (date(2026, 10, 19), date(2026, 10, 21), "future"),
    (date(2026, 10, 1), date(2026, 10, 16), "at most 15 days"),
])
def test_invalid_period_dates_rejected(db, user_id, start, end, message):
    with pytest.raises(LogError, match=message):
        log_period(db, user_id, start, end, "medium", TODAY)


def test_fifteen_day_period_is_allowed(db, user_id):
    assert log_period(db, user_id, date(2026, 10, 1), date(2026, 10, 15), "light", TODAY) == (date(2026, 10, 1), date(2026, 10, 15))


def test_cycle_page_saves_period_dates(logged_in_client):
    today = date.today()
    start, end = today - timedelta(days=6), today - timedelta(days=2)
    response = logged_in_client.post("/cycle/period", data={"start_date": start.isoformat(), "end_date": end.isoformat(),
                                                            "flow": "medium"}, follow_redirects=False)
    assert response.status_code == 303 and response.headers["location"] == "/cycle?saved=period"
    cycle = logged_in_client.get("/api/cycle/status").json()
    assert cycle["last_period_start"] == start.isoformat() and cycle["last_period_end"] == end.isoformat()
    assert cycle["periods"][0]["days"] == 5
    page = logged_in_client.get("/cycle")
    assert 'data-testid="period-row"' in page.text and "Cycle tracker" in page.text


def test_old_log_url_redirects_to_cycle_tracker(logged_in_client):
    response = logged_in_client.get("/log", follow_redirects=False)
    assert response.status_code == 301 and response.headers["location"] == "/cycle"
