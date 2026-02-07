import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime


@pytest.fixture
def auth_token(client):
    from unittest.mock import patch, AsyncMock
    from uuid import uuid4

    mock_user = AsyncMock()
    mock_user.user_id = uuid4()
    mock_user.email = "test@example.com"
    mock_user.is_verified = True  # CRITICAL: User must be verified
    mock_user.password = "hashed_pw"

    # Patch authenticate_user used by the login endpoint
    with patch("app.database.user.authenticate_user", return_value=mock_user):
        response = client.post("/user/login", json={
            "email": "test@example.com",
            "password": "12345"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]


class TestTaskViews:

    def test_post_task_success(self, client, auth_token):
        from unittest.mock import patch
        payload = {
            "title": "Test Task",
            "description": "Test description"
            # appointed_at omitted to avoid timezone issues
        }

        # First patch create_task with AsyncMock
        with patch("app.database.task.create_task", new_callable=AsyncMock) as mock_create:
            from uuid import uuid4
            mock_task_id = uuid4()
            mock_create.return_value = mock_task_id

            response = client.post(
                "/task/",
                json=payload,
                headers={"Authorization": f"Bearer {auth_token}"}
            )

            assert response.status_code == 201
            data = response.json()
            assert data["message"] == "Task created successfully"
            assert "task_id" in data

    def test_patch_task_success(self, client, auth_token):
        from unittest.mock import patch, AsyncMock
        from uuid import uuid4

        # First get a real task from the database
        with patch("app.database.task.get_user_tasks", new_callable=AsyncMock) as mock_get_tasks, \
             patch("app.database.task.count_user_tasks", new_callable=AsyncMock) as mock_count:

            # Mock to return a list with a real task structure
            mock_task = MagicMock()
            mock_task.task_id = uuid4()
            mock_task.title = "Test Task"
            mock_task.description = "Test Description"
            mock_task.description = "Test Description"
            mock_task.appointed_at = None
            mock_task.created_at = datetime.now()
            mock_task.user_fk = "1f7df84c-1789-4e3b-8d76-7945c9172a82"

            mock_get_tasks.return_value = [mock_task]
            mock_count.return_value = 1

            # Get the task
            response = client.get(
                "/task/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200

            tasks = response.json()["tasks"]
            if tasks:
                task_id = tasks[0]["task_id"]

                # Now patch the task - only mock update, not get
                with patch("app.database.task.update_task_by_id", new_callable=AsyncMock) as mock_update, \
                     patch("app.database.task.get_task_by_id", new_callable=AsyncMock) as mock_get_task:    # noqa: F841

                    # Mock the update to return the updated task
                    mock_updated_task = MagicMock()     # Use MagicMock for attributes, it's not awaited once returned
                    mock_updated_task.task_id = task_id
                    mock_updated_task.title = "Updated title"
                    mock_updated_task.description = "Updated description"
                    mock_updated_task.appointed_at = None

                    mock_update.return_value = mock_updated_task

                    response = client.patch(
                        f"/task/{task_id}",
                        json={"title": "Updated title"},
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )

                    assert response.status_code == 200

    def test_patch_task_not_found(self, client, auth_token):
        task_id = str(uuid4())
        with patch(
            "app.database.task.get_task_by_id",
            new_callable=AsyncMock,
            return_value=None
        ):
            response = client.patch(
                f"/task/{task_id}",
                json={"title": "whatever"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 400
        assert response.json()["message"] == "Task not found or update failed"

    def test_delete_task_success(self, client, auth_token):
        """
        Test that deletion of a task with a valid id and a valid token returns a 200 status code and a "Task deleted successfully" message.

        :param client: The FastAPI test client
        :type client: TestClient
        :param auth_token: A valid authentication token
        :type auth_token: str
        """
        from unittest.mock import patch, AsyncMock
        from uuid import uuid4

        # First create a task to get a real task_id
        with patch("app.database.task.get_user_tasks", new_callable=AsyncMock) as mock_get_tasks, \
             patch("app.database.task.count_user_tasks", new_callable=AsyncMock) as mock_count:

            # Mock to return a list with a real task structure
            mock_task = MagicMock()
            mock_task.task_id = uuid4()
            mock_task.title = "Test Task to Delete"
            mock_task.description = "Test Description"
            mock_task.description = "Test Description"
            mock_task.appointed_at = None
            mock_task.created_at = datetime.now()
            mock_task.user_fk = "1f7df84c-1789-4e3b-8d76-7945c9172a82"
            mock_get_tasks.return_value = [mock_task]
            mock_count.return_value = 1

            # Get the task
            response = client.get(
                "/task/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200

            tasks = response.json()["tasks"]
            if tasks:
                task_id = tasks[0]["task_id"]

                # Now delete the task
                with patch("app.database.task.remove_task", new_callable=AsyncMock) as mock_remove:
                    mock_remove.return_value = True

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
        with patch("app.database.task.remove_task", new_callable=AsyncMock, return_value=False):
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
            "app.database.task.remove_task",
            new_callable=AsyncMock,
            side_effect=Exception("DB Error")
        ):
            response = client.delete(
                f"/task/{task_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 500
        assert response.json()["message"] == "Internal server error"

    def test_get_all_tasks(self, client, auth_token):
        """
        Test that getting all tasks returns a 200 status code and a list of
        tasks with pagination metadata.
        :param client: The FastAPI test client
        :type client: TestClient
        :param auth_token: A valid authentication token
        :type auth_token: str
        """
        with patch("app.database.task.get_user_tasks", new_callable=AsyncMock, return_value=[]), \
                patch("app.database.task.count_user_tasks", new_callable=AsyncMock, return_value=0):
            response = client.get(
                "/task/",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "pagination" in data
        assert data["tasks"] is not None
        assert data["pagination"]["total_pages"] is not None
        assert data["pagination"]["current_page"] is not None
        assert data["pagination"]["page_size"] == 10
        assert data["pagination"]["has_next"] is not None
        assert data["pagination"]["has_prev"] is not None
