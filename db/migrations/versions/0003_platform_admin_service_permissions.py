"""Seed Platform Admin Service permissions and role bindings.

Revision ID: 0003_platform_admin_perms
Revises: 0002_platform_admin_identity
Create Date: 2026-07-02
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op


revision: str = "0003_platform_admin_perms"
down_revision: str | None = "0002_platform_admin_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PERMISSIONS = [
    ("platform.dashboard.read", "Read platform dashboard summary"),
    ("platform.tenant.read", "Read tenants"),
    ("platform.tenant.create", "Create tenants"),
    ("platform.tenant.update", "Update tenants"),
    ("platform.tenant.lifecycle.manage", "Manage tenant lifecycle"),
    ("platform.tenant.domain.manage", "Manage tenant domains"),
    ("platform.provisioning.read", "Read provisioning jobs"),
    ("platform.provisioning.manage", "Manage provisioning jobs"),
    ("platform.infra_pool.read", "Read infrastructure pools"),
    ("platform.infra_pool.manage", "Manage infrastructure pools"),
    ("platform.plan.read", "Read plans"),
    ("platform.plan.manage", "Manage plans"),
    ("platform.quota.read", "Read quotas"),
    ("platform.quota.manage", "Manage quotas"),
    ("platform.feature.read", "Read features"),
    ("platform.feature.manage", "Manage features"),
    ("platform.addon.read", "Read add-ons"),
    ("platform.addon.manage", "Manage add-ons"),
    ("platform.entitlement.read", "Read effective entitlements"),
    ("platform.feature_flag.read", "Read feature flags"),
    ("platform.feature_flag.manage", "Manage feature flags"),
    ("platform.user.read", "Read platform users"),
    ("platform.user.manage", "Manage platform users"),
    ("platform.role.read", "Read platform roles"),
    ("platform.role.manage", "Manage platform roles"),
    ("platform.support_session.read", "Read support sessions"),
    ("platform.support_session.manage", "Manage support sessions"),
    ("platform.support_ticket.read", "Read support tickets"),
    ("platform.support_ticket.manage", "Manage support tickets"),
    ("platform.sla.read", "Read SLA policies"),
    ("platform.sla.manage", "Manage SLA policies"),
    ("platform.compliance.read", "Read compliance mappings"),
    ("platform.compliance.manage", "Manage compliance mappings"),
    ("platform.ai_governance.read", "Read AI governance metadata"),
    ("platform.ai_governance.manage", "Manage AI governance metadata"),
    ("platform.operations.read", "Read operations metadata"),
    ("platform.operations.manage", "Manage operations metadata"),
    ("platform.audit_log.read", "Read platform audit logs"),
]


def upgrade() -> None:
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
        WHERE r.role_key = 'super_admin'
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO platform.platform_role_permissions(role_id, permission_id)
        SELECT r.id, p.id
        FROM platform.platform_roles r
        JOIN platform.platform_permissions p
          ON p.permission_key IN (
            'platform.dashboard.read',
            'platform.tenant.read',
            'platform.entitlement.read',
            'platform.support_session.read',
            'platform.support_session.manage',
            'platform.support_ticket.read',
            'platform.support_ticket.manage',
            'platform.audit_log.read'
          )
        WHERE r.role_key = 'support_admin'
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO platform.platform_role_permissions(role_id, permission_id)
        SELECT r.id, p.id
        FROM platform.platform_roles r
        JOIN platform.platform_permissions p
          ON p.permission_key IN (
            'platform.ai_governance.read',
            'platform.ai_governance.manage',
            'platform.feature.read',
            'platform.feature_flag.read',
            'platform.audit_log.read'
          )
        WHERE r.role_key = 'ai_governance_admin'
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
