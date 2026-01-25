from fastapi.responses import JSONResponse
from fastapi import status, Depends, APIRouter
from fastapi.exceptions import HTTPException
from fastapi_utils.cbv import cbv
from app.schemas.user import UserLogin, UserSignup
from app.database.user import create_user, authenticate_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.utils.jwt_manager import create_access_token

router_user_service = APIRouter(prefix="/user", tags=["User"])


@cbv(router_user_service)
class UserViews:
    db: AsyncSession = Depends(get_db)

    @router_user_service.post("/login", summary="Login")
    async def login(self, user_data: UserLogin) -> JSONResponse:
        user = await authenticate_user(db=self.db, user=user_data)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
        token = create_access_token(user_id=user.user_id)
        return JSONResponse(
            {
                "access_token": token,
                "token_type": "bearer"
            }
        )

    @router_user_service.post("/signup", summary="Create user")
    async def signup(self, user_data: UserSignup) -> JSONResponse:
        new_user = await create_user(db=self.db, user=user_data)
        if new_user:
            token = create_access_token(user_id=new_user.user_id)
            return JSONResponse(
                {
                    "message": "User created",
                    "access_token": token
                },
                status_code=status.HTTP_201_CREATED
            )
        return JSONResponse(
            {
                "message": "Signup failed, try to change the username"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
