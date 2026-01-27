import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers import user, task

TEST_USER_ID = str(uuid.UUID("82f291fb-8bda-47b4-8056-03942705b3fa"))


@pytest.fixture
def db_session():
    return AsyncMock()


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router=user.user_router)
    app.include_router(router=task.tasks_router)
    return app


@pytest.fixture
def client(db_session):
    app = _make_app()

    from app.database.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app=app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides = {}


@pytest.fixture
def authed_client(db_session):
    app = _make_app()

    from app.database.database import get_db
    from app.utils.oauth2Schema import get_current_user_id

    async def override_get_db():
        yield db_session

    async def override_user_id():
        return TEST_USER_ID

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_user_id

    with TestClient(app=app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides = {}
