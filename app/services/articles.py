"""Learn: curated women's health reading from trusted public-health sources, plus monetization rules.

We write our own short summaries and link to the original article. We never copy third-party text.
Rules (tested):
- Safety topics (warning signs, screening) are ALWAYS free, whatever the user's plan.
- Premium articles unlock with a subscription, or one at a time by watching a short ad (max per day).
- Ads are contextual only: no health data ever goes to an ad network. See docs/RESEARCH.md (FTC v. Flo Health).
"""
import os
from datetime import datetime, timedelta

TOPICS = ["Ovarian health", "Breast health", "Hormones & cycle", "Nutrition", "Fitness", "Mind & motivation", "Life stages"]

ARTICLES: list[dict] = [
    # ---- Featured: always free (10) ----
    {"slug": "ovarian-cysts", "topic": "Ovarian health", "tier": "free", "safety": False, "minutes": 5, "source": "NHS",
     "title": "Ovarian cysts: what's normal and when to get checked",
     "summary": "Most ovarian cysts are harmless and go away on their own. Learn which symptoms, like sudden severe pelvic pain, need urgent care.",
     "url": "https://www.nhs.uk/conditions/ovarian-cyst/"},
    {"slug": "ovarian-cancer-symptoms", "topic": "Ovarian health", "tier": "free", "safety": True, "minutes": 6, "source": "NHS",
     "title": "Ovarian cancer: symptoms you shouldn't ignore",
     "summary": "Persistent bloating, feeling full quickly and pelvic pain are easy to dismiss. Here's when they're worth a doctor's visit.",
     "url": "https://www.nhs.uk/conditions/ovarian-cancer/"},
    {"slug": "breast-cancer-facts", "topic": "Breast health", "tier": "free", "safety": True, "minutes": 6, "source": "WHO",
     "title": "Breast cancer: the global facts and why early detection matters",
     "summary": "Breast cancer is the most common cancer in women worldwide. Early diagnosis and treatment greatly improve survival.",
     "url": "https://www.who.int/news-room/fact-sheets/detail/breast-cancer"},
    {"slug": "breast-checks", "topic": "Breast health", "tier": "free", "safety": True, "minutes": 5, "source": "NHS",
     "title": "Knowing your breasts: changes to look out for",
     "summary": "Lumps, skin changes, nipple changes or discharge: what to look for, and why most changes aren't cancer but should still be checked.",
     "url": "https://www.nhs.uk/conditions/breast-cancer-in-women/"},
    {"slug": "pcos", "topic": "Hormones & cycle", "tier": "free", "safety": False, "minutes": 6, "source": "NHS",
     "title": "PCOS explained: irregular periods, symptoms and treatment",
     "summary": "Polycystic ovary syndrome is common and very manageable. Understand the signs, the tests and what helps.",
     "url": "https://www.nhs.uk/conditions/polycystic-ovary-syndrome-pcos/"},
    {"slug": "pms", "topic": "Hormones & cycle", "tier": "free", "safety": False, "minutes": 5, "source": "ACOG",
     "title": "PMS: why it happens and what actually helps",
     "summary": "From exercise and sleep to treatment options, a gynecologists' guide to easing premenstrual symptoms.",
     "url": "https://www.acog.org/womens-health/faqs/premenstrual-syndrome"},
    {"slug": "healthy-diet", "topic": "Nutrition", "tier": "free", "safety": False, "minutes": 5, "source": "WHO",
     "title": "What a healthy diet really looks like",
     "summary": "Simple, evidence-based basics: fruit and vegetables, less salt, sugar and processed fat, and why they matter at every age.",
     "url": "https://www.who.int/news-room/fact-sheets/detail/healthy-diet"},
    {"slug": "physical-activity", "topic": "Fitness", "tier": "free", "safety": False, "minutes": 4, "source": "WHO",
     "title": "How much movement do you need? Less than you think to start",
     "summary": "The weekly activity targets for adults, and the good news: every bit of movement counts towards them.",
     "url": "https://www.who.int/news-room/fact-sheets/detail/physical-activity"},
    {"slug": "mindfulness-basics", "topic": "Mind & motivation", "tier": "free", "safety": False, "minutes": 4, "source": "NHS",
     "title": "Mindfulness: paying attention to the present moment",
     "summary": "What mindfulness is, how it can help with stress, and easy ways to practise it in everyday life.",
     "url": "https://www.nhs.uk/mental-health/self-help/tips-and-support/mindfulness/"},
    {"slug": "five-steps-wellbeing", "topic": "Mind & motivation", "tier": "free", "safety": False, "minutes": 4, "source": "NHS",
     "title": "Five small steps to feel better, starting today",
     "summary": "Connect, move, learn, give, notice: five practical, motivating habits linked to better mental wellbeing.",
     "url": "https://www.nhs.uk/mental-health/self-help/guides-tools-and-activities/five-steps-to-mental-wellbeing/"},
    # ---- Library: premium (subscribe, or watch an ad to unlock one for 24 hours) ----
    {"slug": "endometriosis", "topic": "Hormones & cycle", "tier": "premium", "safety": False, "minutes": 6, "source": "WHO",
     "title": "Endometriosis: the painful condition that takes years to diagnose",
     "summary": "Why endometriosis is often missed, its symptoms beyond period pain, and current treatment options.",
     "url": "https://www.who.int/news-room/fact-sheets/detail/endometriosis"},
    {"slug": "cervical-cancer", "topic": "Life stages", "tier": "premium", "safety": False, "minutes": 6, "source": "WHO",
     "title": "Cervical cancer: prevention through HPV vaccination and screening",
     "summary": "One of the most preventable cancers: how vaccination and regular screening work together.",
     "url": "https://www.who.int/news-room/fact-sheets/detail/cervical-cancer"},
    {"slug": "menopause", "topic": "Life stages", "tier": "premium", "safety": False, "minutes": 5, "source": "WHO",
     "title": "Menopause: what changes and how to feel your best",
     "summary": "Symptoms, timing and long-term health in the years around menopause.",
     "url": "https://www.who.int/news-room/fact-sheets/detail/menopause"},
    {"slug": "anaemia", "topic": "Nutrition", "tier": "premium", "safety": False, "minutes": 5, "source": "WHO",
     "title": "Anaemia: why so many women are low on iron",
     "summary": "Tiredness, weakness and hair fall can have a common, treatable cause. Who is most at risk and why.",
     "url": "https://www.who.int/news-room/fact-sheets/detail/anaemia"},
    {"slug": "stress", "topic": "Mind & motivation", "tier": "premium", "safety": False, "minutes": 5, "source": "NHS",
     "title": "Stress: spotting the signs and taking back control",
     "summary": "How stress shows up in body and mind, and practical steps to manage it.",
     "url": "https://www.nhs.uk/every-mind-matters/mental-health-issues/stress/"},
    {"slug": "depression", "topic": "Mind & motivation", "tier": "premium", "safety": False, "minutes": 6, "source": "WHO",
     "title": "Depression: more common than you think, and treatable",
     "summary": "Signs to look out for in yourself and others, and the effective treatments available.",
     "url": "https://www.who.int/news-room/fact-sheets/detail/depression"},
]
BY_SLUG = {a["slug"]: a for a in ARTICLES}

AD_UNLOCK_HOURS = 24
MAX_AD_UNLOCKS_PER_DAY = 3


def ad_seconds() -> int:
    """How long an ad must play before it can be claimed (env-configurable so tests run fast)."""
    return int(os.getenv("AD_SECONDS", "15"))


def featured() -> list[dict]:
    return [a for a in ARTICLES if a["tier"] == "free"]


def is_unlocked(article: dict, plan: str, unlocked_slugs: set[str]) -> bool:
    if article["tier"] == "free" or article["safety"]:
        return True
    return plan == "premium" or article["slug"] in unlocked_slugs


def ad_claim_error(started_at: datetime | None, now: datetime, claimed_today: int) -> str | None:
    """Why an ad can't be claimed yet, or None if it can."""
    if started_at is None:
        return "Start the ad first."
    if claimed_today >= MAX_AD_UNLOCKS_PER_DAY:
        return f"You've used today's {MAX_AD_UNLOCKS_PER_DAY} ad unlocks. Come back tomorrow, or go Premium."
    if (now - started_at).total_seconds() < ad_seconds():
        return "Please watch the ad to the end."
    return None


def unlock_until(now: datetime) -> datetime:
    return now + timedelta(hours=AD_UNLOCK_HOURS)
