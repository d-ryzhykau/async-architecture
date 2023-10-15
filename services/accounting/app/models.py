import enum
from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    public_id = mapped_column(UUID, primary_key=True)
    email = mapped_column(String(256), nullable=False, unique=True)
    role = mapped_column(String, index=True, nullable=False)
    is_deleted = mapped_column(Boolean, nullable=False, default=False)

    account: Mapped["Account"] = relationship(back_populates="owner")


class Task(Base):
    __tablename__ = "task"

    public_id = mapped_column(UUID, primary_key=True)
    description = mapped_column(Text, nullable=False)
    jira_id = mapped_column(String, nullable=True)

    assignment_price = mapped_column(Numeric(4, 2), nullable=False)
    completion_price = mapped_column(Numeric(4, 2), nullable=False)


class Account(Base):
    __tablename__ = "account"

    id = mapped_column(Integer, primary_key=True)
    public_id = mapped_column(UUID, unique=True, nullable=False, default=uuid4)
    balance = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=0,
    )

    owner_public_id = mapped_column(
        ForeignKey("user.public_id"), nullable=True, unique=True
    )
    owner: Mapped["User"] = relationship(back_populates="account")

    audit_log_records: Mapped[List["AuditLogRecord"]] = relationship(
        back_populates="account"
    )


class AuditLogRecordReason(str, enum.Enum):
    task_assigned = "task_assigned"
    task_completed = "task_completed"
    payout = "payout"


class AuditLogRecord(Base):
    __tablename__ = "audit_log_record"

    id = mapped_column(Integer, primary_key=True)
    credit = mapped_column(Numeric(4, 2), nullable=False, default=0)
    debit = mapped_column(Numeric(4, 2), nullable=False, default=0)
    reason = mapped_column(Enum(AuditLogRecordReason), nullable=False)
    created_at = mapped_column(DateTime, default=datetime.utcnow)

    # TODO: use strictly typed columns instead of metadata
    info = mapped_column(JSONB, nullable=True)

    account_id = mapped_column(ForeignKey("account.id"), nullable=False)
    account: Mapped["Account"] = relationship(back_populates="audit_log_records")
