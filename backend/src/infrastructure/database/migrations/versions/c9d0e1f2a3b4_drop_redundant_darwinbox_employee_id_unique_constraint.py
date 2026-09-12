"""drop_redundant_darwinbox_employee_id_unique_constraint

Removes the duplicate uniqueness guarantee on ``darwinbox_employees.employee_id``.

The table-creation migration (``f3a4b5c6d7e8``) declared BOTH
``sa.UniqueConstraint("employee_id")`` — which Postgres named
``darwinbox_employees_employee_id_key`` and backed with its own index — AND
``op.create_index("ix_darwinbox_employees_employee_id", unique=True)``. The ORM
model declares ``mapped_column(String(50), unique=True, index=True)``, which
SQLAlchemy renders as the unique *index* alone, so the constraint has no
counterpart in the metadata and ``alembic check`` reported it as drift.

Two B-tree indexes were therefore being maintained for the same invariant on the
hottest write path in the service: ``bulk_upsert`` touches every row on each
Darwinbox sync. Dropping the constraint leaves uniqueness fully enforced by the
remaining unique index.

Safe for the upsert: ``bulk_upsert`` uses
``on_conflict_do_update(index_elements=[DarwinboxEmployeeModel.employee_id])``,
which infers the arbiter from the column rather than naming a constraint, so it
resolves against the surviving unique index unchanged. A migration that named the
constraint in ``index_elements``/``constraint=`` would not have been safe here.

Revision ID: c9d0e1f2a3b4
Revises: a8b9c0d1e2f3
Create Date: 2026-08-27 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: str | None = "a8b9c0d1e2f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "darwinbox_employees_employee_id_key",
        "darwinbox_employees",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "darwinbox_employees_employee_id_key",
        "darwinbox_employees",
        ["employee_id"],
    )
