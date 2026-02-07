from redis import asyncio as aioredis
from app.config.config import REDIS_CONFIG
from contextlib import asynccontextmanager


redis_client = aioredis.from_url(
    REDIS_CONFIG.redis_url.get_secret_value(),
    decode_responses=True,
    health_check_interval=30,
    encoding='utf-8'
)


@asynccontextmanager
async def redis_session():
    try:
        yield redis_client
    except Exception as e:
        raise e
