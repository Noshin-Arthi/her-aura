"""BBT ovulation confirmation (3-over-6 rule) and cycle phase. Safety-relevant, so boundaries are tested hard."""
from dataclasses import dataclass
from datetime import date, timedelta

import pytest

from app.services.cycle import NOT_CONTRACEPTION, confirm_ovulation, cycle_status, estimated_next_period, is_late_luteal

START = date(2026, 9, 1)
LOW = [36.40, 36.35, 36.45, 36.38, 36.42, 36.40]   # cover line = 36.45


def series(temps, start=START):
    return [(start + timedelta(days=i), t) for i, t in enumerate(temps)]


def test_classic_shift_is_confirmed():
    readings = series(LOW + [36.55, 36.60, 36.70])
    assert confirm_ovulation(readings) == START + timedelta(days=6)


@pytest.mark.parametrize("third, confirmed", [(36.64, False), (36.65, True)])
def test_third_high_must_be_point_two_above_cover(third, confirmed):
    readings = series(LOW + [36.50, 36.55, third])
    assert (confirm_ovulation(readings) is not None) is confirmed


def test_two_highs_are_not_enough():
    assert confirm_ovulation(series(LOW + [36.60, 36.70])) is None


def test_a_high_equal_to_cover_breaks_the_run():
    assert confirm_ovulation(series(LOW + [36.45, 36.60, 36.70])) is None


def test_missing_day_breaks_the_sequence():
    readings = series(LOW + [36.55, 36.60, 36.70])
    del readings[7]  # skip one morning
    assert confirm_ovulation(readings) is None


def test_first_shift_is_returned_even_if_later_data_exists():
    readings = series(LOW + [36.55, 36.60, 36.70, 36.70, 36.75])
    assert confirm_ovulation(readings) == START + timedelta(days=6)


def test_unsorted_input_is_handled():
    readings = series(LOW + [36.55, 36.60, 36.70])
    assert confirm_ovulation(list(reversed(readings))) == START + timedelta(days=6)


@pytest.mark.parametrize("days_until, expected", [(0, False), (1, True), (7, True), (8, False), (-2, False)])
def test_late_luteal_window(days_until, expected):
    today = date(2026, 10, 10)
    assert is_late_luteal(today + timedelta(days=days_until), today) is expected


def test_next_period_needs_history():
    assert estimated_next_period([], 28) is None
    assert estimated_next_period([date(2026, 9, 1)], None) is None
    assert estimated_next_period([date(2026, 8, 4), date(2026, 9, 1)], 28.4) == date(2026, 9, 29)


@dataclass
class Log:
    log_date: date
    period_flow: str = "none"
    bbt_celsius: float | None = None


def test_cycle_status_only_uses_current_cycle_temperatures():
    # A shift in the previous cycle must not count as this cycle's ovulation.
    old = [Log(d, bbt_celsius=t) for d, t in series(LOW + [36.55, 36.60, 36.70], start=date(2026, 8, 10))]
    periods = [Log(date(2026, 8, 1), "heavy"), Log(date(2026, 8, 29), "heavy")]
    status = cycle_status(old + periods, date(2026, 9, 5))
    assert status["last_period_start"] == date(2026, 8, 29)
    assert status["bbt_readings"] == 0
    assert status["ovulation_confirmed_from"] is None
    assert status["not_contraception"] == NOT_CONTRACEPTION
    assert "not a contraceptive" in NOT_CONTRACEPTION
