import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def image_file():
    return io.BytesIO(b"fake image bytes")


def test_get_avatar_no_avatar(authed_client):
    with patch(
        "app.routers.user.get_avatar",
        new=AsyncMock(return_value=None),
    ):
        response = authed_client.get("/user/avatar")

    assert response.status_code == 200
    data = response.json()
    assert "avatar_url" in data
    assert "default_avatar.jpeg" in data["avatar_url"]
    assert data["message"] == "Using default avatar"


def test_get_avatar_with_avatar(authed_client):
    with patch(
        "app.routers.user.get_avatar",
        new=AsyncMock(return_value="avatars/test-user-id"),
    ):
        response = authed_client.get("/user/avatar")

    assert response.status_code == 200
    data = response.json()
    assert "avatar_url" in data
    assert "avatars/test-user-id" in data["avatar_url"]


def test_upload_avatar_success(authed_client, image_file):
    with patch(
        "app.routers.user.post_avatar",
        new=AsyncMock(return_value="avatars/test-user-id"),
    ) as mock_post_avatar, patch(
        "app.routers.user.add_avatar",
        new=AsyncMock(return_value=MagicMock()),
    ) as mock_add_avatar:
        response = authed_client.post(
            "/user/avatar",
            files={"file": ("test.jpg", image_file, "image/jpeg")},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Avatar uploaded"
    assert "path" in data
    assert data["path"] == "avatars/test-user-id"
    mock_post_avatar.assert_awaited_once()
    mock_add_avatar.assert_awaited_once()


def test_upload_avatar_invalid_file_type(authed_client):
    invalid_file = io.BytesIO(b"This is not an image")

    response = authed_client.post(
        "/user/avatar",
        files={"file": ("test.txt", invalid_file, "text/plain")},
    )
    assert response.status_code == 400
    assert "Only images allowed" in response.json()["detail"]


def test_upload_avatar_user_not_found(authed_client, image_file):
    with patch(
        "app.routers.user.post_avatar",
        new=AsyncMock(return_value="avatars/test-user-id"),
    ), patch(
        "app.routers.user.add_avatar",
        new=AsyncMock(return_value=None),
    ):
        response = authed_client.post(
            "/user/avatar",
            files={"file": ("test.jpg", image_file, "image/jpeg")},
        )

    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_delete_avatar_success(authed_client):
    with patch(
        "app.routers.user.delete_avatar_database",
        new=AsyncMock(return_value=MagicMock()),
    ) as mock_delete_avatar_db, patch(
        "app.routers.user.delete_avatar",
        new=AsyncMock(return_value=None),
    ) as mock_delete_avatar:
        response = authed_client.delete("/user/avatar")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Avatar deleted successfully"
    mock_delete_avatar_db.assert_awaited_once()
    mock_delete_avatar.assert_awaited_once()


def test_delete_avatar_no_existing_avatar(authed_client):
    with patch(
        "app.routers.user.delete_avatar_database",
        new=AsyncMock(return_value=None),
    ) as mock_delete_avatar_db, patch(
        "app.routers.user.delete_avatar",
        new=AsyncMock(return_value=None),
    ) as mock_delete_avatar:
        response = authed_client.delete("/user/avatar")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Avatar deleted successfully"
    mock_delete_avatar_db.assert_awaited_once()
    mock_delete_avatar.assert_not_awaited()


def test_avatar_endpoints_no_authentication(client):
    response = client.get("/user/avatar")
    assert response.status_code == 401

    response = client.post(
        "/user/avatar",
        files={"file": ("test.jpg", b"fake image", "image/jpeg")},
    )
    assert response.status_code == 401

    response = client.delete("/user/avatar")
    assert response.status_code == 401


def test_avatar_endpoints_invalid_token(client):
    invalid_token = "invalid.token.here"

    response = client.get(
        "/user/avatar",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401

    response = client.post(
        "/user/avatar",
        headers={"Authorization": f"Bearer {invalid_token}"},
        files={"file": ("test.jpg", b"fake image", "image/jpeg")},
    )
    assert response.status_code == 401

    response = client.delete(
        "/user/avatar",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401


def test_upload_avatar_s3_error(authed_client, image_file):
    with patch(
        "app.routers.user.post_avatar",
        new=AsyncMock(side_effect=Exception("S3 connection failed")),
    ):
        response = authed_client.post(
            "/user/avatar",
            files={"file": ("test.jpg", image_file, "image/jpeg")},
        )

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


def test_delete_avatar_s3_error(authed_client):
    with patch(
        "app.routers.user.delete_avatar_database",
        new=AsyncMock(return_value=MagicMock()),
    ), patch(
        "app.routers.user.delete_avatar",
        new=AsyncMock(side_effect=Exception("S3 deletion failed")),
    ):
        response = authed_client.delete("/user/avatar")

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]
