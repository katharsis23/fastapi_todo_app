from fastapi import status, Depends, HTTPException, APIRouter, Query
from fastapi_utils.cbv import cbv
from fastapi.responses import JSONResponse
from app.database.database import get_db
from app.database.task import (
    create_task,
    update_task,
    delete_task,
    find_task_by_id,
    get_all_tasks_by_user,
    get_tasks_count_by_user
)
from app.utils.oauth2Schema import get_current_user_id
from app.schemas.task import TaskCreate, TaskUpdate
from loguru import logger
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession


tasks_endpoints = APIRouter(prefix="/task", tags=["Task"])


@cbv(tasks_endpoints)
class TaskViews:
    db: AsyncSession = Depends(get_db)

    @tasks_endpoints.post("/", summary="Create task")
    async def post_task(
        self,
        task_data: TaskCreate,
        token=Depends(get_current_user_id)
    ) -> JSONResponse:
        try:
            created_task_id = await create_task(
                task=task_data,
                user_id=token,
                db=self.db
            )
            if created_task_id:
                return JSONResponse(
                    {
                        "message": "Task created succesfully",
                        "task_id": str(created_task_id)
                    },
                    status_code=status.HTTP_201_CREATED
                )
            else:
                return JSONResponse(
                    {
                        "message": "Task creation fails",
                    },
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except HTTPException as error:
            logger.error(f"Failed task creating: {error}")

    @tasks_endpoints.patch("/{task_id}", summary="Changing task parameter")
    async def patch_task(
        self,
        task_id: UUID,
        task: TaskUpdate,
        token=Depends(get_current_user_id)
    ) -> JSONResponse:
        try:
            existing_task = await find_task_by_id(
                task_id=task_id,
                user_id=token,
                db=self.db
            )
            if existing_task:
                updated_task = await update_task(
                    task_id=task_id,
                    task_update_data=task,
                    user_id=token,
                    db=self.db
                )
                if updated_task:
                    return JSONResponse(
                        {
                            "message": "Update successfull",
                            "task_id": str(updated_task.task_id),
                            "new_title": updated_task.title if task.title else None,
                            "new_description": updated_task.description if task.description else None,
                            "new_appointed_at": updated_task.appointed_at.isoformat() if updated_task.appointed_at else None
                        },
                        status_code=status.HTTP_200_OK
                    )
            return JSONResponse(
                {
                    "message": "Something went wrong"
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except HTTPException as error:
            logger.error(f"Error during task update: {error}")

    @tasks_endpoints.delete("/{task_id}", summary="Delete the specified task")
    async def delete_task_view(
        self,
        task_id: UUID,
        token=Depends(get_current_user_id),
    ) -> JSONResponse:
        try:
            deleted = await delete_task(
                task_id=task_id,
                user_id=token,
                db=self.db,
            )
            if deleted:
                return JSONResponse(
                    {"message": "Task deleted successfully"},
                    status_code=status.HTTP_200_OK,
                )
            return JSONResponse(
                {"message": "Task not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except HTTPException as error:
            logger.error(f"Error during task deletion: {error}")
            return JSONResponse(
                {"message": "Internal server error"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @tasks_endpoints.get("/", summary="Get all tasks of user")
    async def get_tasks(
        self,
        token=Depends(get_current_user_id),
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(
            10, ge=1, le=100, description="Number of tasks per page"
        )
    ) -> JSONResponse:
        try:
            skip = (page - 1) * size
            tasks = await get_all_tasks_by_user(token, self.db, skip, size)
            total_tasks = await get_tasks_count_by_user(token, self.db)
            total_pages = (
                total_tasks + size - 1
            ) // size if size > 0 else 0

            return JSONResponse(
                {
                    "tasks": [
                        {
                            "task_id": str(task.task_id),
                            "title": task.title,
                            "description": task.description,
                            "appointed_at": (
                                task.appointed_at.isoformat()
                                if task.appointed_at else None
                            ),
                            "created_at": task.created_at.isoformat()
                        }
                        for task in tasks
                    ],
                    "pagination": {
                        "total_pages": total_pages,
                        "current_page": page,
                        "page_size": size,
                        "has_next": page < total_pages,
                        "has_prev": page > 1
                    }
                },
                status_code=status.HTTP_200_OK
            )
        except HTTPException as error:
            logger.error(f"Error during task retrieval: {error}")
            return JSONResponse(
                {"message": "Internal server error"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
