from fastapi.responses import JSONResponse
from fastapi import status, Depends
from fastapi.exceptions import HTTPException
from schemas.user import UserLogin, UserSignup
from database.user import create_user, authenticate_user
from fastapi.routing import APIRouter
from fastapi_utils import cbv
from sqlalchemy import AsyncSession
from database import get_db

user_router = APIRouter(prefix="/user")


@cbv(user_router)
class UserViews:
    db = Depends(get_db)

    @user_router.post("/login", summary="Login")
    async def login(self, user: UserLogin) -> JSONResponse:
        pass

    @user_router.post("/signup", summary="Create user")
    async def signup(self, user: UserSignup) -> JSONResponse:
        pass
