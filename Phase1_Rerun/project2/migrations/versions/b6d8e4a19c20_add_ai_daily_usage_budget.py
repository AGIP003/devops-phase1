"""add aggregate AI daily usage budget

Revision ID: b6d8e4a19c20
Revises: a4c7e2f91b30
Create Date: 2026-08-22 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b6d8e4a19c20"
down_revision = "a4c7e2f91b30"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_daily_usage",
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column(
            "reserved_cost_usd",
            sa.Numeric(precision=12, scale=8),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "estimated_cost_usd",
            sa.Numeric(precision=12, scale=8),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "input_tokens",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "cached_input_tokens",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "output_tokens",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "completed_requests",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "failed_requests",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "reserved_cost_usd >= 0",
            name="ck_ai_daily_usage_reserved_nonnegative",
        ),
        sa.CheckConstraint(
            "estimated_cost_usd >= 0",
            name="ck_ai_daily_usage_estimated_nonnegative",
        ),
        sa.PrimaryKeyConstraint("usage_date"),
    )


def downgrade():
    op.drop_table("ai_daily_usage")
