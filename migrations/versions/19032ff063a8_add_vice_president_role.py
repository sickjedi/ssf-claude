"""add vice_president role

Revision ID: 19032ff063a8
Revises: a3ffbc91129e
Create Date: 2026-04-21 10:05:23.771209

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '19032ff063a8'
down_revision = 'a3ffbc91129e'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE role ADD VALUE 'vice_president'")


def downgrade():
    # PostgreSQL does not support removing enum values; a full recreate would be needed
    pass
