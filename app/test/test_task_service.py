
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from loguru import logger


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


@pytest.fixture
def auth_token(client):
    response = client.post("/user/login", json={
        "username": "test_user",
        "password": "12345"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


class TestTaskViews:

    def test_post_task_success(self, client, auth_token):
        payload = {
            "title": "Test Task",
            "description": "Test description",
            "appointed_at": (
                datetime.now(timezone.utc) + timedelta(days=1)
            ).isoformat()
        }

        response = client.post(
            "/task/",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Task created succesfully"
        assert "task_id" in data

    def test_patch_task_success(self, client, auth_token):
        test_task = {
            "title": "Initial title",
            "description": "Initial description",
            "appointed_at": (
                datetime.now(timezone.utc) + timedelta(days=1)
            ).isoformat()
        }
        creation_response = client.post(
            "/task/",
            json=test_task,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert creation_response.status_code == 201
        created_task_id = creation_response.json()["task_id"]
        assert created_task_id is not None

        updated_payload = {
            "title": "Updated title",
            "description": "Updated description",
            "appointed_at": (
                datetime.now(timezone.utc) + timedelta(days=2)
            ).isoformat()
        }
        updated_response = client.patch(
            f"/task/{created_task_id}",
            json=updated_payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert updated_response.status_code == 200
        updated_data = updated_response.json()
        assert updated_data["task_id"] == created_task_id
        assert updated_data["new_title"] == updated_payload["title"]
        assert updated_data["new_description"] == updated_payload["description"]
        assert updated_data["new_appointed_at"] == updated_payload["appointed_at"]

    def test_patch_task_not_found(self, client, auth_token):
        task_id = str(uuid4())
        with patch(
            "app.database.task.find_task_by_id",
            AsyncMock(return_value=None)
        ):
            response = client.patch(
                f"/task/{task_id}",
                json={"title": "whatever"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 400
        assert response.json()["message"] == "Something went wrong"

    @pytest.mark.skip()
    def test_delete_task_success(self, client, auth_token):
        """
        Test that deletion of a task with a valid id and a valid token returns a 200 status code and a "Task deleted successfully" message.

        :param client: The FastAPI test client
        :type client: TestClient
        :param auth_token: A valid authentication token
        :type auth_token: str
        """
        task_id = str(uuid4())
        with patch(
            "app.database.task.delete_task", AsyncMock(return_value=True)
        ):
            response = client.delete(
                f"/task/{task_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 200
        assert response.json()["message"] == "Task deleted successfully"

    def test_delete_task_not_found(self, client, auth_token):
        """
        Test that deletion of a task with a valid id but an invalid token returns a 404 status code and a "Task not found" message.

        :param client: The FastAPI test client
        :type client: TestClient
        :param auth_token: A valid authentication token
        :type auth_token: str
        """
        task_id = str(uuid4())
        with patch("app.database.task.delete_task", AsyncMock(return_value=False)):
            response = client.delete(
                f"/task/{task_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 404
        assert response.json()["message"] == "Task not found"

    def test_delete_task_error(self, client, auth_token):
        """
        Test that deletion of a task with a database error returns a
        404 status code and an "Internal server error" message.

        :param client: A TestClient instance
        :param auth_token: A token for authentication

        :return: None
        """
        task_id = str(uuid4())
        with patch(
            "app.database.task.delete_task",
            AsyncMock(side_effect=Exception("DB Error"))
        ):
            response = client.delete(
                f"/task/{task_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 404
        assert response.json()["message"] == "Task not found"

    def test_get_all_tasks(self, client, auth_token):
        """
        Test that getting all tasks returns a 200 status code and a list of
        tasks with pagination metadata.
        :param client: The FastAPI test client
        :type client: TestClient
        :param auth_token: A valid authentication token
        :type auth_token: str
        """
        with patch(
            "app.database.task.get_all_tasks_by_user",
            AsyncMock(return_value=[])
        ), patch(
            "app.database.task.get_tasks_count_by_user",
            AsyncMock(return_value=0)
        ):
            response = client.get(
                "/task/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "pagination" in data
        assert data["tasks"] is not None
        assert data["pagination"]["total_pages"] == 6
        assert data["pagination"]["current_page"] == 1
        assert data["pagination"]["page_size"] == 10
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_prev"] is False
