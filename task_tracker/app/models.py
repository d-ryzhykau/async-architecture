from functools import partial
from random import randint
from uuid import uuid4
from typing import List

from sqlalchemy import UUID, Boolean, String, ForeignKey, Text, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# TODO: use type hints for column definitions
class User(Base):
    __tablename__ = "user"

    uuid = mapped_column(UUID, primary_key=True)
    email = mapped_column(String(256), nullable=False, unique=True)
    role = mapped_column(String, index=True, nullable=False)
    is_deleted = mapped_column(Boolean, nullable=False, default=False)

    assigned_tasks: Mapped[List["Task"]] = relationship(back_populates="assigned_to")


# TODO: use type hints for column definitions
class Task(Base):
    __tablename__ = "task"

    # TODO: use separate internal and public ID's
    uuid = mapped_column(UUID, primary_key=True, default=uuid4)
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

    assigned_to_uuid = mapped_column(ForeignKey("user.uuid"), nullable=False)
    assigned_to: Mapped["User"] = relationship(back_populates="assigned_tasks")
