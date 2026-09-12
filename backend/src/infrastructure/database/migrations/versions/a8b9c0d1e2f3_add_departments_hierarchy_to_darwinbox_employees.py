"""add_departments_hierarchy_to_darwinbox_employees

Adds the ``departments_hierarchy`` field newly returned by the Darwinbox master
API (e.g. "Regulatory Affairs"). Persisted from the sync and surfaced in both
the internal stored-employee response and the published Darwin AD response so
consuming applications receive it without any contract change on their side.

``server_default=""`` is required because the column is NOT NULL and the table
already holds the full employee master (~16k rows).

Revision ID: a8b9c0d1e2f3
Revises: f5a6b7c8d9e0
Create Date: 2026-08-27 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a8b9c0d1e2f3"
down_revision: str | None = "f5a6b7c8d9e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "darwinbox_employees",
        sa.Column(
            "departments_hierarchy", sa.Text(), nullable=False, server_default=""
        ),
    )


def downgrade() -> None:
    op.drop_column("darwinbox_employees", "departments_hierarchy")
