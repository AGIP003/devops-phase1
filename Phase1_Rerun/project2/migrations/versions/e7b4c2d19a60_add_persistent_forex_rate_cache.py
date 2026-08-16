"""add persistent forex rate cache

Revision ID: e7b4c2d19a60
Revises: bf093d91b73e
Create Date: 2026-08-16 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e7b4c2d19a60"
down_revision = "bf093d91b73e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "forex_rates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("quote_currency", sa.String(length=3), nullable=False),
        sa.Column("rate", sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column("rate_date", sa.Date(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "base_currency",
            "quote_currency",
            "rate_date",
            name="uq_forex_rates_provider_pair_date",
        ),
    )
    op.create_index(
        "idx_forex_rates_provider_base_date",
        "forex_rates",
        ["provider", "base_currency", "rate_date"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "idx_forex_rates_provider_base_date",
        table_name="forex_rates",
    )
    op.drop_table("forex_rates")
