from app.s3_client import s3_client
from app.models.models import User
from app.database.database import AsyncSession
from uuid import UUID
from fastapi import HTTPException
from loguru import logger


async def post_avatar(user_id: UUID, file: bytes) -> str:
    try:
        filename = f"{user_id}"
        await s3_client.upload_file(
            file=file,
            bucket_name="avatars",
            object_name=filename
        )
        return filename
    except Exception as e:
        logger.error(f"Failed to upload avatar for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def delete_avatar(user_id: UUID) -> None:
    try:
        filename = f"{user_id}"
        await s3_client.delete_file(
            bucket_name="avatars",
            object_name=filename
        )
    except Exception as e:
        logger.error(f"Failed to delete avatar for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
