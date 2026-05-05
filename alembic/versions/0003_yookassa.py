"""add yookassa_payment_id to payments

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-05

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column("yookassa_payment_id", sa.String(255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_payments_yookassa_payment_id", "payments", ["yookassa_payment_id"]
    )
    op.create_index(
        "ix_payments_yookassa_payment_id", "payments", ["yookassa_payment_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_payments_yookassa_payment_id", table_name="payments")
    op.drop_constraint("uq_payments_yookassa_payment_id", "payments", type_="unique")
    op.drop_column("payments", "yookassa_payment_id")
