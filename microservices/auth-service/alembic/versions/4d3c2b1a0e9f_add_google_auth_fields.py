"""add google auth fields

Revision ID: 4d3c2b1a0e9f
Revises: e2ca5dabb130
Create Date: 2026-01-20 10:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d3c2b1a0e9f"
down_revision: Union[str, Sequence[str], None] = "e2ca5dabb130"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(), nullable=True))
    op.add_column("users", sa.Column("auth_provider", sa.String(), server_default="local", nullable=False))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(), nullable=True))

    # Make username and hashed_password nullable
    op.alter_column("users", "username", existing_type=sa.String(), nullable=True)
    op.alter_column("users", "hashed_password", existing_type=sa.String(), nullable=True)

def downgrade() -> None:
    op.alter_column("users", "hashed_password", existing_type=sa.String(), nullable=False)
    op.alter_column("users", "username", existing_type=sa.String(), nullable=False)
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "auth_provider")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "full_name")
