"""add multitenancy

Revision ID: 1c0674e1ad36
Revises: 7fbf65a5f5a9
Create Date: 2026-05-01 14:50:21.555897

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c0674e1ad36'
down_revision = '7fbf65a5f5a9'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Add super_admin to Role enum
    op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'super_admin'")

    # 2. Create organisations table
    op.create_table(
        'organisations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('oib', sa.String(length=11), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('iban', sa.String(length=34), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('oib'),
    )

    # 3. Seed first org from existing settings row (read before dropping settings)
    row = conn.execute(sa.text(
        "SELECT name, oib, address, city, iban FROM settings LIMIT 1"
    )).fetchone()

    if row and row.oib:
        conn.execute(sa.text(
            "INSERT INTO organisations (name, oib, address, city, iban, is_active) "
            "VALUES (:name, :oib, :address, :city, :iban, true)"
        ), {
            'name': row.name or 'Default Organisation',
            'oib': row.oib,
            'address': row.address,
            'city': row.city,
            'iban': row.iban,
        })
    else:
        # No settings row or no OIB — insert a placeholder
        conn.execute(sa.text(
            "INSERT INTO organisations (name, oib, is_active) "
            "VALUES ('Default Organisation', '00000000000', true)"
        ))

    first_org_id = conn.execute(sa.text("SELECT id FROM organisations LIMIT 1")).scalar()

    # 4. Drop settings now that data has been migrated
    op.drop_table('settings')

    # 5. Add nullable organisation_id columns to all tenant-scoped tables
    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organisation_id', sa.Integer(), nullable=True))

    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organisation_id', sa.Integer(), nullable=True))

    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organisation_id', sa.Integer(), nullable=True))

    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organisation_id', sa.Integer(), nullable=True))

    # 6. Backfill all existing rows to the first org
    for table in ('members', 'customers', 'invoices', 'items'):
        conn.execute(sa.text(f'UPDATE {table} SET organisation_id = :id'), {'id': first_org_id})

    # 7. Make organisation_id NOT NULL, drop old global unique constraints,
    #    add FK constraints and per-org composite unique constraints

    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.alter_column('organisation_id', nullable=False)
        batch_op.drop_constraint('uq_members_oib', type_='unique')
        batch_op.drop_constraint('members_email_address_key', type_='unique')
        batch_op.create_foreign_key('fk_members_organisation', 'organisations', ['organisation_id'], ['id'])
        batch_op.create_unique_constraint('uq_members_org_oib', ['organisation_id', 'oib'])
        batch_op.create_unique_constraint('uq_members_org_email', ['organisation_id', 'email_address'])

    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.alter_column('organisation_id', nullable=False)
        batch_op.drop_constraint('customers_company_name_key', type_='unique')
        batch_op.drop_constraint('customers_company_oib_key', type_='unique')
        batch_op.create_foreign_key('fk_customers_organisation', 'organisations', ['organisation_id'], ['id'])
        batch_op.create_unique_constraint('uq_customers_org_company_name', ['organisation_id', 'company_name'])
        batch_op.create_unique_constraint('uq_customers_org_company_oib', ['organisation_id', 'company_oib'])

    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.alter_column('organisation_id', nullable=False)
        batch_op.drop_constraint('invoices_invoice_number_key', type_='unique')
        batch_op.create_foreign_key('fk_invoices_organisation', 'organisations', ['organisation_id'], ['id'])
        batch_op.create_unique_constraint('uq_invoices_org_number', ['organisation_id', 'invoice_number'])

    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.alter_column('organisation_id', nullable=False)
        batch_op.create_foreign_key('fk_items_organisation', 'organisations', ['organisation_id'], ['id'])

    # 8. Make users.member_id nullable (super_admin users have no member record)
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('member_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('member_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)

    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.drop_constraint('fk_items_organisation', type_='foreignkey')
        batch_op.drop_column('organisation_id')

    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.drop_constraint('fk_invoices_organisation', type_='foreignkey')
        batch_op.drop_constraint('uq_invoices_org_number', type_='unique')
        batch_op.create_unique_constraint('invoices_invoice_number_key', ['invoice_number'])
        batch_op.drop_column('organisation_id')

    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.drop_constraint('fk_customers_organisation', type_='foreignkey')
        batch_op.drop_constraint('uq_customers_org_company_name', type_='unique')
        batch_op.drop_constraint('uq_customers_org_company_oib', type_='unique')
        batch_op.create_unique_constraint('customers_company_name_key', ['company_name'])
        batch_op.create_unique_constraint('customers_company_oib_key', ['company_oib'])
        batch_op.drop_column('organisation_id')

    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.drop_constraint('fk_members_organisation', type_='foreignkey')
        batch_op.drop_constraint('uq_members_org_oib', type_='unique')
        batch_op.drop_constraint('uq_members_org_email', type_='unique')
        batch_op.create_unique_constraint('uq_members_oib', ['oib'])
        batch_op.create_unique_constraint('members_email_address_key', ['email_address'])
        batch_op.drop_column('organisation_id')

    op.create_table(
        'settings',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('address', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('city', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.Column('oib', sa.VARCHAR(length=11), autoincrement=False, nullable=True),
        sa.Column('iban', sa.VARCHAR(length=34), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('id', name='settings_pkey'),
    )
    op.drop_table('organisations')
