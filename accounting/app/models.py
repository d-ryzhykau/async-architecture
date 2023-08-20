from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
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

    assigned_tasks: Mapped[List["Task"]] = relationship(back_populates="assigned_to")
    account: Mapped["Account"] = relationship(back_populates="owner")


class Task(Base):
    __tablename__ = "task"

    public_id = mapped_column(UUID, primary_key=True)
    is_completed = mapped_column(Boolean, nullable=False, default=False)
    description = mapped_column(Text, nullable=False)
    jira_id = mapped_column(String, nullable=True)

    assignment_price = mapped_column(Numeric(4, 2), nullable=False)
    completion_price = mapped_column(Numeric(4, 2), nullable=False)

    assigned_to_public_id = mapped_column(ForeignKey("user.public_id"), nullable=False)
    assigned_to: Mapped["User"] = relationship(back_populates="assigned_tasks")


class Account(Base):
    __tablename__ = "account"

    id = mapped_column(Integer, primary_key=True)
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


class BillingCycle(Base):
    __tablename__ = "billing_cycle"

    id = mapped_column(Integer, primary_key=True)
    closed_at = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    audit_log_records: Mapped[List["AuditLogRecord"]] = relationship(
        back_populates="billing_cycle"
    )

    credit = mapped_column(Numeric(6, 2), nullable=False)
    debit = mapped_column(Numeric(6, 2), nullable=False)


class AuditLogRecord(Base):
    __tablename__ = "audit_log_record"

    id = mapped_column(Integer, primary_key=True)
    credit = mapped_column(Numeric(4, 2), nullable=False, default=0)
    debit = mapped_column(Numeric(4, 2), nullable=False, default=0)
    created_at = mapped_column(DateTime, default=datetime.utcnow)

    account_id = mapped_column(ForeignKey("account.id"), nullable=False)
    account: Mapped["Account"] = relationship(back_populates="audit_log_records")

    # TODO: use strictly typed columns instead of metadata
    info = mapped_column(JSONB, nullable=True)

    # null for records of running billing cycle
    billing_cycle_id = mapped_column(ForeignKey("billing_cycle.id"), nullable=True)
    billing_cycle: Mapped[Optional["BillingCycle"]] = relationship(
        back_populates="audit_log_records"
    )
