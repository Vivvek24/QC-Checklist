"""add checklist_pdf_exports table and checklist_requests.export permission

Revision ID: a1b2c3d4e5f6
Revises: e6a4b5448808
Create Date: 2026-09-15 00:00:00.000000

"""
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "e6a4b5448808"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── audit table: one row per PDF export (who/when via audit columns) ──
    op.create_table(
        "checklist_pdf_exports",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("request_number", sa.String(length=100), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("modified_by", sa.String(length=255), nullable=False),
        sa.Column("modified_date", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_checklist_pdf_exports_request_number"),
        "checklist_pdf_exports",
        ["request_number"],
        unique=False,
    )

    # ── seed the export permission + link it to ADMINISTRATOR (idempotent) ──
    now = datetime.now(UTC)
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO permissions
                (code, name, description, scope, resource, action, is_active,
                 created_by, created_date, modified_by, modified_date)
            SELECT 'checklist_requests.export', 'Export Checklist Request as PDF', '',
                   'API', 'checklist_requests', 'EXPORT', true,
                   'migration', :now, 'migration', :now
            WHERE NOT EXISTS (
                SELECT 1 FROM permissions WHERE code = 'checklist_requests.export'
            )
            """
        ),
        {"now": now},
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions
                (role_id, permission_id, created_by, created_date, modified_by, modified_date)
            SELECT r.id, p.id, 'migration', :now, 'migration', :now
            FROM roles r
            JOIN permissions p ON p.code = 'checklist_requests.export'
            WHERE r.code = 'ADMINISTRATOR'
              AND NOT EXISTS (
                  SELECT 1 FROM role_permissions rp
                  WHERE rp.role_id = r.id AND rp.permission_id = p.id
              )
            """
        ),
        {"now": now},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id IN (
                SELECT id FROM permissions WHERE code = 'checklist_requests.export'
            )
            """
        )
    )
    conn.execute(
        sa.text("DELETE FROM permissions WHERE code = 'checklist_requests.export'")
    )
    op.drop_index(
        op.f("ix_checklist_pdf_exports_request_number"),
        table_name="checklist_pdf_exports",
    )
    op.drop_table("checklist_pdf_exports")
