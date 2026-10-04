"""Rule-based health insights. Pure functions, so they are easy to unit test.

The red-flag rule is adapted from the Goff Ovarian Cancer Symptom Index
(Goff et al., Cancer 2007): pelvic/abdominal pain, bloating or feeling full quickly
on 12 or more days in a month. It is a prompt to see a doctor, never a diagnosis.
"""
from datetime import date, timedelta

DISCLAIMER = (
    "Her Aura is not a medical device and does not diagnose any condition. "
    "If you are worried about a symptom, please see a doctor."
)
RED_FLAG_DAYS = 12
WINDOW_DAYS = 30


def red_flag_symptom_days(logs, today: date) -> int:
    """Count days in the last 30 with any Goff index symptom."""
    start = today - timedelta(days=WINDOW_DAYS - 1)
    return sum(
        1
        for log in logs
        if start <= log.log_date <= today
        and (log.pelvic_or_abdominal_pain or log.bloating or log.early_fullness)
    )


def period_start_dates(logs) -> list[date]:
    """A period starts on a day with flow when the previous day had no flow."""
    flow_days = sorted(log.log_date for log in logs if log.period_flow != "none")
    starts = []
    for day in flow_days:
        if not starts or (day - timedelta(days=1)) not in flow_days:
            starts.append(day)
    return starts


def average_cycle_length(logs) -> float | None:
    starts = period_start_dates(logs)
    if len(starts) < 2:
        return None
    gaps = [(b - a).days for a, b in zip(starts, starts[1:])]
    return round(sum(gaps) / len(gaps), 1)


def build_insight(logs, today: date) -> dict:
    days = red_flag_symptom_days(logs, today)
    red_flag = days >= RED_FLAG_DAYS
    if red_flag:
        message = (
            f"You logged pain, bloating or early fullness on {days} of the last {WINDOW_DAYS} days. "
            "Symptoms this frequent are worth discussing with a gynecologist soon."
        )
    elif not logs:
        message = "Start logging daily to see your trends."
    else:
        message = "No frequent warning symptoms in the last 30 days. Keep logging."
    return {
        "days_logged": len(logs),
        "symptom_days": days,
        "window_days": WINDOW_DAYS,
        "threshold_days": RED_FLAG_DAYS,
        "average_cycle_length": average_cycle_length(logs),
        "red_flag": red_flag,
        "message": message,
        "disclaimer": DISCLAIMER,
    }
