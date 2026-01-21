"""add_faculty_id_to_exams

Revision ID: a1b2c3d4e5f7
Revises: ff2672c1be55
Create Date: 2024-06-01 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = 'ff2672c1be55'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('exams', sa.Column('faculty_id', sa.UUID(), nullable=True))
    op.add_column('exams', sa.Column('semester_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_exams_faculty_id'), 'exams', ['faculty_id'], unique=False)
    op.create_index(op.f('ix_exams_semester_id'), 'exams', ['semester_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_exams_semester_id'), table_name='exams')
    op.drop_index(op.f('ix_exams_faculty_id'), table_name='exams')
    op.drop_column('exams', 'semester_id')
    op.drop_column('exams', 'faculty_id')
