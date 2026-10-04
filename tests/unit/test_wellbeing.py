"""Mindfulness programme rules and sleep summary."""
from dataclasses import dataclass
from datetime import date, timedelta

import pytest

from app.services.wellbeing import PROGRAM, PROGRAM_DAYS, can_complete, next_program_day, sleep_summary


def test_program_is_seven_ordered_days():
    assert [p["day"] for p in PROGRAM] == list(range(1, 8)) and PROGRAM_DAYS == 7
    assert all(p["steps"] and p["minutes"] > 0 for p in PROGRAM)


@pytest.mark.parametrize("done, expected", [(set(), 1), ({1, 2}, 3), ({1, 3}, 2), (set(range(1, 8)), None)])
def test_next_program_day(done, expected):
    assert next_program_day(done) == expected


@pytest.mark.parametrize("day, done, allowed", [
    (1, set(), True), (2, set(), False), (2, {1}, True), (2, {1, 2}, False), (0, set(), False), (8, set(range(1, 8)), False),
])
def test_days_unlock_in_order(day, done, allowed):
    assert can_complete(day, done) is allowed


@dataclass
class Night:
    log_date: date
    hours: float
    quality: int


def test_sleep_summary_last_seven_nights_only():
    today = date(2026, 10, 10)
    nights = [Night(today, 6, 2), Night(today - timedelta(days=6), 8, 4), Night(today - timedelta(days=7), 2, 1)]
    assert sleep_summary(nights, today) == {"nights": 2, "avg_hours": 7.0, "avg_quality": 3.0}


def test_sleep_summary_empty():
    assert sleep_summary([], date(2026, 10, 10)) == {"nights": 0, "avg_hours": None, "avg_quality": None}
