from pydantic import BaseModel
from typing import Optional, Any, Dict
import uuid


class UserSchema(BaseModel):
    password: str
    username: str
    id: Optional[uuid.uuid4] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserSignup(BaseModel):
    username: str
    password: str
