"""Mindfulness programme and sleep content, plus the small rules around them.

All text is original to Her Aura. Evidence notes (with sources) live in docs/RESEARCH.md.
"""
from datetime import date, timedelta

# A 7-day beginner programme: short, one skill per day, each builds on the last.
PROGRAM: list[dict] = [
    {"day": 1, "title": "Arriving: three slow breaths", "minutes": 3,
     "steps": ["Sit comfortably and let your shoulders drop.",
               "Breathe in through your nose for a count of 4, out for a count of 6.",
               "Do this three times, then breathe normally and notice how you feel."]},
    {"day": 2, "title": "Counting the breath", "minutes": 5,
     "steps": ["Breathe naturally. Count each out-breath from 1 to 10, then start again.",
               "When you lose count, that's normal. Notice it kindly and go back to 1."]},
    {"day": 3, "title": "Body scan, part 1", "minutes": 5,
     "steps": ["Close your eyes. Move your attention slowly from your feet up to your hips.",
               "Notice warmth, pressure or tension without trying to change it."]},
    {"day": 4, "title": "Body scan, part 2", "minutes": 7,
     "steps": ["Continue from your hips to the top of your head.",
               "Pause at your belly and lower back: places that often hold cycle-related tension."]},
    {"day": 5, "title": "Noticing thoughts", "minutes": 7,
     "steps": ["Breathe normally. When a thought appears, silently label it 'thinking'.",
               "Return to the breath. The skill is the returning, not an empty mind."]},
    {"day": 6, "title": "Being kind to difficult feelings", "minutes": 8,
     "steps": ["Recall a mildly stressful moment. Notice where you feel it in the body.",
               "Breathe into that place and say to yourself: 'This is hard, and it's okay to feel this.'"]},
    {"day": 7, "title": "Your own practice", "minutes": 10,
     "steps": ["Combine what you learned: 2 minutes breathing, 5 minutes body scan, 3 minutes open awareness.",
               "Choose a regular time for tomorrow. Short and daily beats long and rare."]},
]
PROGRAM_DAYS = len(PROGRAM)

WIND_DOWN: list[dict] = [
    {"title": "4-6 breathing", "minutes": 3,
     "text": "Lie down. Breathe in for 4, out for 6. A longer out-breath helps the body slow down."},
    {"title": "Progressive relaxation", "minutes": 8,
     "text": "Tense your feet for 5 seconds, then release. Move up through calves, thighs, hands, shoulders and face."},
    {"title": "Gentle routine", "minutes": 30,
     "text": "Dim the lights, put the phone away 30 minutes before bed, keep the room cool, and go to bed at a regular time."},
]

LATE_LUTEAL_SLEEP_TIP = ("You're probably in the last week before your period. Many people sleep less well in these days, "
                         "so try an earlier wind-down tonight.")
LATE_LUTEAL_MIND_TIP = ("The week before your period can bring more stress and low mood. "
                        "A short daily practice may help, and it's a good week to keep going.")


def next_program_day(completed_days: set[int]) -> int | None:
    """The lowest day not yet completed, or None when the programme is finished."""
    for item in PROGRAM:
        if item["day"] not in completed_days:
            return item["day"]
    return None


def can_complete(day: int, completed_days: set[int]) -> bool:
    """Days unlock in order: you can complete day N only after day N-1."""
    return 1 <= day <= PROGRAM_DAYS and day not in completed_days and (day == 1 or day - 1 in completed_days)


def sleep_summary(logs, today: date) -> dict:
    """Average hours and quality over the last 7 nights (only nights that were logged)."""
    recent = [l for l in logs if today - timedelta(days=6) <= l.log_date <= today]
    if not recent:
        return {"nights": 0, "avg_hours": None, "avg_quality": None}
    return {"nights": len(recent),
            "avg_hours": round(sum(l.hours for l in recent) / len(recent), 1),
            "avg_quality": round(sum(l.quality for l in recent) / len(recent), 1)}
