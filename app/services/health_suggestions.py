"""Rule-based "which doctor, and when?" suggestions from a user's health-issue history.

Deliberately simple and explainable: every suggestion says WHY it was made.
This is the baseline an AI feature must beat later (see docs/ROADMAP.md, Phase 3);
it is also what the AI falls back to when the model is unavailable.
Never a diagnosis.
"""
from collections import Counter
from datetime import date, timedelta

# key -> (label shown to users, first specialty to see, specialty if it keeps coming back)
CATEGORIES: dict[str, tuple[str, str, str]] = {
    "headache": ("Headache", "General Medicine", "Neurology"),
    "toothache": ("Toothache", "Dentistry", "Dentistry"),
    "skin_rash": ("Skin rash", "Dermatology", "Dermatology"),
    "hair_fall": ("Hair fall", "Dermatology", "Dermatology"),
    "fatigue": ("Tiredness / low energy", "General Medicine", "General Medicine"),
    "fever": ("Fever / cold", "General Medicine", "General Medicine"),
    "stomach": ("Stomach pain / digestion", "General Medicine", "Gastroenterology"),
    "joint_pain": ("Joint or back pain", "General Medicine", "Orthopedics"),
    "low_mood": ("Stress / low mood / poor sleep", "General Medicine", "Psychiatry"),
    "other": ("Other", "General Medicine", "General Medicine"),
}

TIPS: dict[str, list[str]] = {
    "headache": ["Drink enough water through the day", "Take regular breaks from screens", "Keep a regular sleep schedule"],
    "toothache": ["Avoid very hot, cold or sugary food until checked", "Brush twice a day and floss"],
    "skin_rash": ["Note any new soap, food or medicine before the rash", "Avoid scratching; keep the area clean and dry"],
    "hair_fall": ["Make sure meals include enough protein and iron-rich foods", "Avoid tight hairstyles and harsh heat styling"],
    "fatigue": ["Aim for 7-9 hours of sleep", "Eat regular meals; don't skip breakfast", "Add light daily activity such as a 20-minute walk"],
    "fever": ["Rest and drink plenty of fluids"],
    "stomach": ["Eat smaller, regular meals", "Note which foods make it worse"],
    "joint_pain": ["Check your sitting posture and take stretch breaks", "Avoid heavy lifting until checked"],
    "low_mood": ["Keep a regular sleep and wake time", "Talk to someone you trust", "Short daily walks outdoors can help"],
    "other": [],
}

SEVERE = 8                 # severity 8-10 in the last 3 days -> see a doctor soon
RECENT_SEVERE_DAYS = 3
RECURRING_WINDOW = 14
RECURRING_DAYS = 4         # same issue on 4+ days in 14 -> see the specialist
GENERAL_SYMPTOMS = {"fatigue", "hair_fall", "skin_rash", "fever"}
GENERAL_PATTERN_MIN = 3    # 3+ different general symptoms in 14 days -> general checkup

EMERGENCY_NOTE = ("If a symptom is sudden or severe (for example the worst headache of your life, chest pain, "
                  "trouble breathing or fainting), call 999 or go to the nearest emergency department now.")
DISCLAIMER = "Suggestions are based only on what you logged. They are not a diagnosis."


def label(category: str) -> str:
    return CATEGORIES.get(category, CATEGORIES["other"])[0]


def suggest(logs, today: date) -> list[dict]:
    """Return suggestions, most urgent first. `logs` need .category, .severity, .log_date."""
    window = [l for l in logs if today - timedelta(days=RECURRING_WINDOW - 1) <= l.log_date <= today]
    suggestions: list[dict] = []
    seen: set[str] = set()

    # 1. Severe and recent
    for log in sorted(window, key=lambda l: -l.severity):
        if log.severity >= SEVERE and (today - log.log_date).days < RECENT_SEVERE_DAYS and log.category not in seen:
            _, first, _ = CATEGORIES.get(log.category, CATEGORIES["other"])
            suggestions.append(_make(log.category, first, "soon",
                                     f"You rated {label(log.category).lower()} {log.severity}/10 on {log.log_date:%d %b}."))
            seen.add(log.category)

    # 2. Recurring
    days_per_category = Counter()
    for category, day in {(l.category, l.log_date) for l in window}:
        days_per_category[category] += 1
    for category, days in days_per_category.most_common():
        if days >= RECURRING_DAYS and category not in seen:
            _, _, recurring = CATEGORIES.get(category, CATEGORIES["other"])
            suggestions.append(_make(category, recurring, "routine",
                                     f"{label(category)} on {days} of the last {RECURRING_WINDOW} days."))
            seen.add(category)

    # 3. Several general symptoms together
    general = sorted({l.category for l in window} & GENERAL_SYMPTOMS)
    if len(general) >= GENERAL_PATTERN_MIN and "general_checkup" not in seen:
        names = ", ".join(label(c).lower() for c in general)
        suggestions.append({
            "category": "general_checkup", "label": "General checkup", "specialty": "General Medicine",
            "urgency": "routine", "reason": f"You logged several general symptoms in 2 weeks: {names}.",
            "tips": ["A basic checkup and blood test can rule out common causes such as low iron or vitamin levels",
                     "Review your sleep, stress and nutrition"],
        })
    return suggestions


def _make(category: str, specialty: str, urgency: str, reason: str) -> dict:
    return {"category": category, "label": label(category), "specialty": specialty,
            "urgency": urgency, "reason": reason, "tips": TIPS.get(category, [])}
