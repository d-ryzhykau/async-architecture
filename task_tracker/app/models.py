from functools import partial
from random import randint
from typing import List
from uuid import uuid4

from sqlalchemy import UUID, Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# TODO: use type hints for column definitions
class User(Base):
    __tablename__ = "user"

    public_id = mapped_column(UUID, primary_key=True)
    email = mapped_column(String(256), nullable=False, unique=True)
    role = mapped_column(String, index=True, nullable=False)

    assigned_tasks: Mapped[List["Task"]] = relationship(back_populates="assigned_to")


# TODO: use type hints for column definitions
class Task(Base):
    __tablename__ = "task"

    id = mapped_column(Integer, primary_key=True)
    public_id = mapped_column(UUID, unique=True, default=uuid4)
    is_completed = mapped_column(Boolean, nullable=False, default=False)
    description = mapped_column(Text, nullable=False)

    assignment_price = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=partial(randint, 10, 20),
    )
    completion_price = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=partial(randint, 20, 40),
    )

    assigned_to_public_id = mapped_column(ForeignKey("user.public_id"), nullable=False)
    assigned_to: Mapped["User"] = relationship(back_populates="assigned_tasks")
