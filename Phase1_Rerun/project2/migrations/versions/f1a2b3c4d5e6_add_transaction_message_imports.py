"""add transaction message imports

Revision ID: f1a2b3c4d5e6
Revises: c8f1a4e72b09
Create Date: 2026-08-20 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f1a2b3c4d5e6"
down_revision = "c8f1a4e72b09"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "transaction_imports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("external_reference", sa.String(length=64), nullable=False),
        sa.Column("message_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider_transaction_type", sa.String(length=40), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("fee", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "transaction_id",
            name="uq_transaction_imports_transaction_id",
        ),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            "external_reference",
            name="uq_transaction_imports_user_provider_reference",
        ),
        sa.UniqueConstraint(
            "user_id",
            "message_fingerprint",
            name="uq_transaction_imports_user_fingerprint",
        ),
    )

    # Provider-backed imports need canonical payment methods. Reference-data
    # inserts are idempotent so this also repairs environments seeded manually.
    for method_name in ("m-pesa", "airtel money"):
        op.execute(
            sa.text(
                "INSERT INTO payment_methods (name) "
                "SELECT :method_name "
                "WHERE NOT EXISTS ("
                "SELECT 1 FROM payment_methods WHERE lower(name) = :method_name"
                ")"
            ).bindparams(method_name=method_name)
        )


def downgrade():
    op.drop_table("transaction_imports")
    # Payment methods are deliberately retained: deployed transactions may
    # reference them, and deleting shared reference data is not a safe rollback.
