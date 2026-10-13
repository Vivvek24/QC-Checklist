"""seed the services.sap permission and link it to ADMINISTRATOR

Grants access to the SAP Integration service endpoints (/services/sap/*).

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-15 01:00:00.000000

"""
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    now = datetime.now(UTC)
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO permissions
                (code, name, description, scope, resource, action, is_active,
                 created_by, created_date, modified_by, modified_date)
            SELECT 'services.sap', 'Access SAP Integration Service', '',
                   'API', 'services', 'EXECUTE', true,
                   'migration', :now, 'migration', :now
            WHERE NOT EXISTS (
                SELECT 1 FROM permissions WHERE code = 'services.sap'
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
            JOIN permissions p ON p.code = 'services.sap'
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
                SELECT id FROM permissions WHERE code = 'services.sap'
            )
            """
        )
    )
    conn.execute(sa.text("DELETE FROM permissions WHERE code = 'services.sap'"))
