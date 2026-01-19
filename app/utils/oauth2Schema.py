from fastapi.security.oauth2 import OAuth2PasswordBearer
from fastapi import Depends, status, HTTPException
from app.utils.jwt_manager import verify_access_token
import uuid

oauth2_schema = OAuth2PasswordBearer("/user/login")


async def get_current_user_id(token: str = Depends(oauth2_schema)) -> str:
    user_id = verify_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
