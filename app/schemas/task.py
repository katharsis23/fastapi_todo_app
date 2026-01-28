from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone


class TaskCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Task title (1-150 characters)"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional task description"
    )
    appointed_at: Optional[datetime] = Field(
        None,
        description="Optional scheduled completion time"
    )

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @field_validator('appointed_at')
    @classmethod
    def validate_appointed_at(
        cls, v: Optional[datetime]
    ) -> Optional[datetime]:
        if v:
            # Convert naive datetime to UTC aware
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            elif v.tzinfo != timezone.utc:
                v = v.astimezone(timezone.utc)
            if v < datetime.now(timezone.utc):
                raise ValueError('Appointment time cannot be in the past')
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=150,
        description="Task title (1-150 characters)"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional task description"
    )
    appointed_at: Optional[datetime] = Field(
        None,
        description="Optional scheduled completion time"
    )

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip() if v else v

    @field_validator('appointed_at')
    @classmethod
    def validate_appointed_at(
        cls, v: Optional[datetime]
    ) -> Optional[datetime]:
        if v:
            # Convert naive datetime to UTC aware
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            elif v.tzinfo != timezone.utc:
                v = v.astimezone(timezone.utc)
            if v < datetime.now(timezone.utc):
                raise ValueError('Appointment time cannot be in the past')
        return v
