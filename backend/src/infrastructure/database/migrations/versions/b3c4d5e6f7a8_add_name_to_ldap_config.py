"""add_name_to_ldap_config_and_seed

Adds the unique ``name`` column to ``ldap_config`` (enabling multiple server
configurations) and seeds the initial Emcure Pharma configuration.

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-07-23 19:00:00.000000

"""
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add the name column (server_default keeps the migration safe if rows exist).
    op.add_column(
        'ldap_config',
        sa.Column('name', sa.String(length=150), nullable=False, server_default=''),
    )
    op.create_index(
        op.f('ix_ldap_config_name'), 'ldap_config', ['name'], unique=True
    )
    # Drop the server default now that the column is populated/enforced by the app.
    op.alter_column('ldap_config', 'name', server_default=None)

    # Seed the initial Emcure Pharma configuration.
    now = datetime.now(UTC)
    ldap_config = sa.table(
        'ldap_config',
        sa.column('id', sa.UUID()),
        sa.column('name', sa.String()),
        sa.column('server_uri', sa.String()),
        sa.column('base_dn', sa.String()),
        sa.column('bind_username', sa.String()),
        sa.column('bind_password', sa.String()),
        sa.column('domain_prefix', sa.String()),
        sa.column('use_ssl', sa.Boolean()),
        sa.column('is_enabled', sa.Boolean()),
        sa.column('created_by', sa.String()),
        sa.column('created_date', sa.DateTime(timezone=True)),
        sa.column('modified_by', sa.String()),
        sa.column('modified_date', sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        ldap_config,
        [
            {
                'id': uuid4(),
                'name': 'Emcure Pharma',
                'server_uri': 'ldap://10.21.91.59:389',
                'base_dn': 'DC=emcure,DC=pharma',
                'bind_username': 'EPLPHARMA\\93300116',
                'bind_password': 'Jul@2026',
                'domain_prefix': 'EPLPHARMA\\',
                'use_ssl': False,
                'is_enabled': True,
                'created_by': 'system',
                'created_date': now,
                'modified_by': 'system',
                'modified_date': now,
            }
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_ldap_config_name'), table_name='ldap_config')
    op.drop_column('ldap_config', 'name')
