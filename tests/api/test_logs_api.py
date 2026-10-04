"""API tests: daily symptom logs and insights."""
from datetime import date, timedelta

import pytest


def test_create_and_list_log(logged_in_client):
    payload = {"log_date": date.today().isoformat(), "period_flow": "light", "pain_level": 4, "bloating": True}
    assert logged_in_client.post("/api/logs", json=payload).status_code == 201
    logs = logged_in_client.get("/api/logs").json()
    assert len(logs) == 1 and logs[0]["pain_level"] == 4 and logs[0]["bloating"] is True


def test_one_log_per_day(logged_in_client):
    payload = {"log_date": date.today().isoformat()}
    logged_in_client.post("/api/logs", json=payload)
    assert logged_in_client.post("/api/logs", json=payload).status_code == 409


def test_future_date_rejected(logged_in_client):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    assert logged_in_client.post("/api/logs", json={"log_date": tomorrow}).status_code == 422


@pytest.mark.parametrize("pain", [-1, 11])
def test_pain_level_boundaries(logged_in_client, pain):
    payload = {"log_date": date.today().isoformat(), "pain_level": pain}
    assert logged_in_client.post("/api/logs", json=payload).status_code == 422


def test_insight_flags_12_symptom_days(logged_in_client):
    for i in range(12):
        day = (date.today() - timedelta(days=i)).isoformat()
        logged_in_client.post("/api/logs", json={"log_date": day, "pelvic_or_abdominal_pain": True})
    insight = logged_in_client.get("/api/insights").json()
    assert insight["red_flag"] is True
    assert "gynecologist" in insight["message"]


def test_copy_previous_day(logged_in_client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    logged_in_client.post("/api/logs", json={"log_date": yesterday, "period_flow": "heavy", "pain_level": 8,
                                             "bloating": True, "notes": "private note"})
    copied = logged_in_client.post("/api/logs/copy-previous")
    assert copied.status_code == 201
    body = copied.json()
    assert body["log_date"] == date.today().isoformat()
    assert (body["period_flow"], body["pain_level"], body["bloating"]) == ("heavy", 8, True)
    assert body["notes"] == ""  # notes are personal to the day, never copied


def test_copy_previous_day_without_yesterday_fails(logged_in_client):
    response = logged_in_client.post("/api/logs/copy-previous")
    assert response.status_code == 409
    assert "no log for the previous day" in response.json()["detail"]


def test_copy_previous_day_does_not_overwrite_today(logged_in_client):
    for days_ago in (1, 0):
        day = (date.today() - timedelta(days=days_ago)).isoformat()
        logged_in_client.post("/api/logs", json={"log_date": day})
    assert logged_in_client.post("/api/logs/copy-previous").status_code == 409


def test_users_cannot_see_each_others_logs(client, new_user_payload):
    client.post("/api/auth/register", json=new_user_payload)
    client.post("/api/logs", json={"log_date": date.today().isoformat(), "notes": "private"})
    client.post("/api/auth/logout")
    client.post("/api/auth/register", json={**new_user_payload, "email": "other@example.com"})
    assert client.get("/api/logs").json() == []
