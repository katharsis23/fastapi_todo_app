from app.models.models import Task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from loguru import logger
from app.schemas.task import TaskCreate, TaskUpdate
from uuid import UUID
from typing import Optional


async def create_task(task: TaskCreate, user_id: UUID, db: AsyncSession) -> UUID:
    try:
        task = Task(
            short_name=task.title,
            description=task.description,
            appointed_at=task.appointed_at,
            user_fk=user_id
        )
        db.add(task)
        await db.commit()
        await db.refresh(task.task_id)
        return task.task_id
    except Exception as error:
        logger.error(f"Error during task creation: {error}")
        await db.rollback()


async def find_task_by_id(task_id: UUID, db: AsyncSession, user_id: Optional[UUID] = None) -> Optional[Task]:
    try:
        query = await db.execute(
            select(Task).where(
                Task.task_id == task_id,
                Task.user_fk == user_id
            )
        )
        return query.scalar_one_or_none()
    except Exception as error:
        logger.error(f"Failed to find the task: {error}")
        return None


async def update_task(task_update_data: TaskUpdate, user_id: UUID, task_id: UUID, db: AsyncSession) -> Optional[Task]:
    try:
        existing_task = await find_task_by_id(
            task_id=task_id,
            user_id=user_id,
            db=db
        )

        if existing_task is None:
            logger.warning(f"Task {task_id} not found or access denied")
            return None

        update_data = task_update_data.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(existing_task, key, value)

        await db.commit()
        await db.refresh(existing_task)
        return existing_task
    except Exception as error:
        await db.rollback()
        logger.error(f"Update failed: {error}")
        return None


async def delete_task(task_id: UUID, user_id: UUID, db: AsyncSession) -> bool:
    try:
        existing_task = await find_task_by_id(task_id=task_id, user_id=user_id, db=db)
        if existing_task:
            await db.delete(existing_task)
            await db.commit()
            return True
        return False
    except Exception as error:
        await db.rollback()
        logger.error(f"Delete failed: {error}")
        return False
