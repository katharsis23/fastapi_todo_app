from app.models.models import Task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from loguru import logger
from app.schemas.task import TaskCreate, TaskUpdate
from uuid import UUID
from typing import Optional, List


async def create_task(
    task: TaskCreate,
    user_id: UUID,
    db: AsyncSession
) -> Optional[UUID]:
    try:
        db_task = Task(
            title=task.title,
            description=task.description,
            appointed_at=task.appointed_at,
            user_fk=user_id
        )
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        return db_task.task_id
    except Exception as error:
        logger.error(f"Error during task creation: {error}")
        await db.rollback()
        return None


async def find_task_by_id(
    task_id: UUID,
    user_id: UUID,
    db: AsyncSession
) -> Optional[Task]:
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


async def update_task(
    task_id: UUID,
    task_update_data: TaskUpdate,
    user_id: UUID,
    db: AsyncSession
) -> Optional[Task]:
    try:
        existing_task = await find_task_by_id(
            task_id=task_id,
            user_id=user_id,
            db=db
        )

        if existing_task is None:
            logger.warning(f"Task {task_id} not found or access denied")
            return None

        update_data = task_update_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if hasattr(existing_task, key):
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
        existing_task = await find_task_by_id(
            task_id=task_id,
            user_id=user_id,
            db=db
        )
        if existing_task:
            await db.delete(existing_task)
            await db.commit()
            return True
        return False
    except Exception as error:
        await db.rollback()
        logger.error(f"Delete failed: {error}")
        return False


async def get_all_tasks_by_user(
    user_id: UUID,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10
) -> List[Task]:
    try:
        query = await db.execute(
            select(Task)
            .where(Task.user_fk == user_id)
            .offset(skip)
            .limit(limit)
        )
        return query.scalars().all()
    except Exception as error:
        logger.error(f"Failed to get all tasks: {error}")
        return []


async def get_tasks_count_by_user(user_id: UUID, db: AsyncSession) -> int:
    try:
        query = await db.execute(
            select(func.count(Task.task_id))
            .where(Task.user_fk == user_id)
        )
        return query.scalar()
    except Exception as error:
        logger.error(f"Failed to get tasks count: {error}")
        return 0
