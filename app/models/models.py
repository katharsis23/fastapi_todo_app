from app.database import DECLARATIVE_BASE
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey
from uuid import UUID, uuid4
from datetime import datetime, timezone


class Task(DECLARATIVE_BASE):
    __tablename__ = "task"

    task_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    appointed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    user_fk: Mapped[UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="tasks")


class User(DECLARATIVE_BASE):
    __tablename__ = "users"

    user_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    password: Mapped[str] = mapped_column(String(500), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    avatar_url: Mapped[str] = mapped_column(String(255), nullable=True)

    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="user")
