"""R-E-1: auth_service + login/me/logout + role-protected DELETE."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.auth_service import get_auth_service


@pytest.fixture(autouse=True)
def _reset_auth_state():
    get_auth_service().clear()
    yield
    get_auth_service().clear()


@pytest.fixture
def admin_password(monkeypatch):
    monkeypatch.setattr(settings, "admin_password", "s3cret")
    return "s3cret"


@pytest.fixture
def client():
    return TestClient(app)


def test_login_tester_default_credentials(client):
    response = client.post("/v1/auth/login", json={"id": "tester", "password": "tester"})
    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["role"] == "tester"
    assert body["profile"]["display_name"] == "테스트 검토자"
    assert body["token"]


def test_login_admin_requires_env_password(client, admin_password):
    response = client.post(
        "/v1/auth/login", json={"id": "admin", "password": admin_password}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["role"] == "admin"
    assert body["profile"]["display_name"] == "김준법 수석"


def test_login_admin_without_env_password_is_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_password", None)
    response = client.post(
        "/v1/auth/login", json={"id": "admin", "password": "anything"}
    )
    assert response.status_code == 401


def test_login_wrong_password(client):
    response = client.post("/v1/auth/login", json={"id": "tester", "password": "wrong"})
    assert response.status_code == 401


def test_me_returns_profile(client):
    token = _login(client, "tester", "tester")
    response = client.get(
        "/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "tester"


def test_me_without_token_is_401(client):
    response = client.get("/v1/auth/me")
    assert response.status_code == 401


def test_logout_invalidates_token(client):
    token = _login(client, "tester", "tester")
    client.post("/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    response = client.get(
        "/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


# --- DELETE protection -----------------------------------------------------


def test_delete_content_requires_auth(client):
    response = client.delete("/v1/compliance/contents/c-doesnt-exist")
    assert response.status_code == 401


def test_delete_content_rejects_tester(client):
    token = _login(client, "tester", "tester")
    response = client.delete(
        "/v1/compliance/contents/c-doesnt-exist",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_delete_content_allows_admin(client, admin_password):
    token = _login(client, "admin", admin_password)
    # 404 is fine — the auth gate passed; the row simply doesn't exist.
    response = client.delete(
        "/v1/compliance/contents/c-doesnt-exist",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (204, 404)


def test_delete_content_honours_legacy_admin_token(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_token", "legacy-token")
    response = client.delete(
        "/v1/compliance/contents/c-doesnt-exist",
        headers={"x-admin-token": "legacy-token"},
    )
    assert response.status_code in (204, 404)


def _login(client: TestClient, user_id: str, password: str) -> str:
    response = client.post(
        "/v1/auth/login", json={"id": user_id, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["token"]
