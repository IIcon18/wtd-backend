"""add timestamps and fix price type

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-17

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # swim_profiles — add created_at and updated_at
    op.add_column(
        "swim_profiles",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "swim_profiles",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # workouts — add created_at
    op.add_column(
        "workouts",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # payments — add updated_at, change price from Numeric to Integer
    op.add_column(
        "payments",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.alter_column(
        "payments",
        "price",
        type_=sa.Integer(),
        postgresql_using="price::integer",
    )


def downgrade() -> None:
    op.alter_column(
        "payments",
        "price",
        type_=sa.Numeric(10, 2),
        postgresql_using="price::numeric",
    )
    op.drop_column("payments", "updated_at")
    op.drop_column("workouts", "created_at")
    op.drop_column("swim_profiles", "updated_at")
    op.drop_column("swim_profiles", "created_at")