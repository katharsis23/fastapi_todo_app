from fastapi.responses import JSONResponse
from fastapi import status, Depends, APIRouter, HTTPException
from fastapi_utils.cbv import cbv
from app.schemas.user import UserLogin, UserSignup, UserAuthResponse, UserInfo
from app.database import user as user_db
from app.database.database import get_db, AsyncSession
from sqlalchemy.future import select
from app.models.models import User
from app.utils.jwt_manager import create_access_token
from app.external import avatar as avatar_ext
from app.utils.oauth2Schema import get_current_user_id
from loguru import logger
from fastapi import File, UploadFile
from uuid import UUID
from app.core.celery_worker import start_verification
from app.schemas.user import UserVerify, UserResendCode
from app.redis_client import redis_session
from app.database import avatar as avatar_db
from datetime import datetime
from sqlalchemy.exc import IntegrityError

user_router = APIRouter(prefix="/user", tags=["User"])


@cbv(user_router)
class UserViews:
    db: AsyncSession = Depends(get_db)

    @user_router.post("/login", summary="Login", response_model=UserAuthResponse)
    async def login_endpoint(self, user_data: UserLogin) -> UserAuthResponse:
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
            return UserAuthResponse(
                access_token=token,
                user=UserInfo.model_validate(user),
                message="Login successful"
            )
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Unexpected error during login: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    @user_router.post("/signup", summary="Create user", response_model=UserAuthResponse)
    async def signup_endpoint(self, user_data: UserSignup) -> UserAuthResponse:
        logger.info(f"Signup attempt for user: {user_data.email}")
        try:
            new_user = await user_db.create_user(db=self.db, user=user_data)
            if new_user:
                await start_verification(email=user_data.email)
                logger.info(f"User {user_data.email} created successfully. Verification pending.")

                token = create_access_token(user_id=new_user.user_id)
                return UserAuthResponse(
                    access_token=token,
                    user=UserInfo.model_validate(new_user),
                    message="User created. Please verify your email."
                )
            logger.warning(f"Signup failed for user: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup failed, try to change the username"
            )
        except IntegrityError as e:
            logger.warning(f"Integrity error during signup: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup failed: email or username already exists"
            )
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Unexpected error during signup: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    @user_router.post("/verify", summary="Verify user email", response_model=UserAuthResponse)
    async def verify_user_endpoint(self, verify_data: UserVerify) -> UserAuthResponse:
        logger.info(f"Verification attempt for: {verify_data.email}")
        try:
            async with redis_session() as session:
                redis_code = await session.get(f"verification:{verify_data.email}")

            if not redis_code or redis_code != verify_data.code:
                raise HTTPException(status_code=400, detail="Invalid code or expired")

            verified_user = await user_db.verify_user(email=verify_data.email, db=self.db)
            if verified_user:
                token = create_access_token(user_id=verified_user.user_id)
                return UserAuthResponse(
                    access_token=token,
                    user=UserInfo.model_validate(verified_user),
                    message="User verified successfully"
                )
            raise HTTPException(status_code=404, detail="User not found")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verification: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @user_router.post("/resend-code", summary="Resend verification code")
    async def resend_verify_code_endpoint(self, email_data: UserResendCode) -> JSONResponse:
        logger.info(f"Resend code request for: {email_data.email}")
        try:
            user = await self.db.scalar(select(User).where(User.email == email_data.email))

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            if user.is_verified:
                raise HTTPException(status_code=400, detail="User already verified")

            await start_verification(email=email_data.email)
            return JSONResponse(
                content={"message": "Verification code resent successfully"},
                status_code=status.HTTP_200_OK
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resending code: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @user_router.delete("/avatar", summary="Delete avatar")
    async def delete_avatar_endpoint(self, token: str = Depends(get_current_user_id)) -> JSONResponse:
        try:
            # For v2, we should ideally check metadata for extension
            # For now, let's try to delete with common extensions or just the ID if it was old
            user = await user_db.delete_avatar_database(user_id=token, db=self.db)
            avatar_v2 = await avatar_db.get_avatar_by_user_id_v2(user_id=token, db=self.db)

            if avatar_v2:
                # Try to extract extension from stored URL or metadata
                ext = "jpg"
                if "." in avatar_v2.url:
                    ext = avatar_v2.url.split(".")[-1]
                await avatar_ext.delete_avatar(user_id=token, extension=ext)
                await avatar_db.delete_avatar_v2(user_id=token, db=self.db)
            elif user:
                await avatar_ext.delete_avatar(user_id=token)   # default jpg

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
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only images allowed"
                )

            if file.size > 1024 * 1024 * 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File too large"
                )

            content = await file.read()
            extension = file.content_type.split('/')[-1] if '/' in file.content_type else "jpg"
            s3_path = await avatar_ext.post_avatar(user_id=user_id, file=content, extension=extension)

            user = await user_db.add_avatar(user_id=user_id, url=s3_path, db=self.db)

            if user:
                return JSONResponse(
                    content={"message": "Avatar uploaded", "path": f"http://localhost:9000/{s3_path}"},
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
        # Check v2 first
        avatar_path = await avatar_db.get_avatar_url_by_user_id_v2(user_id=user_id, db=self.db)

        # Then check v1 if v2 is empty
        if not avatar_path:
            avatar_path = await user_db.get_avatar(user_id=user_id, db=self.db)

        if avatar_path:
            # Ensure path includes bucket name
            if not avatar_path.startswith("avatars/"):
                avatar_path = f"avatars/{avatar_path}"

            full_url = f"http://localhost:9000/{avatar_path}"
            return JSONResponse({"avatar_url": full_url})

        return JSONResponse(
            {
                "message": "Using default avatar",
                "avatar_url": "http://localhost:9000/avatars/default_avatar.jpeg"
            }
        )

    @user_router.get("/avatar/v2", summary="Get avatar")
    async def get_avatar_endpoint_v2(self, user_id: UUID = Depends(get_current_user_id)) -> JSONResponse:
        avatar_url = await avatar_db.get_avatar_url_by_user_id_v2(user_id=user_id, db=self.db)
        if avatar_url:
            # Ensure path includes bucket name
            if not avatar_url.startswith("avatars/"):
                avatar_url = f"avatars/{avatar_url}"

            full_url = f"http://localhost:9000/{avatar_url}"
            return JSONResponse({"avatar_url": full_url})
        return JSONResponse(
            {
                "message": "Using default avatar",
                "avatar_url": "http://localhost:9000/avatars/default_avatar.jpeg"
            }
        )

    @user_router.post("/avatar/v2", summary="Upload avatar")
    async def upload_avatar_v2(self, file: UploadFile = File(...), user_id: UUID = Depends(get_current_user_id)) -> JSONResponse:
        try:
            if file.size > 1024 * 1024 * 10:
                raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

            if not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Only images allowed")

            content = await file.read()
            extension = file.content_type.split('/')[-1] if '/' in file.content_type else "jpg"
            s3_path = await avatar_ext.post_avatar(user_id=user_id, file=content, extension=extension)
            metadata = {
                "uploaded_at": datetime.now().isoformat(),
                "file_size": file.size,
                "content_type": file.content_type
            }
            user = await avatar_db.add_avatar_v2(user_id=user_id, url=s3_path, db=self.db, metadata=metadata)

            if user:
                return JSONResponse(
                    content={"message": "Avatar uploaded", "path": f'http://localhost:9000/{s3_path}'},
                    status_code=status.HTTP_201_CREATED
                )
            raise HTTPException(status_code=404, detail="User not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Avatar upload failed: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
