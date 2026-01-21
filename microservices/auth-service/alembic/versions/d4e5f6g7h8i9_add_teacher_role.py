"""add_teacher_role

Revision ID: d4e5f6g7h8i9
Revises: 4d3c2b1a0e9f
Create Date: 2024-06-01 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd4e5f6g7h8i9'
down_revision = '4d3c2b1a0e9f'
branch_labels = None
depends_on = None


def upgrade():
    # Adding 'TEACHER' to RoleEnum. In Postgres, this is done via ALTER TYPE.
    # Note: This is specific to Postgres.
    op.execute("ALTER TYPE roleenum ADD VALUE 'TEACHER'")


def downgrade():
    # Removing a value from an Enum is not supported by Postgres ALTER TYPE.
    # Usually, one would have to rename the type, create a new one, and swap.
    # For a downgrade, we can just leave it as is or do nothing.
    pass
