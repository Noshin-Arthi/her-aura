"""Unit tests for the rule-based insight engine. Boundary values matter here: 11 vs 12 days."""
from dataclasses import dataclass
from datetime import date, timedelta

import pytest

from app.services.health_insights import average_cycle_length, build_insight, period_start_dates, red_flag_symptom_days

TODAY = date(2026, 10, 31)


@dataclass
class FakeLog:
    log_date: date
    period_flow: str = "none"
    pelvic_or_abdominal_pain: bool = False
    bloating: bool = False
    early_fullness: bool = False


def symptom_days(count: int) -> list[FakeLog]:
    return [FakeLog(TODAY - timedelta(days=i), bloating=True) for i in range(count)]


@pytest.mark.parametrize("days, expected_flag", [(0, False), (11, False), (12, True), (20, True)])
def test_red_flag_boundary(days, expected_flag):
    assert build_insight(symptom_days(days), TODAY)["red_flag"] is expected_flag


def test_symptoms_older_than_30_days_are_ignored():
    old = [FakeLog(TODAY - timedelta(days=31 + i), bloating=True) for i in range(15)]
    assert red_flag_symptom_days(old, TODAY) == 0


@pytest.mark.parametrize("days_ago, counted", [(0, True), (29, True), (30, False)])
def test_rolling_window_edges(days_ago, counted):
    # The window is today plus the 29 days before it: 30 days in total.
    logs = [FakeLog(TODAY - timedelta(days=days_ago), bloating=True)]
    assert red_flag_symptom_days(logs, TODAY) == (1 if counted else 0)


def test_window_across_leap_day():
    # 2028 is a leap year: from Mar 10 back 29 days includes Feb 29.
    today = date(2028, 3, 10)
    logs = [FakeLog(today - timedelta(days=i), early_fullness=True) for i in range(30)]
    assert date(2028, 2, 29) in {log.log_date for log in logs}
    assert red_flag_symptom_days(logs, today) == 30


def test_insight_reports_symptom_day_count():
    insight = build_insight(symptom_days(4), TODAY)
    assert (insight["symptom_days"], insight["window_days"], insight["threshold_days"]) == (4, 30, 12)


def test_urinary_urgency_alone_does_not_count():
    # Only pain, bloating and early fullness are in the index.
    logs = [FakeLog(TODAY - timedelta(days=i)) for i in range(15)]
    assert red_flag_symptom_days(logs, TODAY) == 0


def test_period_start_dates_groups_consecutive_flow_days():
    logs = [FakeLog(date(2026, 9, d), period_flow="medium") for d in (1, 2, 3)] + \
           [FakeLog(date(2026, 9, d), period_flow="light") for d in (29, 30)]
    assert period_start_dates(logs) == [date(2026, 9, 1), date(2026, 9, 29)]


def test_average_cycle_length_needs_two_periods():
    assert average_cycle_length([FakeLog(date(2026, 9, 1), period_flow="heavy")]) is None


def test_average_cycle_length():
    logs = [FakeLog(date(2026, 8, 1), period_flow="heavy"),
            FakeLog(date(2026, 8, 29), period_flow="heavy"),
            FakeLog(date(2026, 9, 28), period_flow="heavy")]
    assert average_cycle_length(logs) == 29.0


def test_insight_always_carries_disclaimer():
    assert "not a medical device" in build_insight([], TODAY)["disclaimer"]
