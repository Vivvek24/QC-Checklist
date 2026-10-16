"""add is_approvable to questions and question_id FK to approval_labels

Mirrors the stage approval-label pattern on the question master:
  - questions.is_approvable (bool, default false)
  - approval_labels.question_id (nullable FK -> questions.id, ON DELETE CASCADE)

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-15 02:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column(
            "is_approvable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "approval_labels",
        sa.Column("question_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "ix_approval_labels_question_id",
        "approval_labels",
        ["question_id"],
    )
    op.create_foreign_key(
        "fk_approval_labels_question_id_questions",
        "approval_labels",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_approval_labels_question_id_questions",
        "approval_labels",
        type_="foreignkey",
    )
    op.drop_index("ix_approval_labels_question_id", table_name="approval_labels")
    op.drop_column("approval_labels", "question_id")
    op.drop_column("questions", "is_approvable")
