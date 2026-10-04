"""API tests: articles, plans, rewarded ads, emotional load."""
from datetime import date, timedelta

import pytest

from app.services.articles import MAX_AD_UNLOCKS_PER_DAY

PREMIUM = "endometriosis"


def test_free_user_sees_all_articles_but_no_premium_urls(logged_in_client):
    items = logged_in_client.get("/api/articles").json()
    assert len(items) == 16
    for a in items:
        assert a["unlocked"] is (a["tier"] == "free")
        assert (a["url"] is None) is (not a["unlocked"])   # locked URLs are never sent


def test_locked_article_returns_402(logged_in_client):
    assert logged_in_client.get(f"/api/articles/{PREMIUM}").status_code == 402
    assert logged_in_client.get("/api/articles/no-such-article").status_code == 404


def test_premium_demo_unlocks_everything_and_can_be_cancelled(logged_in_client):
    assert logged_in_client.post("/api/plan/premium").json() == {"plan": "premium"}
    assert all(a["unlocked"] for a in logged_in_client.get("/api/articles").json())
    logged_in_client.post("/api/plan/free")
    assert logged_in_client.get(f"/api/articles/{PREMIUM}").status_code == 402
    assert logged_in_client.post("/api/plan/gold").status_code == 422


def test_claiming_an_ad_too_early_fails(logged_in_client, monkeypatch):
    monkeypatch.setenv("AD_SECONDS", "15")
    logged_in_client.post(f"/api/articles/{PREMIUM}/ad/start")
    response = logged_in_client.post(f"/api/articles/{PREMIUM}/ad/claim")
    assert response.status_code == 409 and "watch the ad" in response.json()["detail"]


def test_claim_without_start_fails(logged_in_client, monkeypatch):
    monkeypatch.setenv("AD_SECONDS", "0")
    assert logged_in_client.post(f"/api/articles/{PREMIUM}/ad/claim").json()["detail"] == "Start the ad first."


def test_watched_ad_unlocks_that_article_only(logged_in_client, monkeypatch):
    monkeypatch.setenv("AD_SECONDS", "0")
    logged_in_client.post(f"/api/articles/{PREMIUM}/ad/start")
    article = logged_in_client.post(f"/api/articles/{PREMIUM}/ad/claim").json()
    assert article["unlocked"] and article["url"].startswith("https://www.who.int/")
    assert logged_in_client.get("/api/articles/menopause").status_code == 402


def test_cannot_start_ad_for_free_or_already_unlocked_article(logged_in_client):
    assert logged_in_client.post("/api/articles/pcos/ad/start").status_code == 409


def test_daily_ad_limit(logged_in_client, monkeypatch):
    monkeypatch.setenv("AD_SECONDS", "0")
    slugs = ["endometriosis", "cervical-cancer", "menopause", "anaemia"]
    for slug in slugs[:MAX_AD_UNLOCKS_PER_DAY]:
        logged_in_client.post(f"/api/articles/{slug}/ad/start")
        assert logged_in_client.post(f"/api/articles/{slug}/ad/claim").status_code == 200
    extra = slugs[MAX_AD_UNLOCKS_PER_DAY]
    logged_in_client.post(f"/api/articles/{extra}/ad/start")
    assert "today's" in logged_in_client.post(f"/api/articles/{extra}/ad/claim").json()["detail"]


# ---------- Emotional load ----------
def checkin(client, days_ago=0, **kw):
    body = {"log_date": (date.today() - timedelta(days=days_ago)).isoformat(), "mood": 3, "stress": 5, "energy": 3, **kw}
    return client.post("/api/emotional", json=body)


def test_checkin_round_trip(logged_in_client):
    response = checkin(logged_in_client, areas=["household", "caregiving", "household"], handoff="school forms")
    assert response.status_code == 201
    assert response.json()["areas"] == ["household", "caregiving"]   # duplicates removed, order kept
    assert logged_in_client.get("/api/emotional").json()[0]["handoff"] == "school forms"


@pytest.mark.parametrize("field, value", [("mood", 0), ("mood", 6), ("stress", 11), ("energy", 0), ("areas", ["chores"])])
def test_checkin_validation(logged_in_client, field, value):
    assert checkin(logged_in_client, **{field: value}).status_code == 422


def test_one_checkin_per_day_and_no_future(logged_in_client):
    checkin(logged_in_client)
    assert checkin(logged_in_client).status_code == 409
    assert checkin(logged_in_client, days_ago=-1).status_code == 422


def test_insights_endpoint(logged_in_client):
    for i in range(5):
        checkin(logged_in_client, days_ago=i, stress=8, areas=["work"])
    body = logged_in_client.get("/api/emotional/insights").json()
    assert body["high_stress_days"] == 5
    assert {s["kind"] for s in body["suggestions"]} >= {"stress", "handoff"}
    assert "09612-119911" in body["support_line"]


def test_checkins_are_private(client, new_user_payload):
    client.post("/api/auth/register", json=new_user_payload)
    checkin(client, notes="very private")
    client.post("/api/auth/logout")
    client.post("/api/auth/register", json={**new_user_payload, "email": "third.person@example.com"})
    assert client.get("/api/emotional").json() == []
