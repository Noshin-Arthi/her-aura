"""Public 'try it' endpoint used by the landing page demo."""
import pytest
from sqlalchemy import text


def preview(client, *issues):
    return client.post("/api/suggestions/preview", json={"issues": [
        {"category": c, "severity": s, "days": d} for c, s, d in issues]})


def test_works_without_login(client):
    response = preview(client, ("toothache", 9, 1))
    assert response.status_code == 200
    first = response.json()["suggestions"][0]
    assert (first["specialty"], first["urgency"]) == ("Dentistry", "soon")


def test_same_rules_as_real_app(client):
    # 4 of 14 days is the recurring threshold in app/services/health_suggestions.py
    assert preview(client, ("headache", 3, 3)).json()["suggestions"] == []
    assert preview(client, ("headache", 3, 4)).json()["suggestions"][0]["specialty"] == "Neurology"


def test_nothing_is_saved(client, db):
    preview(client, ("skin_rash", 9, 5))
    assert db.execute(text("SELECT COUNT(*) FROM health_issue_logs")).scalar_one() == 0


@pytest.mark.parametrize("issue", [("unknown", 5, 1), ("headache", 0, 1), ("headache", 11, 1),
                                   ("headache", 5, 0), ("headache", 5, 15)])
def test_invalid_input_rejected(client, issue):
    assert preview(client, issue).status_code == 422


def test_empty_and_oversized_requests_rejected(client):
    assert client.post("/api/suggestions/preview", json={"issues": []}).status_code == 422
    assert preview(client, *[("headache", 5, 1)] * 11).status_code == 422
