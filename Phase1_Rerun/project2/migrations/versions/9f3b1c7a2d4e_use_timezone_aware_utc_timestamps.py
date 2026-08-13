"""use timezone-aware UTC timestamps

Revision ID: 9f3b1c7a2d4e
Revises: 731c6bd75249
Create Date: 2026-08-13

Existing timestamp-without-time-zone values are interpreted as UTC. This
preserves the instant represented by data written under the application's
previous naive-UTC convention.
"""

from alembic import op
import sqlalchemy as sa


revision = "9f3b1c7a2d4e"
down_revision = "731c6bd75249"
branch_labels = None
depends_on = None


TIMESTAMP_COLUMNS = (
    ("users", "created_at", True),
    ("users", "updated_at", True),
    ("users", "last_login", True),
    ("categories", "created_at", True),
    ("telegram_link_tokens", "expires_at", False),
    ("telegram_link_tokens", "created_at", True),
    ("telegram_user_preferences", "updated_at", False),
    ("transactions", "created_at", True),
    ("transactions", "updated_at", True),
    ("transactions", "deleted_at", True),
    ("budgets", "last_used_at", True),
    ("budgets", "created_at", True),
    ("budgets", "updated_at", True),
    ("budget_items", "created_at", True),
    ("budget_items", "updated_at", True),
)


def upgrade():
    for table_name, column_name, nullable in TIMESTAMP_COLUMNS:
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=nullable,
            postgresql_using=f"{column_name} AT TIME ZONE 'UTC'",
        )


def downgrade():
    for table_name, column_name, nullable in reversed(TIMESTAMP_COLUMNS):
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=nullable,
            postgresql_using=f"{column_name} AT TIME ZONE 'UTC'",
        )
