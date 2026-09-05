"""add transfer classification and provider flow

Revision ID: e9b1f0a4c673
Revises: c2f7a19d3e84
Create Date: 2026-09-06 01:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e9b1f0a4c673"
down_revision = "c2f7a19d3e84"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    unexpected_types = connection.execute(
        sa.text(
            "SELECT DISTINCT type FROM categories "
            "WHERE type NOT IN ('income', 'expense')"
        )
    ).scalars().all()
    if unexpected_types:
        raise RuntimeError(
            "Cannot add the transaction-type constraint until unexpected "
            f"category types are reviewed: {sorted(unexpected_types)}"
        )

    # A category name such as "Loan" can legitimately be used for both an
    # inflow and an outflow. Type is therefore part of its identity.
    op.drop_constraint(
        "categories_user_id_name_key",
        "categories",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_categories_user_name_type",
        "categories",
        ["user_id", "name", "type"],
    )
    op.create_check_constraint(
        "ck_categories_type",
        "categories",
        "type IN ('income', 'expense', 'transfer')",
    )

    # Keep provider-observed movement separate from the user's reporting
    # classification. Existing imports are backfilled from stable transaction
    # types because raw provider messages were intentionally never retained.
    op.add_column(
        "transaction_imports",
        sa.Column("provider_flow", sa.String(length=16), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE transaction_imports "
            "SET provider_flow = CASE "
            "WHEN provider_transaction_type = 'received_money' "
            "THEN 'money_in' ELSE 'money_out' END"
        )
    )
    op.alter_column(
        "transaction_imports",
        "provider_flow",
        existing_type=sa.String(length=16),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_transaction_imports_provider_flow",
        "transaction_imports",
        "provider_flow IN ('money_in', 'money_out')",
    )


def downgrade():
    connection = op.get_bind()
    duplicate_count = connection.execute(
        sa.text(
            "SELECT count(*) FROM ("
            "SELECT user_id, name FROM categories "
            "GROUP BY user_id, name HAVING count(*) > 1"
            ") AS category_name_collisions"
        )
    ).scalar_one()
    if duplicate_count:
        raise RuntimeError(
            "Cannot restore the old category constraint while category names "
            "are used by more than one transaction type."
        )

    op.drop_constraint(
        "ck_transaction_imports_provider_flow",
        "transaction_imports",
        type_="check",
    )
    op.drop_column("transaction_imports", "provider_flow")
    op.drop_constraint(
        "uq_categories_user_name_type",
        "categories",
        type_="unique",
    )
    op.drop_constraint(
        "ck_categories_type",
        "categories",
        type_="check",
    )
    op.create_unique_constraint(
        "categories_user_id_name_key",
        "categories",
        ["user_id", "name"],
    )
