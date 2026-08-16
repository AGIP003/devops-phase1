"""add debt tracking ledger

Revision ID: 4d2a8c7e91f0
Revises: e7b4c2d19a60
Create Date: 2026-08-16 18:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "4d2a8c7e91f0"
down_revision = "e7b4c2d19a60"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "debts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=140), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("counterparty", sa.String(length=100), nullable=True),
        sa.Column(
            "currency_code",
            sa.String(length=3),
            server_default="KES",
            nullable=False,
        ),
        sa.Column("tracking_kind", sa.String(length=12), nullable=False),
        sa.Column("original_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("opening_balance", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "amount_repaid_before_tracking",
            sa.Numeric(14, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("opened_on", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("stated_interest_rate", sa.Numeric(8, 4), nullable=True),
        sa.Column(
            "has_interest",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("interest_period", sa.String(length=20), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "created_via",
            sa.String(length=32),
            server_default="manual",
            nullable=False,
        ),
        sa.Column("external_reference", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "direction IN ('i_owe', 'owed_to_me')",
            name="ck_debts_direction",
        ),
        sa.CheckConstraint(
            "tracking_kind IN ('new', 'existing')",
            name="ck_debts_tracking_kind",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'settled', 'written_off', 'cancelled')",
            name="ck_debts_status",
        ),
        sa.CheckConstraint("opening_balance >= 0", name="ck_debts_opening_balance"),
        sa.CheckConstraint(
            "original_amount IS NULL OR original_amount > 0",
            name="ck_debts_original_amount",
        ),
        sa.CheckConstraint(
            "amount_repaid_before_tracking >= 0",
            name="ck_debts_prior_repayment",
        ),
        sa.CheckConstraint(
            "stated_interest_rate IS NULL OR stated_interest_rate > 0",
            name="ck_debts_interest_rate",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "created_via",
            "external_reference",
            name="uq_debts_user_source_reference",
        ),
    )
    op.create_index("idx_debts_user_status", "debts", ["user_id", "status"])
    op.create_index("idx_debts_user_created", "debts", ["user_id", "created_at"])

    op.create_table(
        "debt_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("debt_id", sa.Integer(), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column("interval_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("installment_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("next_due_date", sa.Date(), nullable=False),
        sa.Column("final_due_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "frequency IN ('one_time', 'daily', 'weekly', 'monthly')",
            name="ck_debt_schedules_frequency",
        ),
        sa.CheckConstraint("interval_count > 0", name="ck_debt_schedules_interval"),
        sa.CheckConstraint(
            "installment_amount IS NULL OR installment_amount > 0",
            name="ck_debt_schedules_installment",
        ),
        sa.ForeignKeyConstraint(["debt_id"], ["debts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("debt_id", name="uq_debt_schedules_debt_id"),
    )
    op.create_index(
        "idx_debt_schedules_next_due",
        "debt_schedules",
        ["next_due_date"],
    )

    op.create_table(
        "debt_fee_terms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("debt_id", sa.Integer(), nullable=False),
        sa.Column("fee_category", sa.String(length=32), nullable=False),
        sa.Column("custom_fee_name", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "fee_category IN ('processing', 'origination', 'late_payment', "
            "'insurance', 'service', 'restructuring', 'legal_collection', 'other')",
            name="ck_debt_fee_terms_category",
        ),
        sa.CheckConstraint(
            "fee_category <> 'other' OR custom_fee_name IS NOT NULL",
            name="ck_debt_fee_terms_other_name",
        ),
        sa.ForeignKeyConstraint(["debt_id"], ["debts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "debt_id",
            "fee_category",
            "custom_fee_name",
            name="uq_debt_fee_terms_debt_category_name",
        ),
    )
    op.create_index("idx_debt_fee_terms_debt_id", "debt_fee_terms", ["debt_id"])

    op.create_table(
        "debt_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("debt_id", sa.Integer(), nullable=False),
        sa.Column("entry_type", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("fee_category", sa.String(length=32), nullable=True),
        sa.Column("custom_fee_name", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("transaction_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_via",
            sa.String(length=32),
            server_default="manual",
            nullable=False,
        ),
        sa.Column("external_reference", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "entry_type IN ('repayment', 'interest', 'fee', "
            "'adjustment_increase', 'adjustment_decrease')",
            name="ck_debt_entries_type",
        ),
        sa.CheckConstraint("amount > 0", name="ck_debt_entries_amount"),
        sa.CheckConstraint(
            "fee_category IS NULL OR fee_category IN "
            "('processing', 'origination', 'late_payment', 'insurance', "
            "'service', 'restructuring', 'legal_collection', 'other')",
            name="ck_debt_entries_fee_category",
        ),
        sa.CheckConstraint(
            "entry_type <> 'fee' OR fee_category IS NOT NULL",
            name="ck_debt_entries_fee_required",
        ),
        sa.CheckConstraint(
            "entry_type = 'fee' OR "
            "(fee_category IS NULL AND custom_fee_name IS NULL)",
            name="ck_debt_entries_fee_fields",
        ),
        sa.CheckConstraint(
            "fee_category <> 'other' OR custom_fee_name IS NOT NULL",
            name="ck_debt_entries_other_fee_name",
        ),
        sa.ForeignKeyConstraint(["debt_id"], ["debts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_id", name="uq_debt_entries_transaction_id"),
        sa.UniqueConstraint(
            "debt_id",
            "created_via",
            "external_reference",
            name="uq_debt_entries_source_reference",
        ),
    )
    op.create_index(
        "idx_debt_entries_debt_date",
        "debt_entries",
        ["debt_id", "occurred_on"],
    )


def downgrade():
    op.drop_index("idx_debt_entries_debt_date", table_name="debt_entries")
    op.drop_table("debt_entries")
    op.drop_index("idx_debt_fee_terms_debt_id", table_name="debt_fee_terms")
    op.drop_table("debt_fee_terms")
    op.drop_index("idx_debt_schedules_next_due", table_name="debt_schedules")
    op.drop_table("debt_schedules")
    op.drop_index("idx_debts_user_created", table_name="debts")
    op.drop_index("idx_debts_user_status", table_name="debts")
    op.drop_table("debts")
