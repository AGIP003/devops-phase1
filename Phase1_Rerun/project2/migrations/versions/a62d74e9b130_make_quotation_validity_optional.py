"""make quotation validity optional

Revision ID: a62d74e9b130
Revises: f4b8c1d27a60
Create Date: 2026-08-25 12:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a62d74e9b130"
down_revision = "f4b8c1d27a60"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "supplier_quotations",
        "valid_until",
        existing_type=sa.Date(),
        nullable=True,
    )


def downgrade():
    connection = op.get_bind()
    missing_validity_count = connection.execute(
        sa.text(
            "SELECT count(*) FROM supplier_quotations "
            "WHERE valid_until IS NULL"
        )
    ).scalar_one()
    if missing_validity_count:
        raise RuntimeError(
            "Cannot restore required quotation validity while quotations "
            "without a validity date exist. Add dates or delete those rows first."
        )

    op.alter_column(
        "supplier_quotations",
        "valid_until",
        existing_type=sa.Date(),
        nullable=False,
    )
