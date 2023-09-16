"""create user and task tables

Revision ID: ca5125875046
Revises:
Create Date: 2023-08-20 16:04:39.205826

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ca5125875046"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column(
            "public_id",
            sa.UUID,
            primary_key=True,
        ),
        sa.Column(
            "email",
            sa.String(256),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String,
            index=True,
            nullable=False,
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean,
            nullable=False,
        ),
    )
    op.create_table(
        "task",
        sa.Column(
            "public_id",
            sa.UUID,
            primary_key=True,
        ),
        sa.Column(
            "description",
            sa.Text,
            nullable=False,
        ),
        sa.Column(
            "jira_id",
            sa.String,
            nullable=True,
        ),
        sa.Column(
            "assignment_price",
            sa.Numeric(precision=4, scale=2),
            nullable=False,
        ),
        sa.Column(
            "completion_price",
            sa.Numeric(precision=4, scale=2),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("task")
    op.drop_table("user")
