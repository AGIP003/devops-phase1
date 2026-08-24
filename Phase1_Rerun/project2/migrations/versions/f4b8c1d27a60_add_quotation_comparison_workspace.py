"""add quotation comparison workspace

Revision ID: f4b8c1d27a60
Revises: d3e7a91c4f20
Create Date: 2026-08-24 15:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f4b8c1d27a60"
down_revision = "d3e7a91c4f20"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "quotation_projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "currency_code",
            sa.String(length=3),
            server_default=sa.text("'KES'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=24),
            server_default=sa.text("'comparing'"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('comparing', 'supplier_selected', 'archived')",
            name="ck_quotation_projects_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_quotation_projects_user_updated",
        "quotation_projects",
        ["user_id", "updated_at"],
        unique=False,
    )

    op.create_table(
        "quotation_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_quotation_items_quantity_positive",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["quotation_projects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "name",
            name="uq_quotation_items_project_name",
        ),
    )
    op.create_index(
        "idx_quotation_items_project_position",
        "quotation_items",
        ["project_id", "position"],
        unique=False,
    )

    op.create_table(
        "supplier_quotations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("supplier", sa.String(length=100), nullable=False),
        sa.Column("contact", sa.String(length=100), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column(
            "delivery_cost",
            sa.Numeric(precision=12, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "discount",
            sa.Numeric(precision=12, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "tax_mode",
            sa.String(length=12),
            server_default=sa.text("'included'"),
            nullable=False,
        ),
        sa.Column(
            "tax_rate",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("delivery_days", sa.Integer(), nullable=True),
        sa.Column("payment_terms", sa.String(length=150), nullable=True),
        sa.Column(
            "preferred",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "delivery_cost >= 0",
            name="ck_supplier_quotations_delivery_cost",
        ),
        sa.CheckConstraint(
            "delivery_days IS NULL OR delivery_days >= 0",
            name="ck_supplier_quotations_delivery_days",
        ),
        sa.CheckConstraint(
            "discount >= 0",
            name="ck_supplier_quotations_discount",
        ),
        sa.CheckConstraint(
            "tax_mode IN ('included', 'excluded', 'none')",
            name="ck_supplier_quotations_tax_mode",
        ),
        sa.CheckConstraint(
            "tax_rate >= 0",
            name="ck_supplier_quotations_tax_rate",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["quotation_projects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "supplier",
            name="uq_supplier_quotations_project_supplier",
        ),
    )
    op.create_index(
        "idx_supplier_quotations_project_id",
        "supplier_quotations",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "uq_supplier_quotations_one_preferred",
        "supplier_quotations",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("preferred = true"),
    )

    op.create_table(
        "supplier_quotation_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "unit_price >= 0",
            name="ck_supplier_quotation_prices_price",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["quotation_items.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["quotation_id"],
            ["supplier_quotations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "quotation_id",
            "item_id",
            name="uq_supplier_quotation_prices_quote_item",
        ),
    )
    op.create_index(
        "idx_supplier_quotation_prices_item_id",
        "supplier_quotation_prices",
        ["item_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "idx_supplier_quotation_prices_item_id",
        table_name="supplier_quotation_prices",
    )
    op.drop_table("supplier_quotation_prices")
    op.drop_index(
        "uq_supplier_quotations_one_preferred",
        table_name="supplier_quotations",
    )
    op.drop_index(
        "idx_supplier_quotations_project_id",
        table_name="supplier_quotations",
    )
    op.drop_table("supplier_quotations")
    op.drop_index(
        "idx_quotation_items_project_position",
        table_name="quotation_items",
    )
    op.drop_table("quotation_items")
    op.drop_index(
        "idx_quotation_projects_user_updated",
        table_name="quotation_projects",
    )
    op.drop_table("quotation_projects")
