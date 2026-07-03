"""add tenant addresses and employee count

Revision ID: 2f1f82fae1fc
Revises: 0003_platform_admin_perms
Create Date: 2026-07-03 16:18:55.049908

Hand-trimmed from the raw `alembic revision --autogenerate` output: the raw diff
also included drops of partition-default tables (audit_logs_default,
analytics_events_default, ai_usage_events_default, security_events_default,
usage_events_default, domain_events_default), several indexes, and table
comments — all pre-existing drift between the live DB and SQLAlchemy metadata
(those objects are created via raw SQL, not modeled as Base subclasses, per
db/migrations/README.md). None of that belongs in this migration; only the
new `tenant_addresses` table and `tenants.employee_count` column are this
change's actual scope.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '2f1f82fae1fc'
down_revision: str | None = '0003_platform_admin_perms'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PERMISSIONS = [
    ("platform.tenant.address.manage", "Manage tenant addresses"),
]


def upgrade() -> None:
    op.create_table(
        'tenant_addresses',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('address_line1', sa.Text(), nullable=False),
        sa.Column('address_line2', sa.Text(), nullable=True),
        sa.Column('city', sa.Text(), nullable=False),
        sa.Column('state', sa.Text(), nullable=False),
        sa.Column('postal_code', sa.Text(), nullable=False),
        sa.Column('country', sa.Text(), nullable=False),
        sa.Column('website_url', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_tenant_addresses_tenant'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tenant_addresses')),
        schema='platform',
    )
    op.add_column('tenants', sa.Column('employee_count', sa.Integer(), nullable=True), schema='platform')

    for permission_key, description in PERMISSIONS:
        op.execute(
            """
            INSERT INTO platform.platform_permissions(permission_key, description)
            VALUES (%(permission_key)r, %(description)r)
            ON CONFLICT (permission_key) DO UPDATE SET description = EXCLUDED.description
            """
            % {"permission_key": permission_key, "description": description}
        )
    op.execute(
        """
        INSERT INTO platform.platform_role_permissions(role_id, permission_id)
        SELECT r.id, p.id
        FROM platform.platform_roles r
        CROSS JOIN platform.platform_permissions p
        WHERE r.role_key = 'super_admin' AND p.permission_key = 'platform.tenant.address.manage'
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    keys = ", ".join("'%s'" % permission_key for permission_key, _description in PERMISSIONS)
    op.execute(
        f"""
        DELETE FROM platform.platform_role_permissions
        WHERE permission_id IN (
          SELECT id FROM platform.platform_permissions WHERE permission_key IN ({keys})
        )
        """
    )
    op.execute(f"DELETE FROM platform.platform_permissions WHERE permission_key IN ({keys})")

    op.drop_column('tenants', 'employee_count', schema='platform')
    op.drop_table('tenant_addresses', schema='platform')
