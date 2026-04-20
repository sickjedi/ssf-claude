"""add member fields

Revision ID: 4247ae759bc0
Revises: caa961e9693d
Create Date: 2026-04-20 13:49:01.143966

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4247ae759bc0'
down_revision = 'caa961e9693d'
branch_labels = None
depends_on = None


def upgrade():
    # Add NOT NULL columns with a temporary server_default to handle existing rows,
    # then remove the default so the constraint is enforced going forward.
    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.add_column(sa.Column('oib', sa.String(length=11), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('date_of_birth', sa.Date(), nullable=False, server_default='1900-01-01'))
        batch_op.add_column(sa.Column('address', sa.String(length=255), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('phone', sa.String(length=50), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('email_address', sa.String(length=255), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('gdpr', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
        batch_op.add_column(sa.Column('end_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('end_reason', sa.String(length=500), nullable=True))
        batch_op.create_unique_constraint('uq_members_oib', ['oib'])

    # Drop server defaults so application code is responsible for providing values
    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.alter_column('oib', server_default=None)
        batch_op.alter_column('date_of_birth', server_default=None)
        batch_op.alter_column('address', server_default=None)
        batch_op.alter_column('phone', server_default=None)
        batch_op.alter_column('email_address', server_default=None)
        batch_op.alter_column('gdpr', server_default=None)
        batch_op.alter_column('is_active', server_default=None)


def downgrade():
    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.drop_constraint('uq_members_oib', type_='unique')
        batch_op.drop_column('end_reason')
        batch_op.drop_column('end_date')
        batch_op.drop_column('is_active')
        batch_op.drop_column('gdpr')
        batch_op.drop_column('email_address')
        batch_op.drop_column('phone')
        batch_op.drop_column('address')
        batch_op.drop_column('date_of_birth')
        batch_op.drop_column('oib')
