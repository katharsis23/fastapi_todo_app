from app.core.celery_app import celery_app
from app.utils.smtp_client import _send_code_verification
import random
import os
from loguru import logger
import asyncio
from app.redis_client import redis_session


async def start_verification(email: str) -> None:
    code = str(random.randint(1000, 9999))
    async with redis_session() as session:
        await session.set(f"verification:{email}", code, ex=300)
    send_code.delay(email, code)


@celery_app.task(name="send_verification_code")
def send_code(email: str, code: str):
    # Variable set in Dockerfile flag.
    # If DEVELOPMENT MODE there is no sense in sending email
    # Variable set in Dockerfile flag.
    # If DEVELOPMENT_MODE is true there is no sense in sending email
    dev_mode_env = os.getenv("DEVELOPMENT_MODE", "true").lower()
    if dev_mode_env == "true":
        logger.info(f"Development mode activated, email sending skip: {email} with code: {code}")
        return
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            _send_code_verification(email=email, code=code)
        )
        return {
            "status": "sent",
            "to": email,
            "code": code
        }
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return {"status": "error", "message": str(e)}
