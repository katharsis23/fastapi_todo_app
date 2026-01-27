from app.database import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import TYPE_CHECKING    # noqa: TYP001

if TYPE_CHECKING:
    pass


class Task(DeclarativeBase):
    __tablename__ = "task"

    task_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Unique identifier for the task"
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Task title"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed task description"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Task creation timestamp"
    )
    appointed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Scheduled completion time"
    )

    user_fk: Mapped[UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to user"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="tasks",
        lazy="select"
    )


class User(DeclarativeBase):
    __tablename__ = "users"

    user_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        comment="Unique identifier for the user"
    )
    password: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Hashed password"
    )
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="Unique username"
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="URL to user avatar image"
    )

    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan"
    )
