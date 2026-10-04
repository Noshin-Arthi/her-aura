"""Emotional load: daily check-ins about mood, stress, energy and the invisible work you carry.

"Mental load" research (Daminger) describes cognitive labour as four steps: anticipating needs,
researching options, deciding, and monitoring, and finds women in different-gender couples do most of it.
So we track WHERE the load comes from, not only how you feel, and suggest handing off the planning,
not just the tasks. Rules are explainable and tested. Never a diagnosis.
"""
from collections import Counter
from datetime import date, timedelta

AREAS: dict[str, str] = {
    "work": "Work or study",
    "household": "Household running",
    "caregiving": "Caring for children or elders",
    "relationships": "Relationships",
    "health": "My own health",
    "money": "Money",
    "other": "Something else",
}

WINDOW = 14
HIGH_STRESS = 7            # stress 7-10 counts as a high-stress day
HIGH_STRESS_DAYS = 5       # 5+ such days in 14 -> suggest support + mindfulness
LOW_MOOD = 2               # mood 1-2 counts as a low day
LOW_MOOD_DAYS = 10         # most days for two weeks -> suggest professional support
MIN_PER_GROUP = 3          # check-ins needed in each group before comparing cycle phases

SUPPORT_LINE = ("If you're thinking about harming yourself, call 999 now. In Bangladesh, Kaan Pete Roi offers free, "
                "confidential emotional support: 09612-119911 (3pm-3am daily). Elsewhere: findahelpline.com.")

HANDOFF_TIPS = {
    "household": "Hand off a whole job, including the remembering and planning (for example 'you own the groceries'), not just single tasks.",
    "caregiving": "Share the planning: who tracks appointments, school forms and medicines? Write it down and split it.",
    "work": "List what only you can do this week. Postpone, delegate or drop one thing that isn't on that list.",
    "money": "Pick one money task and give it a fixed weekly 20-minute slot, so it stops following you around.",
    "relationships": "Name one thing you need and ask for it directly. People can't share a load they can't see.",
    "health": "Book one health task you've been postponing. Done is lighter than pending.",
    "other": "Write down everything on your mind for 5 minutes. A list outside your head weighs less.",
}


def parse_areas(raw: str) -> list[str]:
    return [a for a in (raw or "").split(",") if a in AREAS]


def _window(checkins, today: date, start_days_ago: int, length: int):
    end = today - timedelta(days=start_days_ago)
    start = end - timedelta(days=length - 1)
    return [c for c in checkins if start <= c.log_date <= end]


def _avg(values) -> float | None:
    values = list(values)
    return round(sum(values) / len(values), 1) if values else None


def insights(checkins, today: date, late_luteal_days: set[date] | None = None) -> dict:
    """Summary of the last 14 days, comparison with the 14 before, top load areas and suggestions.

    `late_luteal_days`: dates estimated to be in the pre-period week, to compare stress by cycle phase.
    """
    recent = _window(checkins, today, 0, WINDOW)
    previous = _window(checkins, today, WINDOW, WINDOW)

    area_counts = Counter(a for c in recent for a in parse_areas(c.areas))
    top_areas = [{"key": k, "label": AREAS[k], "days": n} for k, n in area_counts.most_common(3)]
    high_stress_days = sum(1 for c in recent if c.stress >= HIGH_STRESS)
    low_mood_days = sum(1 for c in recent if c.mood <= LOW_MOOD)

    suggestions: list[dict] = []
    if low_mood_days >= LOW_MOOD_DAYS:
        suggestions.append({"kind": "professional", "level": "important",
                            "text": f"Your mood was low on {low_mood_days} of the last {WINDOW} days. Talking to a doctor or counsellor can really help.",
                            "link": "/doctors?specialty=Psychiatry", "link_text": "Find a psychiatrist"})
    if high_stress_days >= HIGH_STRESS_DAYS:
        suggestions.append({"kind": "stress", "level": "notice",
                            "text": f"High stress on {high_stress_days} of the last {WINDOW} days. Short daily breathing practice can take the edge off.",
                            "link": "/mind", "link_text": "Open the mindfulness programme"})
    for area in top_areas[:2]:
        suggestions.append({"kind": "handoff", "level": "tip", "text": f"{area['label']}: {HANDOFF_TIPS[area['key']]}",
                            "link": None, "link_text": None})

    phase = None
    if late_luteal_days:
        pre = [c.stress for c in recent + previous if c.log_date in late_luteal_days]
        rest = [c.stress for c in recent + previous if c.log_date not in late_luteal_days]
        if len(pre) >= MIN_PER_GROUP and len(rest) >= MIN_PER_GROUP:
            diff = round(_avg(pre) - _avg(rest), 1)
            phase = {"pre_period_stress": _avg(pre), "other_stress": _avg(rest), "difference": diff}

    return {
        "checkins": len(recent),
        "avg_mood": _avg(c.mood for c in recent),
        "avg_stress": _avg(c.stress for c in recent),
        "avg_energy": _avg(c.energy for c in recent),
        "prev_avg_stress": _avg(c.stress for c in previous),
        "high_stress_days": high_stress_days,
        "low_mood_days": low_mood_days,
        "top_areas": top_areas,
        "phase": phase,
        "suggestions": suggestions,
        "support_line": SUPPORT_LINE,
    }
