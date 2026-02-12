from app.models.models import Avatar
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from uuid import UUID


async def add_avatar_v2(user_id: UUID, url: str, db: AsyncSession, metadata: dict = None) -> Avatar | None:
    """
    Adds a new avatar for the user.
    If an avatar already exists, it removes the old one (to maintain 1:1 relationship for now)
    and creates a new one.
    """

    try:
        # Check for existing avatar
        existing_avatar = await get_avatar_by_user_id_v2(user_id, db)
        if existing_avatar:
            await db.delete(existing_avatar)
            await db.flush()    # Ensure deletion is staged

        new_avatar = Avatar(
            user_fk=user_id,
            url=url,
            metadata_=metadata
        )
        db.add(new_avatar)
        await db.commit()
        await db.refresh(new_avatar)
        return new_avatar
    except Exception as error:
        await db.rollback()
        logger.error(f"Error adding avatar: {error}")
        raise error


async def get_avatar_by_user_id_v2(user_id: UUID, db: AsyncSession) -> Avatar | None:
    try:
        query = await db.execute(select(Avatar).where(Avatar.user_fk == user_id))
        avatar = query.scalar_one_or_none()
        return avatar
    except Exception as error:
        logger.error(f"Error retrieving avatar: {error}")
        return None


async def delete_avatar_v2(user_id: UUID, db: AsyncSession) -> bool:
    try:
        avatar = await get_avatar_by_user_id_v2(user_id, db)
        if avatar:
            await db.delete(avatar)
            await db.commit()
            return True
        return False
    except Exception as error:
        await db.rollback()
        logger.error(f"Error deleting avatar: {error}")
        raise error


async def get_avatar_url_by_user_id_v2(user_id: UUID, db: AsyncSession) -> str | None:
    try:
        avatar = await get_avatar_by_user_id_v2(user_id, db)
        if avatar:
            return avatar.url
        return None
    except Exception as error:
        logger.error(f"Error retrieving avatar url: {error}")
        return None
