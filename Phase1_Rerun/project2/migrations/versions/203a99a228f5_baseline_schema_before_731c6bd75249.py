"""baseline schema before 731c6bd75249

Revision ID: 203a99a228f5
Revises: 
Create Date: 2026-07-28 00:47:00.582215

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '203a99a228f5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False, unique=True),
        sa.Column('email', sa.String(length=100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
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
        sa.Column('role', sa.String(length=20), nullable=True, server_default=sa.text(
            "'user'")),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('telegram_id', sa.BigInteger(), nullable=True, unique=True)
    )

    op.create_table(
        'payment_method_groups',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True)
    )

    op.create_table(
        'payment_methods',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['payment_method_groups.id'])
    )

    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'name', name='categories_user_id_name_key')
    )
    op.create_index('idx_categories_user_id', 'categories', ['user_id'], unique=False)

    op.create_table(
        'telegram_link_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('token', sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            'expires_at',
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column('used', sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete='CASCADE',
        ),
    )
    op.create_index(
        "idx_telegram_link_tokens_user_id",
        "telegram_link_tokens",
        ["user_id"],
        unique=False,
    )

    #Partial index stores only rows satisfying the condition. used tokens are excluded, makes lookup smaller
    op.create_index(
        "idx_telegram_link_tokens_active",
        "telegram_link_tokens",
        ["token"],
        unique=False,
        postgresql_where=sa.text("used = false"),
    )

    op.create_table(
        'telegram_user_preferences',
        sa.Column('user_id', sa.Integer(),primary_key=True),
        sa.Column('default_payment_method', sa.String(length=50), nullable=False, server_default=sa.text("'m-pesa'")),
        sa.Column('category_aliases', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),      
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
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
        sa.Column('payment_method_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['payment_method_id'], ['payment_methods.id']),
    )
    op.create_index('idx_transactions_user_id', 'transactions', ['user_id'], unique=False)
    op.create_index(
        'idx_transactions_category_id',
        'transactions',
        ['category_id'],
        unique=False,
    )
    op.create_index('idx_transactions_date', 'transactions', ['date'], unique=False)
    op.create_index('idx_transactions_user_date', 'transactions', ['user_id', 'date'], unique=False)


def downgrade():
    op.drop_index('idx_transactions_user_date', table_name='transactions')
    op.drop_index('idx_transactions_date', table_name='transactions')
    op.drop_index('idx_transactions_category_id', table_name='transactions')
    op.drop_index('idx_transactions_user_id', table_name='transactions')
    op.drop_table('transactions')
    op.drop_table('telegram_user_preferences')
    op.drop_index('idx_telegram_link_tokens_active', table_name='telegram_link_tokens')
    op.drop_index('idx_telegram_link_tokens_user_id', table_name='telegram_link_tokens')
    op.drop_table('telegram_link_tokens')
    op.drop_index('idx_categories_user_id', table_name='categories')
    op.drop_table('categories')
    op.drop_table('payment_methods')
    op.drop_table('payment_method_groups')
    op.drop_table('users')
