"""add savings goal ledger

Revision ID: 7a6c9f3b2d10
Revises: 4d2a8c7e91f0
Create Date: 2026-08-16 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "7a6c9f3b2d10"
down_revision = "4d2a8c7e91f0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "savings_goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("target_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("contribution_frequency", sa.String(length=20), nullable=False),
        sa.Column("currency_code", sa.String(length=3), server_default="KES", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_via", sa.String(length=32), server_default="manual", nullable=False),
        sa.Column("external_reference", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("target_amount > 0", name="ck_savings_goals_target_amount"),
        sa.CheckConstraint(
            "contribution_frequency IN ('weekly', 'fortnightly', 'monthly')",
            name="ck_savings_goals_frequency",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "created_via",
            "external_reference",
            name="uq_savings_goals_user_source_reference",
        ),
    )
    op.create_index(
        "idx_savings_goals_user_target",
        "savings_goals",
        ["user_id", "target_date"],
        unique=False,
    )

    op.create_table(
        "savings_goal_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("entry_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_via", sa.String(length=32), server_default="manual", nullable=False),
        sa.Column("external_reference", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "entry_type IN ('contribution', 'withdrawal')",
            name="ck_savings_goal_entries_type",
        ),
        sa.CheckConstraint("amount > 0", name="ck_savings_goal_entries_amount"),
        sa.ForeignKeyConstraint(
            ["goal_id"],
            ["savings_goals.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "goal_id",
            "created_via",
            "external_reference",
            name="uq_savings_goal_entries_source_reference",
        ),
    )
    op.create_index(
        "idx_savings_goal_entries_goal_date",
        "savings_goal_entries",
        ["goal_id", "occurred_on"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "idx_savings_goal_entries_goal_date",
        table_name="savings_goal_entries",
    )
    op.drop_table("savings_goal_entries")
    op.drop_index("idx_savings_goals_user_target", table_name="savings_goals")
    op.drop_table("savings_goals")
