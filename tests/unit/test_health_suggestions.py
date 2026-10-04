"""Unit tests for the 'which doctor, and when?' rules."""
from dataclasses import dataclass
from datetime import date, timedelta

import pytest

from app.services.health_suggestions import CATEGORIES, suggest

TODAY = date(2026, 10, 15)


@dataclass
class Issue:
    category: str
    severity: int
    log_date: date


def days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def test_no_logs_no_suggestions():
    assert suggest([], TODAY) == []


@pytest.mark.parametrize("severity, expected", [(7, 0), (8, 1), (10, 1)])
def test_severity_threshold(severity, expected):
    result = suggest([Issue("toothache", severity, TODAY)], TODAY)
    assert len(result) == expected
    if expected:
        assert result[0]["urgency"] == "soon" and result[0]["specialty"] == "Dentistry"


@pytest.mark.parametrize("age, flagged", [(0, True), (2, True), (3, False)])
def test_severe_must_be_recent(age, flagged):
    result = suggest([Issue("skin_rash", 9, days_ago(age))], TODAY)
    assert bool(result) is flagged


@pytest.mark.parametrize("days, flagged", [(3, False), (4, True)])
def test_recurring_threshold(days, flagged):
    logs = [Issue("headache", 3, days_ago(i)) for i in range(days)]
    result = suggest(logs, TODAY)
    assert bool(result) is flagged
    if flagged:
        assert result[0]["specialty"] == "Neurology"   # recurring headache -> specialist, not GP
        assert result[0]["urgency"] == "routine"


def test_two_logs_same_day_count_as_one_day():
    logs = [Issue("headache", 3, TODAY)] * 2 + [Issue("headache", 3, days_ago(1)), Issue("headache", 3, days_ago(2))]
    assert suggest(logs, TODAY) == []   # 3 distinct days, not 4


def test_recurring_ignores_logs_older_than_14_days():
    logs = [Issue("headache", 3, days_ago(14 + i)) for i in range(5)]
    assert suggest(logs, TODAY) == []


def test_general_symptom_pattern_suggests_checkup():
    logs = [Issue("fatigue", 3, TODAY), Issue("hair_fall", 2, days_ago(3)), Issue("skin_rash", 2, days_ago(6))]
    result = suggest(logs, TODAY)
    assert [s["category"] for s in result] == ["general_checkup"]
    assert "tiredness" in result[0]["reason"]   # user-facing labels, not internal keys


def test_severe_comes_before_routine_and_no_duplicates():
    logs = [Issue("headache", 3, days_ago(i)) for i in range(5)] + [Issue("headache", 9, TODAY), Issue("toothache", 8, TODAY)]
    result = suggest(logs, TODAY)
    assert [s["urgency"] for s in result] == ["soon", "soon"]
    assert len({s["category"] for s in result}) == len(result)


def test_every_category_has_a_specialty():
    assert all(first and recurring for _, first, recurring in CATEGORIES.values())
