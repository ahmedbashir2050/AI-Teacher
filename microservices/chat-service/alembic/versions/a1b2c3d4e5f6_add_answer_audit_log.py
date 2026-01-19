"""add_answer_audit_log

Revision ID: a1b2c3d4e5f6
Revises: 961494454d11
Create Date: 2024-05-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '961494454d11'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'answer_audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=True),
        sa.Column('book_id', sa.String(length=255), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('ai_answer', sa.Text(), nullable=False),
        sa.Column('source_reference', sa.Text(), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_answer_audit_logs_book_id'), 'answer_audit_logs', ['book_id'], unique=False)
    op.create_index(op.f('ix_answer_audit_logs_session_id'), 'answer_audit_logs', ['session_id'], unique=False)
    op.create_index(op.f('ix_answer_audit_logs_user_id'), 'answer_audit_logs', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_answer_audit_logs_user_id'), table_name='answer_audit_logs')
    op.drop_index(op.f('ix_answer_audit_logs_session_id'), table_name='answer_audit_logs')
    op.drop_index(op.f('ix_answer_audit_logs_book_id'), table_name='answer_audit_logs')
    op.drop_table('answer_audit_logs')
