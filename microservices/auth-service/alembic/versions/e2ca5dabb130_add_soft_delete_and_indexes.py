"""add_soft_delete

Revision ID: e2ca5dabb130
Revises: ff8227c79623
Create Date: 2026-01-18 19:11:05.606307

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2ca5dabb130"
down_revision: Union[str, Sequence[str], None] = "ff8227c79623"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_deleted", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "is_deleted")
