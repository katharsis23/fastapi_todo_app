from fastapi.responses import JSONResponse
from fastapi import status, Depends, APIRouter, HTTPException
from fastapi_utils.cbv import cbv
from app.schemas.user import UserLogin, UserSignup
from app.database import user as user_db
from app.database.database import get_db, AsyncSession
from app.utils.jwt_manager import create_access_token
from app.external import avatar as avatar_ext
from app.utils.oauth2Schema import get_current_user_id
from loguru import logger
from fastapi import File, UploadFile
from uuid import UUID
from app.core.celery_worker import start_verification
from app.schemas.user import UserVerify
from app.redis_client import redis_session

user_router = APIRouter(prefix="/user", tags=["User"])


@cbv(user_router)
class UserViews:
    db: AsyncSession = Depends(get_db)

    @user_router.post("/login", summary="Login")
    async def login_endpoint(self, user_data: UserLogin) -> JSONResponse:
        logger.info(f"Login attempt for user: {user_data.email}")
        try:
            user = await user_db.authenticate_user(db=self.db, user=user_data)
            if not user:
                logger.warning(f"Login failed for user: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid credentials"
                )

            if not user.is_verified:
                logger.warning(f"Unverified user login attempt: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email not verified"
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
            new_user = await user_db.create_user(db=self.db, user=user_data)
            if new_user:
                await start_verification(email=user_data.email)
                logger.info(f"User {user_data.email} created successfully. Verification pending.")
                return JSONResponse(
                    {
                        "message": "User created. Please verify your email.",
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

    @user_router.post("/verify", summary="Verify user email")
    async def verify_user_endpoint(self, verify_data: UserVerify) -> JSONResponse:
        logger.info(f"Verification attempt for: {verify_data.email}")
        try:
            async with redis_session() as session:
                redis_code_bytes = await session.get(f"verification:{verify_data.email}")
                redis_code = redis_code_bytes if redis_code_bytes else None

            if not redis_code or redis_code != verify_data.code:
                raise HTTPException(status_code=400, detail="Invalid code or expired")

            verified_user = await user_db.verify_user(email=verify_data.email, db=self.db)
            if verified_user:
                token = create_access_token(user_id=verified_user.user_id)
                return JSONResponse(
                    content={
                        "message": "User verified successfully",
                        "access_token": token,
                        "token_type": "bearer"
                    },
                    status_code=status.HTTP_200_OK
                )
            raise HTTPException(status_code=404, detail="User not found")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verification: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @user_router.delete("/avatar", summary="Delete avatar")
    async def delete_avatar_endpoint(self, token: str = Depends(get_current_user_id)) -> JSONResponse:
        try:
            user = await user_db.delete_avatar_database(user_id=token, db=self.db)
            if user:
                await avatar_ext.delete_avatar(user_id=token)
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
            s3_path = await avatar_ext.post_avatar(user_id=user_id, file=content)

            user = await user_db.add_avatar(user_id=user_id, avatar_url=s3_path, db=self.db)

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
        avatar_path = await user_db.get_avatar(user_id=user_id, db=self.db)

        if avatar_path:
            full_url = f"http://localhost:9000/{avatar_path}"
            return JSONResponse({"avatar_url": full_url})

        return JSONResponse(
            {
                "message": "Using default avatar",
                "avatar_url": "http://localhost:9000/avatars/default_avatar.jpeg"
            }
        )
