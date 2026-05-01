"""fix role enum uppercase values

Revision ID: 91c5238f4b08
Revises: 1c0674e1ad36
Create Date: 2026-05-01 15:00:00.000000

The original PostgreSQL role enum was created with uppercase values (ADMIN,
PRESIDENT, etc.) matching SQLAlchemy's default behavior of using enum member
names. Previous migrations added vice_president and super_admin in lowercase
which SQLAlchemy cannot use. This migration adds the correct uppercase variants.
"""
from alembic import op


revision = '91c5238f4b08'
down_revision = '1c0674e1ad36'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'VICE_PRESIDENT'")
    op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'SUPER_ADMIN'")


def downgrade():
    # PostgreSQL does not support removing enum values without recreating the type
    pass
