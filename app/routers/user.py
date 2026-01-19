from fastapi.responses import JSONResponse
from fastapi import status, Depends, APIRouter
from fastapi.exceptions import HTTPException
from fastapi_utils.cbv import cbv
from app.schemas.user import UserLogin, UserSignup
from app.database.user import create_user, authenticate_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.utils.jwt_manager import create_access_token, verify_access_token

router_user_service = APIRouter(prefix="/user", tags=["User"])


@cbv(router_user_service)
class UserViews:
    db: AsyncSession = Depends(get_db)

    @router_user_service.post("/login", summary="Login")
    async def login(self, user_data: UserLogin) -> JSONResponse:
        user = await authenticate_user(db=self.db, user=user_data)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token(user_id=user.user_id)
        return JSONResponse({"access_token": token, "token_type": "bearer"})

    @router_user_service.post("/signup", summary="Create user")
    async def signup(self, user_data: UserSignup) -> JSONResponse:
        new_user = await create_user(db=self.db, user=user_data)
        return JSONResponse(
            {
                "message": "User created",
                "id": str(new_user.user_id)
            },
            status_code=201
        )
