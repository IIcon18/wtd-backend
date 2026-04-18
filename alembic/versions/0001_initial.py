"""initial tables

Revision ID: 0001
Revises:
Create Date: 2026-04-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# pre-declare reusable PgEnum objects with create_type=False
# (types are created via op.execute below)
_userrole = PgEnum("user", "pro", "admin", name="userrole", create_type=False)
_swimlevel = PgEnum("beginner", "intermediate", "advanced", name="swimlevel", create_type=False)
_swimgoal = PgEnum("weight_loss", "endurance", "technique", "competition", name="swimgoal", create_type=False)
_sessionsperweek = PgEnum("2", "3", "5", name="sessionsperweek", create_type=False)
_sessionkm = PgEnum("1000", "1500", "2000", "2500+", name="sessionkm", create_type=False)
_poolsize = PgEnum("25", "50", name="poolsize", create_type=False)
_workouttype = PgEnum("technique", "endurance", "speed", "recovery", name="workouttype", create_type=False)
_subscriptiontier = PgEnum("base", "pro", name="subscriptiontier", create_type=False)
_paymenttier = PgEnum("single", "base", "pro", name="paymenttier", create_type=False)
_paymentstatus = PgEnum("pending", "approved", "declined", name="paymentstatus", create_type=False)


def upgrade() -> None:
    # --- create enum types explicitly ---
    op.execute("CREATE TYPE userrole AS ENUM ('user', 'pro', 'admin')")
    op.execute("CREATE TYPE swimlevel AS ENUM ('beginner', 'intermediate', 'advanced')")
    op.execute("CREATE TYPE swimgoal AS ENUM ('weight_loss', 'endurance', 'technique', 'competition')")
    op.execute("CREATE TYPE sessionsperweek AS ENUM ('2', '3', '5')")
    op.execute("CREATE TYPE sessionkm AS ENUM ('1000', '1500', '2000', '2500+')")
    op.execute("CREATE TYPE poolsize AS ENUM ('25', '50')")
    op.execute("CREATE TYPE workouttype AS ENUM ('technique', 'endurance', 'speed', 'recovery')")
    op.execute("CREATE TYPE subscriptiontier AS ENUM ('base', 'pro')")
    op.execute("CREATE TYPE paymenttier AS ENUM ('single', 'base', 'pro')")
    op.execute("CREATE TYPE paymentstatus AS ENUM ('pending', 'approved', 'declined')")

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", _userrole, nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # --- swim_profiles ---
    op.create_table(
        "swim_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("level", _swimlevel, nullable=False),
        sa.Column("goal", _swimgoal, nullable=False),
        sa.Column("sessions_per_week", _sessionsperweek, nullable=False),
        sa.Column("session_km", _sessionkm, nullable=False),
        sa.Column("pool_meters", _poolsize, nullable=False),
        sa.Column("single_workout_available", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_swim_profiles_user_id"),
    )

    # --- workouts ---
    op.create_table(
        "workouts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("level", _swimlevel, nullable=False),
        sa.Column("type", _workouttype, nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("pool_meters", sa.Integer(), nullable=False),
        sa.Column("km_range", sa.String(50), nullable=False),
        sa.Column("content", JSONB(), nullable=False),
        sa.Column("tags", ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- user_sessions ---
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("workout_type", _workouttype, nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("distance_m", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_created_at", "user_sessions", ["created_at"])

    # --- subscriptions ---
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tier", _subscriptiontier, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("ai_requests_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_request_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])

    # --- payments ---
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tier", _paymenttier, nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("screenshot_file_id", sa.String(255), nullable=True),
        sa.Column("status", _paymentstatus, nullable=False, server_default="pending"),
        sa.Column("processed_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["processed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("subscriptions")
    op.drop_table("user_sessions")
    op.drop_table("workouts")
    op.drop_table("swim_profiles")
    op.drop_table("users")

    op.execute("DROP TYPE paymentstatus")
    op.execute("DROP TYPE paymenttier")
    op.execute("DROP TYPE subscriptiontier")
    op.execute("DROP TYPE workouttype")
    op.execute("DROP TYPE poolsize")
    op.execute("DROP TYPE sessionkm")
    op.execute("DROP TYPE sessionsperweek")
    op.execute("DROP TYPE swimgoal")
    op.execute("DROP TYPE swimlevel")
    op.execute("DROP TYPE userrole")