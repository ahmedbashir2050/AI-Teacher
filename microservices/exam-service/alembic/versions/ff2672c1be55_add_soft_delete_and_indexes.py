"""add_soft_delete_and_indexes

Revision ID: ff2672c1be55
Revises: 5cf70dc76719
Create Date: 2026-01-18 19:11:38.735319

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ff2672c1be55"
down_revision: Union[str, Sequence[str], None] = "5cf70dc76719"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("exams", sa.Column("is_deleted", sa.DateTime(), nullable=True))
    op.add_column("questions", sa.Column("is_deleted", sa.DateTime(), nullable=True))
    op.add_column(
        "exam_attempts", sa.Column("is_deleted", sa.DateTime(), nullable=True)
    )

    op.create_index(op.f("ix_exams_course_id"), "exams", ["course_id"], unique=False)
    op.create_index(op.f("ix_exams_creator_id"), "exams", ["creator_id"], unique=False)
    op.create_index(
        op.f("ix_questions_exam_id"), "questions", ["exam_id"], unique=False
    )
    op.create_index(
        op.f("ix_exam_attempts_exam_id"), "exam_attempts", ["exam_id"], unique=False
    )
    op.create_index(
        op.f("ix_exam_attempts_user_id"), "exam_attempts", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_exam_attempts_user_id"), table_name="exam_attempts")
    op.drop_index(op.f("ix_exam_attempts_exam_id"), table_name="exam_attempts")
    op.drop_index(op.f("ix_questions_exam_id"), table_name="questions")
    op.drop_index(op.f("ix_exams_creator_id"), table_name="exams")
    op.drop_index(op.f("ix_exams_course_id"), table_name="exams")

    op.drop_column("exam_attempts", "is_deleted")
    op.drop_column("questions", "is_deleted")
    op.drop_column("exams", "is_deleted")
