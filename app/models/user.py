from app.database import DECLARATIVE_BASE
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from uuid import UUID, uuid4    # noqa F811


class User(DECLARATIVE_BASE):
    __tablename__ = "users"

    user_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    password: Mapped[str] = mapped_column(String(500), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
