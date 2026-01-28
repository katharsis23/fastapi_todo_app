# test_user_service.py
import pytest
from fastapi.testclient import TestClient

from unittest.mock import AsyncMock
from app.main import app
import uuid


@pytest.fixture
def client():
    def override_get_db():
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = True
        return mock_session

    with TestClient(
        app=app,
        raise_server_exceptions=True,
    ) as ac:
        yield ac


RANDOM_SUFFIX = uuid.uuid4().hex[:6]
TEST_USER = f"test_{RANDOM_SUFFIX}"
TEST_EMAIL = f"test_{RANDOM_SUFFIX}@example.com"
TEST_PASS = "password123"


def test_auth_flow(client):
    signup_data = {
        "username": TEST_USER,
        "email": TEST_EMAIL,
        "password": TEST_PASS
    }
    signup_res = client.post("/user/signup", json=signup_data)

    assert signup_res.status_code == 201
    assert "access_token" in signup_res.json()

    login_data = {"email": TEST_EMAIL, "password": TEST_PASS}
    login_res = client.post("/user/login", json=login_data)

    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
    app.dependency_overrides = {}


def test_signup_auth(client):
    signup_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "12345"
    }
    signup_response = client.post("/user/signup", json=signup_data)
    assert signup_response.status_code == 400
    app.dependency_overrides = {}


def test_login_with_invalid_email(client):
    login_data = {
        "email": "invalid-email",
        "password": "password123"
    }
    response = client.post("/user/login", json=login_data)
    assert response.status_code == 422  # Email validation error
    app.dependency_overrides = {}


def test_signup_with_invalid_email(client):
    signup_data = {
        "username": "test_user",
        "email": "invalid-email",
        "password": "password123"
    }
    response = client.post("/user/signup", json=signup_data)
    assert response.status_code == 422  # Email validation error
    app.dependency_overrides = {}


def test_login_with_empty_email(client):
    login_data = {
        "email": "",
        "password": "password123"
    }
    response = client.post("/user/login", json=login_data)
    assert response.status_code == 422  # Validation error
    app.dependency_overrides = {}
