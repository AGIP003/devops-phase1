"""add finance analytics provenance

Revision ID: d3e7a91c4f20
Revises: b6d8e4a19c20
Create Date: 2026-08-23 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d3e7a91c4f20"
down_revision = "b6d8e4a19c20"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "transactions",
        sa.Column("merchant_name", sa.String(length=150), nullable=True),
    )
    op.add_column(
        "transaction_imports",
        sa.Column(
            "fee_source",
            sa.String(length=24),
            server_default="unknown",
            nullable=False,
        ),
    )
    op.add_column(
        "transaction_imports",
        sa.Column(
            "original_estimated_fee",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
    )
    op.add_column(
        "transaction_imports",
        sa.Column("fee_tariff_version", sa.String(length=64), nullable=True),
    )
    op.create_check_constraint(
        "ck_transaction_imports_fee_source",
        "transaction_imports",
        "fee_source IN ('unknown', 'provider_reported', "
        "'estimated_tariff', 'user_confirmed')",
    )
    op.execute(
        sa.text(
            "UPDATE transaction_imports "
            "SET fee_source = CASE "
            "WHEN fee IS NULL THEN 'unknown' "
            "ELSE 'provider_reported' END"
        )
    )

    op.create_table(
        "provider_financing_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("external_reference", sa.String(length=64), nullable=False),
        sa.Column("message_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=24), nullable=False),
        sa.Column(
            "principal_amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column(
            "financing_fee",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "daily_maintenance_fee",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "outstanding_amount",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_on", sa.Date(), nullable=False),
        sa.Column("settled_in_full", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "event_type IN ('draw', 'repayment')",
            name="ck_provider_financing_events_type",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "message_fingerprint",
            name="uq_provider_financing_events_fingerprint",
        ),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            "external_reference",
            "event_type",
            name="uq_provider_financing_events_reference",
        ),
    )
    op.create_index(
        "idx_provider_financing_events_user_date",
        "provider_financing_events",
        ["user_id", "recorded_on"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "idx_provider_financing_events_user_date",
        table_name="provider_financing_events",
    )
    op.drop_table("provider_financing_events")
    op.drop_constraint(
        "ck_transaction_imports_fee_source",
        "transaction_imports",
        type_="check",
    )
    op.drop_column("transaction_imports", "fee_tariff_version")
    op.drop_column("transaction_imports", "original_estimated_fee")
    op.drop_column("transaction_imports", "fee_source")
    op.drop_column("transactions", "merchant_name")
