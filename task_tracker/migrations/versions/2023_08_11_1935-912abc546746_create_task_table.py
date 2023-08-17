"""create task table

Revision ID: 912abc546746
Revises: d8879e8d82ee
Create Date: 2023-08-11 19:35:28.563937

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "912abc546746"
down_revision: Union[str, None] = "d8879e8d82ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "task",
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
            "is_completed",
            sa.Boolean,
            nullable=False,
            default=False,
        ),
        sa.Column(
            "description",
            sa.Text,
            nullable=False,
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
        sa.Column(
            "assigned_to_public_id",
            sa.UUID,
            sa.ForeignKey("user.public_id"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("task")
