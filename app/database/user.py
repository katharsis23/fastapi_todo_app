from app.models.models import User
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.schemas.user import UserLogin, UserSchema
from app.utils.password_manager import hash_password, verify_password
import uuid


async def find_user_by_id(user_id: uuid, db: AsyncSession):
    try:
        query = await db.execute(select(User).where(User.user_id == user_id))
        return query.scalar_one_or_none()
    except Exception as error:
        logger.error(f"Error during user finding by id: {error}")
        return None


async def create_user(user: UserSchema, db: AsyncSession):
    try:
        query = await db.execute(select(User).where(User.username == user.username))
        existing_user = query.scalar_one_or_none()

        if existing_user:
            logger.warning(f"User {user.username} already exists")
            return None

        hashed_pw = hash_password(user.password)
        user_to_add = User(
            username=user.username,
            password=hashed_pw
        )

        db.add(user_to_add)
        await db.commit()
        await db.refresh(user_to_add)
        return user_to_add

    except Exception as error:
        await db.rollback()
        logger.error(f"Cannot insert user into db: {error}")
        raise error


async def authenticate_user(user: UserLogin, db: AsyncSession):
    try:
        query = await db.execute(select(User).where(User.username == user.username))
        existing_user = query.scalar_one_or_none()

        if existing_user and verify_password(user.password, existing_user.password):
            return existing_user
        return False
    except Exception as error:
        logger.error(f"Error during login: {error}")
        return False
