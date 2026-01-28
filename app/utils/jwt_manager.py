from jwt import encode, decode
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
from app.config.config import JWT_CONFIG
from loguru import logger

TIMEZONE = timezone.utc


def create_access_token(user_id: uuid, expires_date: Optional[datetime] = None) -> str:
    """
    Docstring for create_access_token
    :param user_id: Description
    :type user_id: uuid
    :param expires_date: Description
    :type expires_date: Optional[datetime]
    :return: Description
    :rtype: str
    Creates token with expiration time
    """
    if expires_date:
        expire = datetime.now(TIMEZONE) + expires_date
    else:
        expire = datetime.now(TIMEZONE) + timedelta(minutes=JWT_CONFIG.expiration_time)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(TIMEZONE)
    }
    token = encode(
        payload=payload,
        key=JWT_CONFIG.secret_key.get_secret_value(),
        algorithm=JWT_CONFIG.algorithm
    )
    return token


def verify_access_token(token: str) -> Optional[str]:
    """
    Docstring for verify_access_token
    :param token: Description
    :type token: str
    :return: Description
    :rtype: str | None

    Verifies the validity of the token
    """
    try:
        payload = decode(
            jwt=token,
            key=JWT_CONFIG.secret_key.get_secret_value(),
            algorithms=JWT_CONFIG.algorithm
        )
        user_id = payload.get("sub")
        if user_id:
            return user_id
        else:
            return None
    except Exception as error:
        logger.error(f"Error during token verification: {error}")
        return None
