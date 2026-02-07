from fastapi import status, Depends, HTTPException, APIRouter, Query
from fastapi_utils.cbv import cbv
from fastapi.responses import JSONResponse
from app.database.database import get_db, AsyncSession
from app.database import task as task_db
from app.utils.oauth2Schema import get_current_user_id
from app.schemas.task import TaskCreate, TaskUpdate
from app.schemas.responses import (
    TaskCreateResponse,
    TaskUpdateResponse
)
from loguru import logger
from uuid import UUID


tasks_router = APIRouter(prefix="/task", tags=["Task"])


@cbv(tasks_router)
class TaskViews:
    db: AsyncSession = Depends(get_db)

    @tasks_router.post("/", summary="Create task")
    async def create_task_endpoint(
        self,
        task_data: TaskCreate,
        token=Depends(get_current_user_id)
    ) -> JSONResponse:
        logger.info(f"Creating task for user {token}: {task_data.title}")
        try:
            created_task_id = await task_db.create_task(
                task=task_data,
                user_id=token,
                db=self.db
            )
            if created_task_id:
                logger.info(f"Task created successfully: {created_task_id}")
                response = TaskCreateResponse(
                    message="Task created successfully",
                    task_id=str(created_task_id)
                )
                return JSONResponse(
                    response.model_dump(),
                    status_code=status.HTTP_201_CREATED
                )
            else:
                logger.warning(f"Task creation failed for user {token}")
                return JSONResponse(
                    {"message": "Task creation failed"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except HTTPException as error:
            logger.error(f"HTTP error during task creation: {error}")
            raise
        except Exception as error:
            logger.error(f"Unexpected error during task creation: {error}")
            return JSONResponse(
                {"message": "Internal server error"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @tasks_router.patch("/{task_id}", summary="Changing task parameter")
    async def update_task_endpoint(
        self,
        task_id: UUID,
        task: TaskUpdate,
        token=Depends(get_current_user_id)
    ) -> JSONResponse:
        logger.info(f"Updating task {task_id} for user {token}")
        try:
            existing_task = await task_db.get_task_by_id(
                task_id=task_id,
                user_id=token,
                db=self.db
            )
            if existing_task:
                updated_task = await task_db.update_task_by_id(
                    task_id=task_id,
                    task_update_data=task,
                    user_id=token,
                    db=self.db
                )
                if updated_task:
                    logger.info(f"Task {task_id} updated successfully")
                    response = TaskUpdateResponse(
                        message="Update successful",
                        task_id=str(updated_task.task_id),
                        new_title=updated_task.title if task.title else None,
                        new_description=(
                            updated_task.description
                            if task.description else None
                        ),
                        new_appointed_at=(
                            updated_task.appointed_at.isoformat()
                            if updated_task.appointed_at else None
                        )
                    )
                    return JSONResponse(
                        response.model_dump(),
                        status_code=status.HTTP_200_OK
                    )
            logger.warning(
                f"Task {task_id} not found or update failed for user {token}"
            )
            return JSONResponse(
                {"message": "Task not found or update failed"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except HTTPException as error:
            logger.error(f"HTTP error during task update: {error}")
            raise
        except Exception as error:
            logger.error(f"Unexpected error during task update: {error}")
            return JSONResponse(
                {"message": "Internal server error"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @tasks_router.delete("/{task_id}", summary="Delete the specified task")
    async def delete_task_endpoint(
        self,
        task_id: UUID,
        token=Depends(get_current_user_id),
    ) -> JSONResponse:
        logger.info(f"Deleting task {task_id} for user {token}")
        try:
            deleted = await task_db.remove_task(
                task_id=task_id,
                user_id=token,
                db=self.db,
            )
            if deleted:
                logger.info(f"Task {task_id} deleted successfully")
                return JSONResponse(
                    {"message": "Task deleted successfully"},
                    status_code=status.HTTP_200_OK,
                )
            logger.warning(f"Task {task_id} not found for user {token}")
            return JSONResponse(
                {"message": "Task not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except HTTPException as error:
            logger.error(f"HTTP error during task deletion: {error}")
            return JSONResponse(
                {"message": "Internal server error"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as error:
            logger.error(f"Unexpected error during task deletion: {error}")
            print(f"DEBUG_TASK_ERROR: {error}")
            return JSONResponse(
                {"message": "Internal server error"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @tasks_router.get("/", summary="Get all tasks of user")
    async def get_tasks_endpoint(
        self,
        token=Depends(get_current_user_id),
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(
            10, ge=1, le=100, description="Number of tasks per page"
        )
    ) -> JSONResponse:
        logger.info(
            f"Getting tasks for user {token}, "
            f"page {page}, size {size}"
        )
        try:
            skip = (page - 1) * size
            tasks = await task_db.get_user_tasks(token, self.db, skip, size)
            total_tasks = await task_db.count_user_tasks(token, self.db)
            total_pages = (
                total_tasks + size - 1
            ) // size if size > 0 else 0

            logger.info(
                f"Retrieved {len(tasks)} tasks for user {token}, "
                f"page {page}/{total_pages}"
            )

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
