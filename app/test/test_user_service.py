import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
import uuid


@pytest_asyncio.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://127.0.0.1:8000") as client:
        yield client


RANDOM_SUFFIX = uuid.uuid4().hex[:6]
TEST_USER = f"test_{RANDOM_SUFFIX}"
TEST_PASS = "password123"


@pytest.mark.asyncio
async def test_auth_flow(ac: AsyncClient):
    signup_data = {"username": TEST_USER, "password": TEST_PASS}
    signup_res = await ac.post("/user/signup", json=signup_data)

    assert signup_res.status_code == 201
    assert "id" in signup_res.json()

    login_data = {"username": TEST_USER, "password": TEST_PASS}
    login_res = await ac.post("/user/login", json=login_data)

    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
