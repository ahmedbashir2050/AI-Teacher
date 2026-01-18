"""add_soft_delete_and_indexes

Revision ID: 961494454d11
Revises: 5c2c93ae6ddb
Create Date: 2026-01-18 19:11:36.735319

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '961494454d11'
down_revision: Union[str, Sequence[str], None] = '5c2c93ae6ddb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('chat_sessions', sa.Column('is_deleted', sa.DateTime(), nullable=True))
    op.add_column('chat_messages', sa.Column('is_deleted', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_chat_messages_session_id'), 'chat_messages', ['session_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_chat_messages_session_id'), table_name='chat_messages')
    op.drop_column('chat_messages', 'is_deleted')
    op.drop_column('chat_sessions', 'is_deleted')
