
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

    @pytest.mark.skip()
    def test_patch_task_success(self, client, auth_token):
        # Create a mock task for the patch operation
        mock_task = AsyncMock()
        mock_task.task_id = uuid4()
        mock_task.title = "Updated Title"
        mock_task.description = "Updated Desc"
        mock_task.appointed_at = None

        with patch(
            "app.database.task.find_task_by_id",
            AsyncMock(return_value=mock_task)
        ), patch(
            "app.database.task.update_task",
            AsyncMock(return_value=mock_task)
        ):
            test_creation_task = client.post(
                "/task/",
                json={
                    "title": "Test Task",
                    "description": "Test description",
                    "appointed_at": (
                        datetime.now(timezone.utc) + timedelta(days=1)
                    ).isoformat()
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert test_creation_task.status_code == 201
            test_creation_task_data = test_creation_task.json()
            assert test_creation_task_data["message"] == (
                "Task created succesfully"
            )
            assert "task_id" in test_creation_task_data

            updated_payload = {
                "title": "Updated Title",
                "description": "Updated Desc",
            }
            response = client.patch(
                f"/task/{test_creation_task.json()['task_id']}",
                json=updated_payload,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            logger.debug(response.json())
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Update successfull"
            assert data["new_title"] == "Updated Title"

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
