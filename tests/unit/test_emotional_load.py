"""Emotional-load insight rules."""
from dataclasses import dataclass
from datetime import date, timedelta

import pytest

from app.services.emotional_load import SUPPORT_LINE, insights, parse_areas

TODAY = date(2026, 10, 20)


@dataclass
class CheckIn:
    log_date: date
    mood: int = 3
    stress: int = 4
    energy: int = 3
    areas: str = ""


def days(n, **kw):
    return [CheckIn(TODAY - timedelta(days=i), **kw) for i in range(n)]


def test_parse_areas_drops_unknown_keys():
    assert parse_areas("work,unknown,household,") == ["work", "household"]


def test_empty_history():
    result = insights([], TODAY)
    assert result["checkins"] == 0 and result["suggestions"] == [] and result["support_line"] == SUPPORT_LINE


def test_averages_and_previous_window():
    recent = days(2, mood=4, stress=6, energy=2)
    older = [CheckIn(TODAY - timedelta(days=20), stress=2)]
    result = insights(recent + older, TODAY)
    assert (result["avg_mood"], result["avg_stress"], result["avg_energy"]) == (4.0, 6.0, 2.0)
    assert result["prev_avg_stress"] == 2.0


@pytest.mark.parametrize("n, flagged", [(9, False), (10, True)])
def test_low_mood_on_most_days_suggests_professional_support(n, flagged):
    result = insights(days(n, mood=2) + [CheckIn(TODAY - timedelta(days=n), mood=4)], TODAY)
    assert any(s["kind"] == "professional" for s in result["suggestions"]) is flagged


@pytest.mark.parametrize("stress, flagged", [(6, False), (7, True)])
def test_high_stress_threshold(stress, flagged):
    result = insights(days(5, stress=stress), TODAY)
    assert any(s["kind"] == "stress" for s in result["suggestions"]) is flagged


def test_professional_suggestion_comes_first():
    result = insights(days(12, mood=1, stress=9, areas="work"), TODAY)
    assert [s["kind"] for s in result["suggestions"]][:2] == ["professional", "stress"]


def test_top_areas_and_handoff_tips():
    logs = days(5, areas="household,work") + [CheckIn(TODAY - timedelta(days=6), areas="household")]
    result = insights(logs, TODAY)
    assert [a["key"] for a in result["top_areas"]][:2] == ["household", "work"]
    assert result["top_areas"][0]["days"] == 6
    tips = [s["text"] for s in result["suggestions"] if s["kind"] == "handoff"]
    assert tips[0].startswith("Household running:") and "planning" in tips[0]


def test_cycle_phase_comparison_needs_enough_data():
    pre = {TODAY - timedelta(days=i) for i in range(3)}
    logs = [CheckIn(TODAY - timedelta(days=i), stress=8) for i in range(3)] + \
           [CheckIn(TODAY - timedelta(days=i), stress=4) for i in range(3, 6)]
    phase = insights(logs, TODAY, pre)["phase"]
    assert phase == {"pre_period_stress": 8.0, "other_stress": 4.0, "difference": 4.0}
    assert insights(logs[:5], TODAY, pre)["phase"] is None   # only 2 "other" days
