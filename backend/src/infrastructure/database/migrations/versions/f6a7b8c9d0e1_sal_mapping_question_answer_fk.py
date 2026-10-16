"""add question_answer_id to stage_approval_label_mappings; make checklist_stage_id nullable

Lets the SAME stage_approval_label_mappings table store per-question approval
actions: a row belongs to EITHER a checklist stage OR a question_answer
(mirrors the approval_labels stage/question split).

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-15 04:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "stage_approval_label_mappings",
        sa.Column("question_answer_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "ix_stage_approval_label_mappings_question_answer_id",
        "stage_approval_label_mappings",
        ["question_answer_id"],
    )
    op.create_foreign_key(
        "fk_salm_question_answer_id_question_answers",
        "stage_approval_label_mappings",
        "question_answers",
        ["question_answer_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column(
        "stage_approval_label_mappings",
        "checklist_stage_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "stage_approval_label_mappings",
        "checklist_stage_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.drop_constraint(
        "fk_salm_question_answer_id_question_answers",
        "stage_approval_label_mappings",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_stage_approval_label_mappings_question_answer_id",
        table_name="stage_approval_label_mappings",
    )
    op.drop_column("stage_approval_label_mappings", "question_answer_id")
