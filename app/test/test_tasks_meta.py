import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone


class TestTasksMeta:

    @pytest.mark.asyncio
    async def test_get_tasks_hash_empty(self, authed_client):
        """Test getting checksum when user has no tasks."""
        with patch("app.database.task.get_all_user_tasks", new_callable=AsyncMock) as mock_get_tasks:
            mock_get_tasks.return_value = []
            response = authed_client.get("/tasks/meta/")

            assert response.status_code == 200
            data = response.json()
            assert "checksum" in data
            # Empty list hash with separators=(',', ':') and sort_keys=True
            # json.dumps([], sort_keys=True, separators=(',', ':')) -> "[]"
            # hashlib.sha256(b"[]").hexdigest()
            assert data["checksum"] == "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"

    @pytest.mark.asyncio
    async def test_get_tasks_hash_success(self, authed_client):
        """Test getting checksum with tasks."""
        with patch("app.database.task.get_all_user_tasks", new_callable=AsyncMock) as mock_get_tasks:
            # Mock tasks
            task1 = MagicMock()
            task1.task_id = uuid4()
            task1.title = "Task 1"
            task1.description = "Desc 1"
            task1.created_at = datetime(2023, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
            task1.appointed_at = None

            task2 = MagicMock()
            task2.task_id = uuid4()
            task2.title = "Task 2"
            task2.description = "Desc 2"
            task2.created_at = datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
            task2.appointed_at = datetime(2023, 1, 3, 12, 0, 0, tzinfo=timezone.utc)

            mock_get_tasks.return_value = [task1, task2]

            response = authed_client.get("/tasks/meta/")

            assert response.status_code == 200
            data = response.json()
            assert "checksum" in data
            assert len(data["checksum"]) == 64  # SHA256 length

    @pytest.mark.asyncio
    async def test_get_tasks_hash_stability(self, authed_client):
        """Test that same tasks produce exactly the same hash regardless of microsecond noise."""
        with patch("app.database.task.get_all_user_tasks", new_callable=AsyncMock) as mock_get_tasks:
            task_id = uuid4()

            # Task with microseconds
            task1 = MagicMock()
            task1.task_id = task_id
            task1.title = "Stable Task"
            task1.description = "Stable Desc"
            task1.created_at = datetime(2023, 1, 1, 10, 0, 0, 999999, tzinfo=timezone.utc)
            task1.appointed_at = None

            mock_get_tasks.return_value = [task1]
            resp1 = authed_client.get("/tasks/meta/")
            hash1 = resp1.json()["checksum"]

            # Task without microseconds (but same second)
            task2 = MagicMock()
            task2.task_id = task_id
            task2.title = "Stable Task"
            task2.description = "Stable Desc"
            task2.created_at = datetime(2023, 1, 1, 10, 0, 0, 0, tzinfo=timezone.utc)
            task2.appointed_at = None

            mock_get_tasks.return_value = [task2]
            resp2 = authed_client.get("/tasks/meta/")
            hash2 = resp2.json()["checksum"]

            # Hashes should be identical because we strip microseconds
            assert hash1 == hash2

    @pytest.mark.asyncio
    async def test_get_tasks_hash_error(self, authed_client):
        """Test error handling in tasks meta endpoint."""
        with patch("app.database.task.get_all_user_tasks", new_callable=AsyncMock) as mock_get_tasks:
            mock_get_tasks.side_effect = Exception("Database is down")

            response = authed_client.get("/tasks/meta/")

            assert response.status_code == 500
            assert response.json()["message"] == "Internal server error"
