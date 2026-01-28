from fastapi.responses import JSONResponse
from fastapi import status, Depends, APIRouter, HTTPException
from fastapi_utils.cbv import cbv
from app.schemas.user import UserLogin, UserSignup
from app.database.user import (
    create_user,
    authenticate_user,
    add_avatar,
    delete_avatar_database,
    get_avatar
)
from app.database.database import get_db, AsyncSession
from app.utils.jwt_manager import create_access_token
from app.external.avatar import post_avatar, delete_avatar
from app.utils.oauth2Schema import get_current_user_id
from loguru import logger
from fastapi import File, UploadFile
from uuid import UUID

user_router = APIRouter(prefix="/user", tags=["User"])


@cbv(user_router)
class UserViews:
    db: AsyncSession = Depends(get_db)

    @user_router.post("/login", summary="Login")
    async def login_endpoint(self, user_data: UserLogin) -> JSONResponse:
        logger.info(f"Login attempt for user: {user_data.email}")
        try:
            user = await authenticate_user(db=self.db, user=user_data)
            if not user:
                logger.warning(f"Login failed for user: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid credentials"
                )
            token = create_access_token(user_id=user.user_id)
            logger.info(f"User {user_data.email} logged in successfully")
            return JSONResponse(
                {
                    "access_token": token,
                    "token_type": "bearer",
                    "user_id": str(user.user_id)
                }
            )
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Unexpected error during login: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    @user_router.post("/signup", summary="Create user")
    async def signup_endpoint(self, user_data: UserSignup) -> JSONResponse:
        logger.info(f"Signup attempt for user: {user_data.email}")
        try:
            new_user = await create_user(db=self.db, user=user_data)
            if new_user:
                token = create_access_token(user_id=new_user.user_id)
                logger.info(f"User {user_data.email} created successfully")
                return JSONResponse(
                    {
                        "message": "User created",
                        "access_token": token,
                        "user_id": str(new_user.user_id)
                    },
                    status_code=status.HTTP_201_CREATED
                )
            logger.warning(f"Signup failed for user: {user_data.username}")
            return JSONResponse(
                {
                    "message": "Signup failed, try to change the username"
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as error:
            logger.error(f"Unexpected error during signup: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    @user_router.delete("/avatar", summary="Delete avatar")
    async def delete_avatar_endpoint(self, token: str = Depends(get_current_user_id)) -> JSONResponse:
        try:
            user = await delete_avatar_database(user_id=token, db=self.db)
            if user:
                await delete_avatar(user_id=token)
                return JSONResponse(
                    {
                        "message": "Avatar deleted successfully"
                    },
                    status_code=status.HTTP_200_OK
                )
            return JSONResponse(
                {
                    "message": "Avatar deleted successfully"
                },
                status_code=status.HTTP_200_OK
            )
        except Exception as error:
            logger.error(f"Error during avatar deletion: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    @user_router.post("/avatar", summary="Upload avatar")
    async def upload_avatar_endpoint(
        self,
        user_id: UUID = Depends(get_current_user_id),
        file: UploadFile = File(...)
    ) -> JSONResponse:
        try:
            if not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Only images allowed")

            content = await file.read()
            s3_path = await post_avatar(user_id=user_id, file=content)

            user = await add_avatar(user_id=user_id, avatar_url=s3_path, db=self.db)

            if user:
                return JSONResponse(
                    content={"message": "Avatar uploaded", "path": s3_path},
                    status_code=status.HTTP_201_CREATED
                )
            raise HTTPException(status_code=404, detail="User not found")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Avatar upload failed: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @user_router.get("/avatar", summary="Get avatar")
    async def get_avatar_endpoint(self, user_id: UUID = Depends(get_current_user_id)) -> JSONResponse:
        avatar_path = await get_avatar(user_id=user_id, db=self.db)

        if avatar_path:
            full_url = f"http://localhost:9000/{avatar_path}"
            return JSONResponse({"avatar_url": full_url})

        return JSONResponse(
            {
                "message": "Using default avatar",
                "avatar_url": "http://localhost:9000/avatars/default_avatar.jpeg"
            }
        )
