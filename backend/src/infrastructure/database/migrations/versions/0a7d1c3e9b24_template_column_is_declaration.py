"""add is_declaration to template_layout_columns

Lets a stage carry two independent column sets: its normal question grid
(is_declaration = false) and its declaration-questions grid (is_declaration =
true), both scoped to the same format_stage_mapping_id / section_id.

Revision ID: 0a7d1c3e9b24
Revises: f6a7b8c9d0e1
Create Date: 2026-09-15 05:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0a7d1c3e9b24"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "template_layout_columns",
        sa.Column(
            "is_declaration",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("template_layout_columns", "is_declaration")
