"""add deleted_at to transactions and create budget list tables

Revision ID: 731c6bd75249
Revises: 
Create Date: 2026-06-27 01:35:30.397930

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '731c6bd75249' #my identity
down_revision = "203a99a228f5" #my parent
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'transactions',
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'budgets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('target_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            'last_used_at',
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=True,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_budgets_user_id', 'budgets', ['user_id'], unique=False)
    op.create_index('idx_budgets_category', 'budgets', ['category'], unique=False)
    op.create_index('idx_budgets_last_used_at', 'budgets', ['last_used_at'], unique=False)

    op.create_table(
        'budget_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('budget_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('estimated_amount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('actual_amount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('checked', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('position', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=True,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(['budget_id'], ['budgets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_budget_items_budget_id', 'budget_items', ['budget_id'], unique=False)
    op.create_index(
        'idx_budget_items_budget_position',
        'budget_items',
        ['budget_id', 'position'],
        unique=False,
    )


def downgrade():
    op.drop_index('idx_budget_items_budget_position', table_name='budget_items')
    op.drop_index('idx_budget_items_budget_id', table_name='budget_items')
    op.drop_table('budget_items')
    op.drop_index('idx_budgets_last_used_at', table_name='budgets')
    op.drop_index('idx_budgets_category', table_name='budgets')
    op.drop_index('idx_budgets_user_id', table_name='budgets')
    op.drop_table('budgets')
    op.drop_column('transactions', 'deleted_at')
