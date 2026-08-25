"""add persistent NSE market-data cache

Revision ID: c2f7a19d3e84
Revises: a62d74e9b130
Create Date: 2026-08-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c2f7a19d3e84"
down_revision = "a62d74e9b130"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "nse_market_cache",
        sa.Column("cache_key", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("cache_key"),
    )


def downgrade():
    op.drop_table("nse_market_cache")
