"""create_ldap_config_table

Revision ID: a1b2c3d4e5f6
Revises: b2c3d4e5f6a7
Create Date: 2026-07-23 18:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = 'b2c3d4e5f6a7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'ldap_config',
        sa.Column('server_uri', sa.String(length=255), nullable=False),
        sa.Column('base_dn', sa.String(length=255), nullable=False),
        sa.Column('bind_username', sa.String(length=255), nullable=False),
        sa.Column('bind_password', sa.String(length=512), nullable=False),
        sa.Column('domain_prefix', sa.String(length=128), nullable=False),
        sa.Column('use_ssl', sa.Boolean(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('modified_by', sa.String(length=255), nullable=False),
        sa.Column('modified_date', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('ldap_config')
