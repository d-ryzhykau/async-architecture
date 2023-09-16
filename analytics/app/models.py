from sqlalchemy import UUID, Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    public_id = mapped_column(UUID, primary_key=True)
    email = mapped_column(String(256), nullable=False, unique=True)
    role = mapped_column(String, index=True, nullable=False)
    is_deleted = mapped_column(Boolean, nullable=False, default=False)


class Task(Base):
    __tablename__ = "task"

    public_id = mapped_column(UUID, primary_key=True)
    description = mapped_column(Text, nullable=False)
    jira_id = mapped_column(String, nullable=True)

    assignment_price = mapped_column(Numeric(4, 2), nullable=False)
    completion_price = mapped_column(Numeric(4, 2), nullable=False)


class Account(Base):
    __tablename__ = "account"

    public_id = mapped_column(UUID, primary_key=True)
    balance = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=0,
    )

    owner_public_id = mapped_column(UUID, unique=True)


class NewTaskAddedEvent(Base):
    __tablename__ = "new_task_added_event"

    id = mapped_column(Integer, primary_key=True)
    timestamp = mapped_column(DateTime, nullable=False)
    public_id = mapped_column(UUID, nullable=False)
    assigned_to_public_id = mapped_column(UUID, nullable=False)
    assignment_price = mapped_column(Numeric(4, 2), nullable=False)


class TaskReassignedEvent(Base):
    __tablename__ = "task_reassigned_event"

    id = mapped_column(Integer, primary_key=True)
    timestamp = mapped_column(DateTime, nullable=False)
    public_id = mapped_column(UUID, nullable=False)
    assigned_to_public_id = mapped_column(UUID, nullable=False)
    assignment_price = mapped_column(Numeric(4, 2), nullable=False)


class TaskCompletedEvent(Base):
    __tablename__ = "task_completed_event"

    id = mapped_column(Integer, primary_key=True)
    timestamp = mapped_column(DateTime, nullable=False)
    public_id = mapped_column(UUID, nullable=False)
    assigned_to_public_id = mapped_column(UUID, nullable=False)
    completion_price = mapped_column(Numeric(4, 2), nullable=False)
