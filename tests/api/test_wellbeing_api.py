"""API tests: BBT logging, cycle status, sleep and the mindfulness programme."""
from datetime import date, timedelta

import pytest


def day(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


# ---------- BBT / cycle status ----------
@pytest.mark.parametrize("bbt, status", [(34.9, 422), (35.0, 201), (38.5, 201), (38.6, 422)])
def test_bbt_range(logged_in_client, bbt, status):
    assert logged_in_client.post("/api/logs", json={"log_date": day(0), "bbt_celsius": bbt}).status_code == status


def test_cycle_status_confirms_shift_and_warns(logged_in_client):
    temps = [36.40, 36.35, 36.45, 36.38, 36.42, 36.40, 36.55, 36.60, 36.70]
    for i, t in enumerate(temps):  # oldest first, ending today
        logged_in_client.post("/api/logs", json={"log_date": day(len(temps) - 1 - i), "bbt_celsius": t})
    status = logged_in_client.get("/api/cycle/status").json()
    assert status["bbt_readings"] == 9
    assert status["ovulation_confirmed_from"] == day(2)
    assert "not a contraceptive" in status["not_contraception"]


def test_copy_previous_day_does_not_copy_temperature(logged_in_client):
    logged_in_client.post("/api/logs", json={"log_date": day(1), "bbt_celsius": 36.5, "period_flow": "light"})
    copied = logged_in_client.post("/api/logs/copy-previous").json()
    assert copied["period_flow"] == "light" and copied["bbt_celsius"] is None


# ---------- Sleep ----------
def test_log_and_list_sleep(logged_in_client):
    assert logged_in_client.post("/api/sleep", json={"log_date": day(0), "hours": 6.5, "quality": 2}).status_code == 201
    assert logged_in_client.get("/api/sleep").json()[0]["hours"] == 6.5


@pytest.mark.parametrize("hours, quality", [(-1, 3), (24.5, 3), (7, 0), (7, 6)])
def test_sleep_validation(logged_in_client, hours, quality):
    assert logged_in_client.post("/api/sleep", json={"log_date": day(0), "hours": hours, "quality": quality}).status_code == 422


def test_one_sleep_log_per_night(logged_in_client):
    logged_in_client.post("/api/sleep", json={"log_date": day(0), "hours": 7, "quality": 3})
    assert logged_in_client.post("/api/sleep", json={"log_date": day(0), "hours": 8, "quality": 4}).status_code == 409


def test_future_sleep_rejected(logged_in_client):
    assert logged_in_client.post("/api/sleep", json={"log_date": day(-1), "hours": 7, "quality": 3}).status_code == 422


# ---------- Mindfulness ----------
def test_program_days_unlock_in_order(logged_in_client):
    assert logged_in_client.get("/api/mindfulness/progress").json() == {"completed_days": [], "next_day": 1, "total_days": 7}
    assert logged_in_client.post("/api/mindfulness/2/complete").status_code == 409   # can't skip
    assert logged_in_client.post("/api/mindfulness/1/complete").json()["next_day"] == 2
    assert logged_in_client.post("/api/mindfulness/1/complete").status_code == 409   # can't repeat


def test_wellbeing_data_is_private(client, new_user_payload):
    client.post("/api/auth/register", json=new_user_payload)
    client.post("/api/sleep", json={"log_date": day(0), "hours": 5, "quality": 1})
    client.post("/api/mindfulness/1/complete")
    client.post("/api/auth/logout")
    client.post("/api/auth/register", json={**new_user_payload, "email": "another.person@example.com"})
    assert client.get("/api/sleep").json() == []
    assert client.get("/api/mindfulness/progress").json()["completed_days"] == []
