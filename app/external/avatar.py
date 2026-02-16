from app.s3_client import s3_client
from uuid import UUID
from fastapi import HTTPException
from loguru import logger


async def post_avatar(user_id: UUID, file: bytes, extension: str = "jpg") -> str:
    try:
        # Construct filename with extension for better browser compatibility
        filename = f"{user_id}.{extension}"
        await s3_client.upload_file(
            file=file,
            bucket_name="avatars",
            object_name=filename,
            content_type=f"image/{extension}"
        )
        # Return path including bucket name for consistency
        return f"avatars/{filename}"
    except Exception as e:
        logger.error(f"Failed to upload avatar for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def delete_avatar(user_id: UUID, extension: str = "jpg") -> None:
    try:
        filename = f"{user_id}.{extension}"
        await s3_client.delete_file(
            bucket_name="avatars",
            object_name=filename
        )
    except Exception as e:
        logger.error(f"Failed to delete avatar for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
