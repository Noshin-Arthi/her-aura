"""API tests: registration and login."""
import pytest


def test_register_logs_user_in(client, new_user_payload):
    response = client.post("/api/auth/register", json=new_user_payload)
    assert response.status_code == 201
    assert response.json()["email"] == new_user_payload["email"]
    assert "password" not in response.text  # never leak secrets
    assert client.get("/api/me").status_code == 200


def test_duplicate_email_is_rejected_case_insensitively(client, new_user_payload):
    client.post("/api/auth/register", json=new_user_payload)
    duplicate = {**new_user_payload, "email": new_user_payload["email"].upper()}
    assert client.post("/api/auth/register", json=duplicate).status_code == 409


@pytest.mark.parametrize("field, value", [
    ("email", "not-an-email"),
    ("password", "short"),
    ("full_name", "A"),
])
def test_register_validation(client, new_user_payload, field, value):
    assert client.post("/api/auth/register", json={**new_user_payload, field: value}).status_code == 422


def test_login_wrong_password(client, new_user_payload):
    client.post("/api/auth/register", json=new_user_payload)
    client.post("/api/auth/logout")
    response = client.post("/api/auth/login", json={**new_user_payload, "password": "WrongPass1"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"  # same message for both cases


def test_protected_endpoint_requires_login(client):
    assert client.get("/api/logs").status_code == 401


def test_health_check_is_not_shadowed_by_a_page(client):
    # Regression: /health was also the "Log health" page, so the health check never ran (303 redirect).
    response = client.get("/healthz")
    assert response.status_code == 200 and response.json() == {"status": "ok"}
