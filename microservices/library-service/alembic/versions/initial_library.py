"""initial library migration

Revision ID: initial_library
Revises:
Create Date: 2023-10-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial_library'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Faculties table
    op.create_table(
        'faculties',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_faculties_name'), 'faculties', ['name'], unique=True)

    # Departments table
    op.create_table(
        'departments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('faculty_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['faculty_id'], ['faculties.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'faculty_id', name='_department_faculty_uc')
    )
    op.create_index(op.f('ix_departments_name'), 'departments', ['name'], unique=False)

    # Books table
    op.create_table(
        'books',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.DateTime(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('faculty_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=False),
        sa.Column('file_key', sa.String(length=512), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['faculty_id'], ['faculties.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_hash'),
        sa.UniqueConstraint('file_key')
    )
    op.create_index(op.f('ix_books_department_id'), 'books', ['department_id'], unique=False)
    op.create_index(op.f('ix_books_faculty_id'), 'books', ['faculty_id'], unique=False)
    op.create_index(op.f('ix_books_file_hash'), 'books', ['file_hash'], unique=True)
    op.create_index(op.f('ix_books_is_active'), 'books', ['is_active'], unique=False)
    op.create_index(op.f('ix_books_semester'), 'books', ['semester'], unique=False)
    op.create_index(op.f('ix_books_title'), 'books', ['title'], unique=False)
    op.create_index(op.f('ix_books_uploaded_by'), 'books', ['uploaded_by'], unique=False)


def downgrade():
    op.drop_table('books')
    op.drop_table('departments')
    op.drop_table('faculties')
