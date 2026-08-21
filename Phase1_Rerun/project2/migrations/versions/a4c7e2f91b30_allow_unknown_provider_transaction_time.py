"""allow unknown provider transaction time

Revision ID: a4c7e2f91b30
Revises: f1a2b3c4d5e6
Create Date: 2026-08-21 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a4c7e2f91b30"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "transaction_imports",
        "occurred_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )


def downgrade():
    connection = op.get_bind()
    unknown_time_count = connection.execute(
        sa.text(
            "SELECT count(*) FROM transaction_imports "
            "WHERE occurred_at IS NULL"
        )
    ).scalar_one()
    if unknown_time_count:
        raise RuntimeError(
            "Cannot require provider timestamps while imported messages "
            "with unknown provider times exist."
        )

    op.alter_column(
        "transaction_imports",
        "occurred_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )

