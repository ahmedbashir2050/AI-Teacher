"""add_teacher_review_fields

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2024-06-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('answer_audit_logs', sa.Column('verified_by_teacher', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('answer_audit_logs', sa.Column('teacher_comment', sa.Text(), nullable=True))
    op.add_column('answer_audit_logs', sa.Column('rag_confidence_score', sa.Float(), nullable=True))
    op.add_column('answer_audit_logs', sa.Column('custom_tags', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('answer_audit_logs', 'custom_tags')
    op.drop_column('answer_audit_logs', 'rag_confidence_score')
    op.drop_column('answer_audit_logs', 'teacher_comment')
    op.drop_column('answer_audit_logs', 'verified_by_teacher')
