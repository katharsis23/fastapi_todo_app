# test_user_service.py
import pytest
from unittest.mock import AsyncMock, patch
import uuid


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

    # Mock all the database calls and worker calls
    # We want create_user to succeed, send_code to succeed
    # And then login to succeed (after we mock it verified)

    from uuid import uuid4
    mock_user_id = uuid4()

    mock_user = AsyncMock()
    mock_user.user_id = mock_user_id
    mock_user.email = TEST_EMAIL
    mock_user.is_verified = False  # Initially not verified

    mock_verified_user = AsyncMock()
    mock_verified_user.user_id = mock_user_id
    mock_verified_user.email = TEST_EMAIL
    mock_verified_user.is_verified = True

    with patch("app.database.user.create_user", new_callable=AsyncMock, return_value=mock_user), \
         patch("app.routers.user.start_verification", new_callable=AsyncMock), \
         patch("app.database.user.authenticate_user", new_callable=AsyncMock, return_value=mock_verified_user):

        signup_res = client.post("/user/signup", json=signup_data)

        assert signup_res.status_code == 201, f"Signup failed: {signup_res.text}"
        assert "access_token" not in signup_res.json()
        assert "User created" in signup_res.json()["message"]

        login_data = {"email": TEST_EMAIL, "password": TEST_PASS}
        login_res = client.post("/user/login", json=login_data)

        # We return a verified user in authentication mock, so it should succeed
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        assert "access_token" in login_res.json()


@pytest.mark.skip
def test_verification_flow(client):
    # Mock Redis
    from unittest.mock import patch

    signup_data = {
        "username": "verify_test",
        "email": "verify@example.com",
        "password": "password123"
    }

    mock_user = AsyncMock()
    mock_user.user_id = uuid.uuid4()
    mock_user.email = "verify@example.com"
    mock_user.is_verified = False

    with patch("app.database.user.create_user", new_callable=AsyncMock, return_value=mock_user), \
         patch("app.routers.user.start_verification", new_callable=AsyncMock) as mock_verify:   # noqa: F841
        response = client.post("/user/signup", json=signup_data)
        assert response.status_code == 201, f"Signup failed: {response.text}"

    # 2. Verify with correct code
    mock_verified_user = AsyncMock()
    mock_verified_user.user_id = mock_user.user_id
    mock_verified_user.email = "verify@example.com"
    mock_verified_user.is_verified = True

    with patch("app.routers.user.redis_session") as mock_redis, \
         patch("app.database.user.verify_user", new_callable=AsyncMock, return_value=mock_verified_user):

        mock_session = AsyncMock()
        mock_redis.return_value.__aenter__.return_value = mock_session
        mock_redis.return_value.__aexit__.return_value = None

        # Setup mock return
        mock_session.get.return_value = b"1234"

        verify_data = {"email": "verify@example.com", "code": "1234"}
        response = client.post("/user/verify", json=verify_data)

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["message"] == "User verified successfully"


def test_signup_auth(client):
    signup_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "12345"
    }
    signup_response = client.post("/user/signup", json=signup_data)
    assert signup_response.status_code == 400


def test_login_with_invalid_email(client):
    login_data = {
        "email": "invalid-email",
        "password": "password123"
    }
    response = client.post("/user/login", json=login_data)
    assert response.status_code == 422  # Email validation error


def test_signup_with_invalid_email(client):
    signup_data = {
        "username": "test_user",
        "email": "invalid-email",
        "password": "password123"
    }
    response = client.post("/user/signup", json=signup_data)
    assert response.status_code == 422  # Email validation error


def test_login_with_empty_email(client):
    login_data = {
        "email": "",
        "password": "password123"
    }
    response = client.post("/user/login", json=login_data)
    assert response.status_code == 422  # Validation error
