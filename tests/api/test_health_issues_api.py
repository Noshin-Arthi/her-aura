"""API tests: general health issues and doctor suggestions."""
from datetime import date, timedelta

import pytest


def log(client, category, severity, days_ago=0, notes=""):
    day = (date.today() - timedelta(days=days_ago)).isoformat()
    return client.post("/api/health-issues", json={"log_date": day, "category": category, "severity": severity, "notes": notes})


def test_log_and_list_issue(logged_in_client):
    response = log(logged_in_client, "headache", 6, notes="after work")
    assert response.status_code == 201
    assert response.json()["label"] == "Headache"
    issues = logged_in_client.get("/api/health-issues").json()
    assert [(i["category"], i["severity"], i["notes"]) for i in issues] == [("headache", 6, "after work")]


def test_several_issues_same_day_are_allowed(logged_in_client):
    assert log(logged_in_client, "headache", 4).status_code == 201
    assert log(logged_in_client, "toothache", 5).status_code == 201


def test_filter_by_category(logged_in_client):
    log(logged_in_client, "headache", 4)
    log(logged_in_client, "skin_rash", 3)
    issues = logged_in_client.get("/api/health-issues", params={"category": "skin_rash"}).json()
    assert [i["category"] for i in issues] == ["skin_rash"]


@pytest.mark.parametrize("category, severity", [("unknown", 5), ("headache", 0), ("headache", 11)])
def test_invalid_issue_rejected(logged_in_client, category, severity):
    assert log(logged_in_client, category, severity).status_code == 422


def test_future_issue_rejected(logged_in_client):
    assert log(logged_in_client, "fever", 5, days_ago=-1).status_code == 422


def test_suggestion_for_severe_toothache_points_to_dentist(logged_in_client):
    log(logged_in_client, "toothache", 9)
    body = logged_in_client.get("/api/suggestions").json()
    assert body["suggestions"][0]["specialty"] == "Dentistry"
    assert body["suggestions"][0]["urgency"] == "soon"
    assert "999" in body["emergency_note"]
    assert "not a diagnosis" in body["disclaimer"]


def test_suggested_specialty_has_doctors(logged_in_client):
    """Every specialty the rules can suggest must have at least one doctor to book."""
    categories = logged_in_client.get("/api/health-issues/categories").json()
    for c in categories:
        doctors = logged_in_client.get("/api/doctors", params={"specialty": c["specialty"]}).json()
        assert doctors, f"No doctor for {c['specialty']}"


def test_issues_are_private(client, new_user_payload):
    client.post("/api/auth/register", json=new_user_payload)
    log(client, "low_mood", 6, notes="private")
    client.post("/api/auth/logout")
    client.post("/api/auth/register", json={**new_user_payload, "email": "someone.else@example.com"})
    assert client.get("/api/health-issues").json() == []
    assert client.get("/api/suggestions").json()["suggestions"] == []
