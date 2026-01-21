"""add_academic_ids_to_users

Revision ID: c3d4e5f6g7h8
Revises: 7a1597912092
Create Date: 2024-06-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = '7a1597912092'
branch_labels = None
depends_on = None


def upgrade():
    # Adding columns to users table.
    # If the table doesn't exist, this will fail, which is expected if the environment is broken.
    op.add_column('users', sa.Column('faculty_id', sa.UUID(), nullable=True))
    op.add_column('users', sa.Column('department_id', sa.UUID(), nullable=True))
    op.add_column('users', sa.Column('semester_id', sa.UUID(), nullable=True))

    op.create_index(op.f('ix_users_faculty_id'), 'users', ['faculty_id'], unique=False)
    op.create_index(op.f('ix_users_department_id'), 'users', ['department_id'], unique=False)
    op.create_index(op.f('ix_users_semester_id'), 'users', ['semester_id'], unique=False)

    op.create_foreign_key(None, 'users', 'faculties', ['faculty_id'], ['id'])
    op.create_foreign_key(None, 'users', 'departments', ['department_id'], ['id'])
    op.create_foreign_key(None, 'users', 'semesters', ['semester_id'], ['id'])


def downgrade():
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_semester_id'), table_name='users')
    op.drop_index(op.f('ix_users_department_id'), table_name='users')
    op.drop_index(op.f('ix_users_faculty_id'), table_name='users')
    op.drop_column('users', 'semester_id')
    op.drop_column('users', 'department_id')
    op.drop_column('users', 'faculty_id')
