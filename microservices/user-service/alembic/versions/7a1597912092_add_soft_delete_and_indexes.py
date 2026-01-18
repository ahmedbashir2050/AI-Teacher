"""add_soft_delete_and_indexes

Revision ID: 7a1597912092
Revises: 7d8da669ed58
Create Date: 2026-01-18 19:11:10.735319

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7a1597912092'
down_revision: Union[str, Sequence[str], None] = '7d8da669ed58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('faculties', sa.Column('is_deleted', sa.DateTime(), nullable=True))
    op.add_column('departments', sa.Column('is_deleted', sa.DateTime(), nullable=True))
    op.add_column('semesters', sa.Column('is_deleted', sa.DateTime(), nullable=True))
    op.add_column('courses', sa.Column('is_deleted', sa.DateTime(), nullable=True))
    op.add_column('user_profiles', sa.Column('is_deleted', sa.DateTime(), nullable=True))
    op.add_column('books', sa.Column('is_deleted', sa.DateTime(), nullable=True))

    op.create_index(op.f('ix_user_profiles_faculty_id'), 'user_profiles', ['faculty_id'], unique=False)
    op.create_index(op.f('ix_user_profiles_department_id'), 'user_profiles', ['department_id'], unique=False)
    op.create_index(op.f('ix_user_profiles_semester_id'), 'user_profiles', ['semester_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_user_profiles_semester_id'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_department_id'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_faculty_id'), table_name='user_profiles')

    op.drop_column('books', 'is_deleted')
    op.drop_column('user_profiles', 'is_deleted')
    op.drop_column('courses', 'is_deleted')
    op.drop_column('semesters', 'is_deleted')
    op.drop_column('departments', 'is_deleted')
    op.drop_column('faculties', 'is_deleted')
