"""Cycle phase and basal body temperature (BBT) rules. Pure functions, unit tested.

Ovulation CONFIRMATION uses the "3 over 6" rule (Marshall, 1968): three consecutive daily readings
higher than the six readings before them, the third at least 0.2 °C above the highest of those six.
Progesterone raises BBT after ovulation, so this confirms ovulation AFTER it happened.

It cannot predict safe days. Her Aura is not a contraceptive; using an app as birth control requires
regulatory clearance (e.g. FDA De Novo Class II, CE marking) and clinical studies. See docs/ROADMAP.md.
"""
from datetime import date, timedelta

from app.services.health_insights import average_cycle_length, period_start_dates

LOW_WINDOW = 6
HIGH_RUN = 3
MIN_RISE_C = 0.2
LATE_LUTEAL_DAYS = 7

NOT_CONTRACEPTION = ("Temperature tracking confirms ovulation only after it has happened. "
                     "Her Aura is not a contraceptive: do not use it to prevent pregnancy.")


def confirm_ovulation(readings: list[tuple[date, float]]) -> date | None:
    """Return the date of the first higher reading of the first thermal shift, or None.

    Needs 9 consecutive calendar days (6 low + 3 high). A missing day breaks the sequence,
    because a gap could hide a fever or a missed reading.
    """
    series = sorted(readings)
    for i in range(LOW_WINDOW, len(series) - HIGH_RUN + 1):
        window = series[i - LOW_WINDOW:i + HIGH_RUN]
        days = [d for d, _ in window]
        if any((b - a).days != 1 for a, b in zip(days, days[1:])):
            continue
        cover = max(t for _, t in window[:LOW_WINDOW])
        highs = [t for _, t in window[LOW_WINDOW:]]
        if all(t > cover for t in highs) and highs[-1] >= round(cover + MIN_RISE_C, 2):
            return window[LOW_WINDOW][0]
    return None


def estimated_next_period(period_starts: list[date], average_cycle: float | None) -> date | None:
    if not period_starts or not average_cycle:
        return None
    return max(period_starts) + timedelta(days=round(average_cycle))


def is_late_luteal(next_period: date | None, today: date) -> bool:
    """The last week before the expected period, when many people report poorer sleep and mood."""
    if next_period is None:
        return False
    return 0 < (next_period - today).days <= LATE_LUTEAL_DAYS


def cycle_status(logs, today: date) -> dict:
    """Everything the UI shows about the cycle, from the user's symptom logs."""
    starts = period_start_dates(logs)
    average = average_cycle_length(logs)
    next_period = estimated_next_period(starts, average)
    current_start = max(starts) if starts else None
    readings = [(l.log_date, l.bbt_celsius) for l in logs
                if getattr(l, "bbt_celsius", None) is not None and (current_start is None or l.log_date >= current_start)]
    return {
        "last_period_start": current_start,
        "average_cycle_length": average,
        "next_period": next_period,
        "late_luteal": is_late_luteal(next_period, today),
        "bbt_readings": len(readings),
        "ovulation_confirmed_from": confirm_ovulation(readings),
        "not_contraception": NOT_CONTRACEPTION,
    }


def pre_period_days(period_starts: list[date], next_period: date | None = None) -> set[date]:
    """All dates in the 7 days before each known (and the next expected) period start."""
    starts = list(period_starts) + ([next_period] if next_period else [])
    return {s - timedelta(days=i) for s in starts for i in range(1, LATE_LUTEAL_DAYS + 1)}
