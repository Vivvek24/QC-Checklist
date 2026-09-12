"""drop_workflow_and_commission_tables

Drops orphaned tables left behind after the workflow, approval-matrix, and
commission-claim modules were removed from the application (commit 954b9f8).
The ORM models and their creating migrations were deleted, but the physical
tables remained in the database. This migration brings the schema back in sync
with the codebase.

Tables dropped (child-first to respect FK dependencies):
  - approval_tasks, approval_delegations, approval_assignments,
    approval_conditions, approval_rules, approval_matrices
  - workflow_history, workflow_instance_steps, workflow_instances,
    workflow_assignment_rules, workflow_steps, workflow_actions,
    workflow_transitions, workflow_statuses, workflow_definitions
  - commission_claims

Revision ID: f5a6b7c8d9e0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-28 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f5a6b7c8d9e0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Ordered child-first so foreign-key dependencies drop cleanly.
DROPPED_TABLES = [
    "approval_tasks",
    "approval_delegations",
    "approval_assignments",
    "approval_conditions",
    "approval_rules",
    "approval_matrices",
    "workflow_history",
    "workflow_instance_steps",
    "workflow_instances",
    "workflow_assignment_rules",
    "workflow_steps",
    "workflow_actions",
    "workflow_transitions",
    "workflow_statuses",
    "workflow_definitions",
    "commission_claims",
]


def upgrade() -> None:
    for table in DROPPED_TABLES:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')


def downgrade() -> None:
    # Irreversible: the workflow / approval-matrix / commission-claim modules
    # (models and their original creating migrations) were removed from the
    # codebase, so the table definitions no longer exist to recreate.
    raise NotImplementedError(
        "Cannot recreate dropped workflow/commission tables — the source "
        "modules were permanently removed from the application."
    )
