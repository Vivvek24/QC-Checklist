"""sub-question answers as a QuestionAnswer self-join + helper owner FK

- question_answer_sub_question_answers: the child FK must reference
  question_answers (Mendix self-association), so rename
  question_answer_helper_id -> question_answer_parent_id and repoint the FK to
  question_answers. (question_answer_id = child/sub answer,
  question_answer_parent_id = parent answer.)
- question_answer_helpers: add a question_answer_id FK so each helper belongs
  to its QuestionAnswer.

Both tables are empty in all environments, so no data migration is needed.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-15 00:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── self-join: child FK now references question_answers ──
    op.drop_constraint(
        "question_answer_sub_question_ans_question_answer_helper_id_fkey",
        "question_answer_sub_question_answers",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_question_answer_sub_question_answers_question_answer_d4d3",
        table_name="question_answer_sub_question_answers",
    )
    op.alter_column(
        "question_answer_sub_question_answers",
        "question_answer_helper_id",
        new_column_name="question_answer_parent_id",
    )
    op.create_index(
        op.f("ix_question_answer_sub_question_answers_question_answer_parent_id"),
        "question_answer_sub_question_answers",
        ["question_answer_parent_id"],
        unique=False,
    )
    op.create_foreign_key(
        "qa_sub_qa_parent_id_fkey",
        "question_answer_sub_question_answers",
        "question_answers",
        ["question_answer_parent_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── helper now belongs to a QuestionAnswer ──
    op.add_column(
        "question_answer_helpers",
        sa.Column("question_answer_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        op.f("ix_question_answer_helpers_question_answer_id"),
        "question_answer_helpers",
        ["question_answer_id"],
        unique=False,
    )
    op.create_foreign_key(
        "qa_helpers_question_answer_id_fkey",
        "question_answer_helpers",
        "question_answers",
        ["question_answer_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # ── helper owner FK ──
    op.drop_constraint(
        "qa_helpers_question_answer_id_fkey",
        "question_answer_helpers",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_question_answer_helpers_question_answer_id"),
        table_name="question_answer_helpers",
    )
    op.drop_column("question_answer_helpers", "question_answer_id")

    # ── self-join revert ──
    op.drop_constraint(
        "qa_sub_qa_parent_id_fkey",
        "question_answer_sub_question_answers",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_question_answer_sub_question_answers_question_answer_parent_id"),
        table_name="question_answer_sub_question_answers",
    )
    op.alter_column(
        "question_answer_sub_question_answers",
        "question_answer_parent_id",
        new_column_name="question_answer_helper_id",
    )
    op.create_index(
        "ix_question_answer_sub_question_answers_question_answer_d4d3",
        "question_answer_sub_question_answers",
        ["question_answer_helper_id"],
        unique=False,
    )
    op.create_foreign_key(
        "question_answer_sub_question_ans_question_answer_helper_id_fkey",
        "question_answer_sub_question_answers",
        "question_answer_helpers",
        ["question_answer_helper_id"],
        ["id"],
        ondelete="CASCADE",
    )
