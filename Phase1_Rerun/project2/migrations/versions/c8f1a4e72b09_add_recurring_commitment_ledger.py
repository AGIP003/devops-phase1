"""add recurring commitment ledger

Revision ID: c8f1a4e72b09
Revises: 7a6c9f3b2d10
Create Date: 2026-08-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c8f1a4e72b09"
down_revision = "7a6c9f3b2d10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recurring_commitments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=120), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("amount_kind", sa.String(length=20), server_default="fixed", nullable=False),
        sa.Column("currency_code", sa.String(length=3), server_default="KES", nullable=False),
        sa.Column("next_due_date", sa.Date(), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column("custom_interval_days", sa.SmallInteger(), nullable=True),
        sa.Column("recurrence_anchor_day", sa.SmallInteger(), nullable=False),
        sa.Column("auto_renews", sa.Boolean(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_via", sa.String(length=32), server_default="manual", nullable=False),
        sa.Column("external_reference", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("kind IN ('bill', 'subscription')", name="ck_recurring_commitments_kind"),
        sa.CheckConstraint("amount > 0", name="ck_recurring_commitments_amount"),
        sa.CheckConstraint("amount_kind IN ('fixed', 'estimated')", name="ck_recurring_commitments_amount_kind"),
        sa.CheckConstraint(
            "frequency IN ('weekly', 'monthly', 'quarterly', 'termly', 'yearly', 'custom')",
            name="ck_recurring_commitments_frequency",
        ),
        sa.CheckConstraint(
            "(frequency = 'custom' AND custom_interval_days IS NOT NULL AND custom_interval_days > 0) OR "
            "(frequency <> 'custom' AND custom_interval_days IS NULL)",
            name="ck_recurring_commitments_custom_interval",
        ),
        sa.CheckConstraint("status IN ('active', 'cancelled')", name="ck_recurring_commitments_status"),
        sa.CheckConstraint("recurrence_anchor_day BETWEEN 1 AND 31", name="ck_recurring_commitments_anchor_day"),
        sa.CheckConstraint(
            "(kind = 'subscription' AND auto_renews IS NOT NULL) OR "
            "(kind = 'bill' AND auto_renews IS NULL)",
            name="ck_recurring_commitments_auto_renews",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "created_via",
            "external_reference",
            name="uq_recurring_commitments_user_source_reference",
        ),
    )
    op.create_index(
        "idx_recurring_commitments_user_due",
        "recurring_commitments",
        ["user_id", "status", "next_due_date"],
        unique=False,
    )

    op.create_table(
        "commitment_occurrences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("commitment_id", sa.Integer(), nullable=False),
        sa.Column("resolution", sa.String(length=20), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("expected_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("actual_amount", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("resolved_on", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_via", sa.String(length=32), server_default="manual", nullable=False),
        sa.Column("external_reference", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("resolution IN ('paid', 'skipped')", name="ck_commitment_occurrences_resolution"),
        sa.CheckConstraint("expected_amount > 0", name="ck_commitment_occurrences_expected_amount"),
        sa.CheckConstraint(
            "(resolution = 'paid' AND actual_amount IS NOT NULL AND actual_amount > 0) OR "
            "(resolution = 'skipped' AND actual_amount IS NULL)",
            name="ck_commitment_occurrences_actual_amount",
        ),
        sa.ForeignKeyConstraint(
            ["commitment_id"],
            ["recurring_commitments.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "commitment_id",
            "created_via",
            "external_reference",
            name="uq_commitment_occurrences_source_reference",
        ),
    )
    op.create_index(
        "idx_commitment_occurrences_commitment_due",
        "commitment_occurrences",
        ["commitment_id", "due_date"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "idx_commitment_occurrences_commitment_due",
        table_name="commitment_occurrences",
    )
    op.drop_table("commitment_occurrences")
    op.drop_index(
        "idx_recurring_commitments_user_due",
        table_name="recurring_commitments",
    )
    op.drop_table("recurring_commitments")
