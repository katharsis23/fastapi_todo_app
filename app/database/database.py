from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.config import POSTGRESQL_CONFIG
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator   # noqa: TYP001
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

DeclarativeBase = declarative_base()

postgresql_engine = create_async_engine(
    url=POSTGRESQL_CONFIG.db_url,
    echo=True
)

async_session_factory = sessionmaker(
    bind=postgresql_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session = async_session_factory()
    try:
        async with session:
            yield session
    except SQLAlchemyError as database_error:
        await session.rollback()
        logger.error(f"Error with a Postgresql session: {database_error}")
        raise
    finally:
        await session.close()
