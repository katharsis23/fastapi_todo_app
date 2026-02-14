from app.models.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.schemas.user import UserLogin, UserSignup
from app.utils.password_manager import hash_password, verify_password
from uuid import UUID


async def find_user_by_id(user_id: UUID, db: AsyncSession) -> User | None:
    try:
        return await db.scalar(select(User).where(User.user_id == user_id))
    except Exception as error:
        logger.error(f"Error during user finding by id: {error}")
        return None


async def create_user(user: UserSignup, db: AsyncSession) -> User | None:
    try:
        # Check if email is registered
        existing_email_user = await db.scalar(
            select(User).where(User.email == user.email)
        )

        # Check if username is taken by anyone
        username_taken = await db.scalar(
            select(User).where(User.username == user.username)
        )

        if existing_email_user:
            if existing_email_user.is_verified:
                logger.warning(
                    f"User with email {user.email} already exists and is verified"
                )
                return None

            # If reactivating, we need to ensure the NEW username isn't taken by someone ELSE
            if username_taken and username_taken.user_id != existing_email_user.user_id:
                logger.warning(
                    f"Username {user.username} is already taken by another user"
                )
                return None

            # Reactivate unverified account
            logger.info(f"Reactivating unverified account for {user.email}")
            existing_email_user.username = user.username
            existing_email_user.password = hash_password(user.password)
            await db.commit()
            await db.refresh(existing_email_user)
            return existing_email_user

        # New user case
        if username_taken:
            logger.warning(f"Username {user.username} is already taken")
            return None

        hashed_pw = hash_password(user.password)
        user_to_add = User(
            username=user.username,
            password=hashed_pw,
            email=user.email
        )

        db.add(user_to_add)
        await db.commit()
        await db.refresh(user_to_add)
        return user_to_add

    except Exception as error:
        await db.rollback()
        logger.error(f"Cannot insert user into db: {error}")
        raise error


async def authenticate_user(user: UserLogin, db: AsyncSession) -> User | None:
    try:
        existing_user = await db.scalar(select(User).where(User.email == user.email))
        if existing_user and verify_password(user.password, existing_user.password):
            return existing_user
        return None
    except Exception as error:
        logger.error(f"Error during login: {error}")
        return None


async def add_avatar(user_id: UUID, avatar_url: str, db: AsyncSession) -> User | None:
    try:
        user = await find_user_by_id(user_id=user_id, db=db)
        if user:
            user.avatar_url = avatar_url
            await db.commit()
            await db.refresh(user)
            return user
        return None
    except Exception as error:
        await db.rollback()
        logger.error(f"Cannot insert avatar into db: {error}")
        raise error


async def delete_avatar_database(user_id: UUID, db: AsyncSession) -> User | None:
    try:
        user = await find_user_by_id(user_id=user_id, db=db)
        if user:
            user.avatar_url = None
            await db.commit()
            await db.refresh(user)
            return user
        return None
    except Exception as error:
        await db.rollback()
        logger.error(f"Cannot delete avatar from db: {error}")
        raise error


async def get_avatar(user_id: UUID, db: AsyncSession) -> str | None:
    try:
        user = await find_user_by_id(user_id=user_id, db=db)
        if user:
            return user.avatar_url
        return None
    except Exception as error:
        logger.error(f"Error during avatar retrieval: {error}")
        raise error


async def verify_user(email: str, db: AsyncSession) -> User | None:
    try:
        user = await db.scalar(select(User).where(User.email == email))
        if user:
            user.is_verified = True
            await db.commit()
            await db.refresh(user)
            return user
        return None
    except Exception as error:
        await db.rollback()
        logger.error(f"Error verifying user: {error}")
        raise error
