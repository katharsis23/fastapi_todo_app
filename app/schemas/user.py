from pydantic import BaseModel, Field, field_validator, EmailStr


class UserLogin(BaseModel):
    password: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Password (5-100 characters)"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Password cannot be empty')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class UserSignup(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username (3-50 characters)"
    )
    password: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Password (5-100 characters)"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address"
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Username cannot be empty')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError(
                'Username can only contain letters, numbers, _ and -'
            )
        return v.strip().lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Password cannot be empty')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class UserVerify(BaseModel):
    email: EmailStr = Field(..., description="User email")
    code: str = Field(..., description="Verification code")
