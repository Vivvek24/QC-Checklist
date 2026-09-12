"""add_darwin_ad_fields_to_darwinbox_employees

Adds the four fields the published Darwin AD service returns that were not
previously persisted from the Darwinbox master sync:
  - employeeid_num   (Darwinbox internal numeric id, surfaced as "employeeid")
  - split_territory
  - split_department
  - split_role

Revision ID: d4e5f6a7b8c9
Revises: b3c4d5e6f7a8
Create Date: 2026-07-23 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "b3c4d5e6f7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "darwinbox_employees",
        sa.Column(
            "employeeid_num",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "darwinbox_employees",
        sa.Column(
            "split_territory", sa.Text(), nullable=False, server_default=""
        ),
    )
    op.add_column(
        "darwinbox_employees",
        sa.Column(
            "split_department", sa.Text(), nullable=False, server_default=""
        ),
    )
    op.add_column(
        "darwinbox_employees",
        sa.Column("split_role", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("darwinbox_employees", "split_role")
    op.drop_column("darwinbox_employees", "split_department")
    op.drop_column("darwinbox_employees", "split_territory")
    op.drop_column("darwinbox_employees", "employeeid_num")
