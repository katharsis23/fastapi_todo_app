from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class TaskCreate(BaseModel):
    title: str
    description: Optional[str]
    appointed_at: Optional[datetime]


class TaskUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    appointed_at: Optional[datetime]
