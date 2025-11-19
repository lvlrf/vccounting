"""Add customer models and multi-group resellers

Revision ID: 001_initial_migration
Revises:
Create Date: 2024-11-19 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import uuid

# revision identifiers, used by Alembic.
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('telegram_chat_id', sa.String(50), nullable=True),
        sa.Column('telegram_username', sa.String(50), nullable=True),
        sa.Column('representative_id', sa.UUID(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['representative_id'], ['resellers.id'], ),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_customers_email'), 'customers', ['email'], unique=True)
    op.create_index(op.f('ix_customers_phone'), 'customers', ['phone'], unique=False)

    # 2. Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('customer_id', sa.UUID(), nullable=False),
        sa.Column('plan', sa.Enum('basic', 'pro', 'enterprise', name='subscriptionplan'), nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # 3. Create reseller_group_memberships table (Many-to-Many)
    op.create_table(
        'reseller_group_memberships',
        sa.Column('reseller_id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('reseller_id', 'group_id'),
        sa.ForeignKeyConstraint(['reseller_id'], ['resellers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['group_id'], ['reseller_groups.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # 4. Migrate existing reseller groups to new Many-to-Many table
    # (Only if group_id exists)
    conn = op.get_bind()

    # Check if group_id column exists
    result = conn.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'resellers'
        AND COLUMN_NAME = 'group_id'
    """))
    group_id_exists = result.scalar() > 0

    if group_id_exists:
        # Migrate existing relationships
        conn.execute(sa.text("""
            INSERT INTO reseller_group_memberships (reseller_id, group_id, joined_at)
            SELECT id, group_id, created_at
            FROM resellers
            WHERE group_id IS NOT NULL
        """))

        # Drop the old foreign key and column
        op.drop_constraint('resellers_ibfk_1', 'resellers', type_='foreignkey')
        op.drop_column('resellers', 'group_id')

    # 5. Add referral_code to resellers
    op.add_column('resellers', sa.Column('referral_code', sa.String(20), nullable=True))
    op.create_index(op.f('ix_resellers_referral_code'), 'resellers', ['referral_code'], unique=True)

    # 6. Add customer_id to customer_accounts
    op.add_column('customer_accounts', sa.Column('customer_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_customer_accounts_customer_id'), 'customer_accounts', ['customer_id'], unique=False)
    op.create_foreign_key('fk_customer_accounts_customer', 'customer_accounts', 'customers', ['customer_id'], ['id'])

    # 7. Replace customer_name and customer_note with description
    # Check if columns exist before dropping
    result = conn.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'customer_accounts'
        AND COLUMN_NAME IN ('customer_name', 'customer_note')
    """))
    old_columns_exist = result.scalar() > 0

    if old_columns_exist:
        op.drop_column('customer_accounts', 'customer_name')
        op.drop_column('customer_accounts', 'customer_note')

    # Check if description doesn't exist
    result = conn.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'customer_accounts'
        AND COLUMN_NAME = 'description'
    """))
    description_exists = result.scalar() > 0

    if not description_exists:
        op.add_column('customer_accounts', sa.Column('description', sa.Text(), nullable=True))

    # 8. Add discount fields to product_groups
    op.add_column('product_groups', sa.Column('reseller_discount_percentage', sa.Numeric(5, 2), nullable=False, server_default='0'))
    op.add_column('product_groups', sa.Column('customer_discount_percentage', sa.Numeric(5, 2), nullable=False, server_default='0'))
    op.add_column('product_groups', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))

    # 9. Update PanelType enum to include ovpanel
    # MySQL ENUM modification
    op.execute("""
        ALTER TABLE products
        MODIFY COLUMN panel_type ENUM('marzban', 'remnawave', 'marzneshin', 'ovpanel')
    """)


def downgrade() -> None:
    # Reverse all operations

    # 9. Remove ovpanel from PanelType enum
    op.execute("""
        ALTER TABLE products
        MODIFY COLUMN panel_type ENUM('marzban', 'remnawave', 'marzneshin')
    """)

    # 8. Remove discount fields from product_groups
    op.drop_column('product_groups', 'is_active')
    op.drop_column('product_groups', 'customer_discount_percentage')
    op.drop_column('product_groups', 'reseller_discount_percentage')

    # 7. Restore customer_name and customer_note
    op.drop_column('customer_accounts', 'description')
    op.add_column('customer_accounts', sa.Column('customer_name', sa.String(100), nullable=True))
    op.add_column('customer_accounts', sa.Column('customer_note', sa.Text(), nullable=True))

    # 6. Remove customer_id from customer_accounts
    op.drop_constraint('fk_customer_accounts_customer', 'customer_accounts', type_='foreignkey')
    op.drop_index(op.f('ix_customer_accounts_customer_id'), table_name='customer_accounts')
    op.drop_column('customer_accounts', 'customer_id')

    # 5. Remove referral_code from resellers
    op.drop_index(op.f('ix_resellers_referral_code'), table_name='resellers')
    op.drop_column('resellers', 'referral_code')

    # 4. Restore group_id column (won't restore data)
    op.add_column('resellers', sa.Column('group_id', sa.UUID(), nullable=True))
    op.create_foreign_key('resellers_ibfk_1', 'resellers', 'reseller_groups', ['group_id'], ['id'])

    # 3. Drop reseller_group_memberships table
    op.drop_table('reseller_group_memberships')

    # 2. Drop subscriptions table
    op.drop_table('subscriptions')

    # 1. Drop customers table
    op.drop_index(op.f('ix_customers_phone'), table_name='customers')
    op.drop_index(op.f('ix_customers_email'), table_name='customers')
    op.drop_table('customers')
