"""Content and monetization rules for Learn."""
from datetime import datetime, timedelta

import pytest

from app.services import articles
from app.services.articles import ARTICLES, MAX_AD_UNLOCKS_PER_DAY, ad_claim_error, featured, is_unlocked

NOW = datetime(2026, 10, 10, 12, 0, 0)


def test_ten_featured_free_articles_covering_requested_topics():
    free = featured()
    assert len(free) == 10
    titles = " ".join(a["title"].lower() for a in free)
    for word in ("ovarian cyst", "breast", "diet", "movement", "mindfulness"):
        assert word in titles


def test_every_article_links_to_a_trusted_source_over_https():
    for a in ARTICLES:
        assert a["url"].startswith("https://"), a["slug"]
        assert a["source"] in {"WHO", "NHS", "ACOG"}, a["slug"]
        assert a["topic"] in articles.TOPICS, a["slug"]


def test_slugs_are_unique():
    assert len({a["slug"] for a in ARTICLES}) == len(ARTICLES)


def test_safety_articles_are_never_premium():
    # Warning signs and screening must never be behind a paywall.
    assert all(a["tier"] == "free" for a in ARTICLES if a["safety"])


@pytest.mark.parametrize("tier, safety, plan, unlocked, expected", [
    ("free", False, "free", set(), True),
    ("premium", False, "free", set(), False),
    ("premium", False, "free", {"x"}, True),
    ("premium", False, "premium", set(), True),
    ("premium", True, "free", set(), True),   # safety overrides tier, even if someone mislabels it
])
def test_is_unlocked(tier, safety, plan, unlocked, expected):
    assert is_unlocked({"slug": "x", "tier": tier, "safety": safety}, plan, unlocked) is expected


def test_ad_must_be_started(monkeypatch):
    assert ad_claim_error(None, NOW, 0) == "Start the ad first."


@pytest.mark.parametrize("watched, ok", [(14.9, False), (15, True)])
def test_ad_must_play_to_the_end(monkeypatch, watched, ok):
    monkeypatch.setenv("AD_SECONDS", "15")
    error = ad_claim_error(NOW - timedelta(seconds=watched), NOW, 0)
    assert (error is None) is ok


@pytest.mark.parametrize("claimed_today, ok", [(MAX_AD_UNLOCKS_PER_DAY - 1, True), (MAX_AD_UNLOCKS_PER_DAY, False)])
def test_daily_ad_limit(monkeypatch, claimed_today, ok):
    monkeypatch.setenv("AD_SECONDS", "0")
    assert (ad_claim_error(NOW, NOW, claimed_today) is None) is ok
