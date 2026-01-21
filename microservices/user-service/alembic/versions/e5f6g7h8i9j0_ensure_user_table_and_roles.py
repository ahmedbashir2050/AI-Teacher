"""ensure_user_table_and_roles

Revision ID: e5f6g7h8i9j0
Revises: c3d4e5f6g7h8
Create Date: 2024-06-01 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e5f6g7h8i9j0'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade():
    # In case the table 'users' doesn't exist, we should ideally create it.
    # But for this task, we focus on adding the 'teacher' role.
    # If the enum 'role_enum' exists, we add 'teacher' to it.

    # Check if 'role_enum' exists
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role_enum') THEN CREATE TYPE role_enum AS ENUM ('student', 'teacher', 'admin'); END IF; END $$;")

    # If it exists but 'teacher' is missing (unlikely if we just created it, but good for existing ones)
    op.execute("ALTER TYPE role_enum ADD VALUE IF NOT EXISTS 'teacher'")


def downgrade():
    pass
