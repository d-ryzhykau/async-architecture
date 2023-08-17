"""create user table

Revision ID: 529aaf2e5e59
Revises:
Create Date: 2023-08-10 01:57:59.177363

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "529aaf2e5e59"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
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
            "email",
            sa.String(256),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum(
                "manager",
                "accountant",
                "worker",
                create_constraint=True,
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "password_hash",
            sa.String,
            nullable=False,
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean,
            nullable=False,
            default=False,
        ),
        sa.Index(
            "key_email_not_is_deleted",
            "email",
            unique=True,
            postgresql_where=sa.text("NOT is_deleted"),
        ),
    )


def downgrade() -> None:
    op.drop_table("user")
