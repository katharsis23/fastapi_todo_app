from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from config import POSTGRESQL_CONFIG
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

DECLARATIVE_BASE = declarative_base()

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
    try:
        async with async_session_factory() as connection:
            yield connection
            await connection.commit()
    except SQLAlchemyError as database_error:
        await connection.rollback()
        logger.error(f"Error with a Postgresql session: {database_error}")
        raise
    finally:
        await connection.close()
