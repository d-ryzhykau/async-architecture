"""add task.jira_id

Revision ID: 77df06dc8023
Revises: 912abc546746
Create Date: 2023-08-17 23:32:59.199926

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77df06dc8023'
down_revision: Union[str, None] = '912abc546746'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "task",
        sa.Column(
            "jira_id",
            sa.String,
            nullable=True,
        )
    )


def downgrade() -> None:
    op.drop_column("task", "jira_id")
