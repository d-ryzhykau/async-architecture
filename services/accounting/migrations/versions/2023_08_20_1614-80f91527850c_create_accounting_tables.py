"""create accounting tables

Revision ID: 80f91527850c
Revises: ca5125875046
Create Date: 2023-08-20 16:14:32.301715

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "80f91527850c"
down_revision: Union[str, None] = "ca5125875046"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "account",
        sa.Column(
            "id",
            sa.Integer,
            primary_key=True,
        ),
        sa.Column(
            "public_id",
            sa.UUID,
            unique=True,
        ),
        sa.Column(
            "balance",
            sa.Numeric(6, 2),
            nullable=False,
        ),
        sa.Column(
            "owner_public_id",
            sa.UUID,
            sa.ForeignKey("user.public_id"),
            nullable=False,
            unique=True,
        ),
    )
    op.create_table(
        "audit_log_record",
        sa.Column(
            "id",
            sa.Integer,
            primary_key=True,
        ),
        sa.Column(
            "credit",
            sa.Numeric(6, 2),
            nullable=False,
        ),
        sa.Column(
            "debit",
            sa.Numeric(6, 2),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.Enum(
                "task_assigned",
                "task_completed",
                "payout",
                create_constraint=True,
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
        ),
        sa.Column(
            "info",
            JSONB,
            nullable=True,
        ),
        sa.Column(
            "account_id",
            sa.Integer,
            sa.ForeignKey("account.id"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_log_record")
    op.drop_table("account")
