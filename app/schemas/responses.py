from pydantic import BaseModel
from typing import Optional, Any, List


class APIResponse(BaseModel):
    """Unified API response structure"""
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None


class TaskResponse(BaseModel):
    """Task response schema"""
    task_id: str
    title: str
    description: Optional[str] = None
    appointed_at: Optional[str] = None
    created_at: str


class TaskListResponse(BaseModel):
    """Task list response with pagination"""
    tasks: List[TaskResponse]
    pagination: dict


class TaskCreateResponse(BaseModel):
    """Task creation response"""
    message: str
    task_id: str


class TaskUpdateResponse(BaseModel):
    """Task update response"""
    message: str
    task_id: str
    new_title: Optional[str] = None
    new_description: Optional[str] = None
    new_appointed_at: Optional[str] = None
