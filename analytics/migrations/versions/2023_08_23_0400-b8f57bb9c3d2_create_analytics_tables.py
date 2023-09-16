"""create analytics tables

Revision ID: b8f57bb9c3d2
Revises: d8879e8d82ee
Create Date: 2023-08-23 04:00:33.435900

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8f57bb9c3d2"
down_revision: Union[str, None] = "d8879e8d82ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "new_task_added_event",
        sa.Column(
            "id",
            sa.Integer,
            primary_key=True,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime,
            nullable=False,
        ),
        sa.Column(
            "public_id",
            sa.UUID,
            nullable=False,
        ),
        sa.Column(
            "assigned_to_public_id",
            sa.UUID,
            nullable=False,
        ),
        sa.Column(
            "assignment_price",
            sa.Numeric(4, 2),
            nullable=False,
        ),
    )
    op.create_table(
        "task_reassigned_event",
        sa.Column(
            "id",
            sa.Integer,
            primary_key=True,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime,
            nullable=False,
        ),
        sa.Column(
            "public_id",
            sa.UUID,
            nullable=False,
        ),
        sa.Column(
            "assigned_to_public_id",
            sa.UUID,
            nullable=False,
        ),
        sa.Column(
            "assignment_price",
            sa.Numeric(4, 2),
            nullable=False,
        ),
    )
    op.create_table(
        "task_completed_event",
        sa.Column(
            "id",
            sa.Integer,
            primary_key=True,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime,
            nullable=False,
        ),
        sa.Column(
            "public_id",
            sa.UUID,
            nullable=False,
        ),
        sa.Column(
            "assigned_to_public_id",
            sa.UUID,
            nullable=False,
        ),
        sa.Column(
            "completion_price",
            sa.Numeric(4, 2),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("new_task_added_event")
    op.drop_table("task_reassigned_event")
    op.drop_table("task_completed_event")
