from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import sys

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import text
from sqlalchemy.engine import Connection

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "packages" / "backend-common" / "src"))
sys.path.insert(0, str(REPOSITORY_ROOT / "services" / "identity" / "src"))

from gnxthire_common.db import create_sync_engine
from gnxthire_common.config import get_settings
from gnxthire_identity.config import get_identity_settings
from gnxthire_identity.security import hash_password, validate_password_policy


DEFAULT_PLATFORM_ADMIN_SEED_EMAIL = "ankit@gnxtsystems.com"
DEFAULT_PLATFORM_ADMIN_SEED_PASSWORD = "LocalTest@12345"
SEED_EMAIL_DOMAIN = "local.gnxthire.test"


class PlatformAdminSeedSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    email: str = Field(
        default=DEFAULT_PLATFORM_ADMIN_SEED_EMAIL,
        validation_alias="PLATFORM_ADMIN_SEED_EMAIL",
    )
    password: str = Field(
        default=DEFAULT_PLATFORM_ADMIN_SEED_PASSWORD,
        validation_alias=AliasChoices("PLATFORM_ADMIN_SEED_PASSWORD", "PLATFORM_ADMIN_LOCAL_PASSWORD"),
    )


SEED_SETTINGS = PlatformAdminSeedSettings()
PLATFORM_ADMIN_SEED_EMAIL = SEED_SETTINGS.email.strip().lower()
PLATFORM_ADMIN_SEED_PASSWORD = SEED_SETTINGS.password


@dataclass(frozen=True)
class SeedUser:
    email: str
    display_name: str
    role_key: str


USERS = [
    SeedUser(PLATFORM_ADMIN_SEED_EMAIL, "Super Admin", "super_admin"),
    SeedUser("support.admin@local.gnxthire.test", "Support Admin", "support_admin"),
    SeedUser("billing.admin@local.gnxthire.test", "Billing Plan Admin", "billing_plan_admin"),
    SeedUser("security.admin@local.gnxthire.test", "Security Admin", "security_admin"),
    SeedUser("ai.governance@local.gnxthire.test", "AI Governance Admin", "ai_governance_admin"),
    SeedUser("auditor@local.gnxthire.test", "Read-only Auditor", "readonly_auditor"),
]

ROLES = [
    ("super_admin", "Super Admin", "Full local/test platform administration access."),
    ("support_admin", "Support Admin", "Tenant support, support sessions, tickets, and audit review."),
    ("billing_plan_admin", "Billing / Plan Admin", "Plans, quotas, features, add-ons, and entitlements."),
    ("security_admin", "Security Admin", "Platform users, roles, permissions, audit, and compliance."),
    ("ai_governance_admin", "AI Governance Admin", "AI model catalogue and governance alerts."),
    ("readonly_auditor", "Read-only Auditor", "Read-only access to platform state and audit logs."),
]

PERMISSIONS = [
    "platform.dashboard.read",
    "platform.tenant.read",
    "platform.tenant.create",
    "platform.tenant.update",
    "platform.tenant.lifecycle.manage",
    "platform.tenant.domain.manage",
    "platform.provisioning.read",
    "platform.provisioning.manage",
    "platform.infra_pool.read",
    "platform.infra_pool.manage",
    "platform.plan.read",
    "platform.plan.manage",
    "platform.quota.read",
    "platform.quota.manage",
    "platform.feature.read",
    "platform.feature.manage",
    "platform.addon.read",
    "platform.addon.manage",
    "platform.entitlement.read",
    "platform.feature_flag.read",
    "platform.feature_flag.manage",
    "platform.user.read",
    "platform.user.manage",
    "platform.role.read",
    "platform.role.manage",
    "platform.support_session.read",
    "platform.support_session.manage",
    "platform.support_ticket.read",
    "platform.support_ticket.manage",
    "platform.sla.read",
    "platform.sla.manage",
    "platform.compliance.read",
    "platform.compliance.manage",
    "platform.ai_governance.read",
    "platform.ai_governance.manage",
    "platform.operations.read",
    "platform.operations.manage",
    "platform.audit_log.read",
]

ROLE_PERMISSIONS = {
    "support_admin": {
        "platform.dashboard.read",
        "platform.tenant.read",
        "platform.provisioning.read",
        "platform.support_session.read",
        "platform.support_session.manage",
        "platform.support_ticket.read",
        "platform.support_ticket.manage",
        "platform.sla.read",
        "platform.audit_log.read",
    },
    "billing_plan_admin": {
        "platform.dashboard.read",
        "platform.tenant.read",
        "platform.plan.read",
        "platform.plan.manage",
        "platform.quota.read",
        "platform.quota.manage",
        "platform.feature.read",
        "platform.feature.manage",
        "platform.addon.read",
        "platform.addon.manage",
        "platform.entitlement.read",
        "platform.audit_log.read",
    },
    "security_admin": {
        "platform.dashboard.read",
        "platform.tenant.read",
        "platform.user.read",
        "platform.user.manage",
        "platform.role.read",
        "platform.role.manage",
        "platform.compliance.read",
        "platform.compliance.manage",
        "platform.audit_log.read",
    },
    "ai_governance_admin": {
        "platform.dashboard.read",
        "platform.tenant.read",
        "platform.feature.read",
        "platform.feature_flag.read",
        "platform.ai_governance.read",
        "platform.ai_governance.manage",
        "platform.audit_log.read",
    },
    "readonly_auditor": {permission for permission in PERMISSIONS if permission.endswith(".read")},
}


def require_local_or_test() -> None:
    settings = get_settings()
    identity_settings = get_identity_settings()
    if settings.environment not in {"local", "test"} or identity_settings.app_env not in {"local", "test"}:
        raise SystemExit("Refusing to seed Platform Admin data outside local/test environments.")


def execute_scalar(connection: Connection, sql: str, params: dict[str, object]) -> object:
    return connection.execute(text(sql), params).scalar_one()


def upsert_role(connection: Connection, role_key: str, name: str, description: str) -> object:
    return execute_scalar(
        connection,
        """
        INSERT INTO platform.platform_roles(role_key, name, description)
        VALUES (:role_key, :name, :description)
        ON CONFLICT (role_key) DO UPDATE
        SET name = EXCLUDED.name, description = EXCLUDED.description, updated_at = now()
        RETURNING id
        """,
        {"role_key": role_key, "name": name, "description": description},
    )


def upsert_permission(connection: Connection, permission_key: str) -> object:
    return execute_scalar(
        connection,
        """
        INSERT INTO platform.platform_permissions(permission_key, description)
        VALUES (:permission_key, :description)
        ON CONFLICT (permission_key) DO UPDATE
        SET description = EXCLUDED.description
        RETURNING id
        """,
        {"permission_key": permission_key, "description": permission_key.replace(".", " ")},
    )


def seed_access_control(connection: Connection) -> dict[str, object]:
    role_ids = {role_key: upsert_role(connection, role_key, name, description) for role_key, name, description in ROLES}
    permission_ids = {permission: upsert_permission(connection, permission) for permission in PERMISSIONS}

    for role_key, role_id in role_ids.items():
        connection.execute(text("DELETE FROM platform.platform_role_permissions WHERE role_id = :role_id"), {"role_id": role_id})
        role_permissions = set(PERMISSIONS) if role_key == "super_admin" else ROLE_PERMISSIONS.get(role_key, set())
        for permission in sorted(role_permissions):
            connection.execute(
                text(
                    """
                    INSERT INTO platform.platform_role_permissions(role_id, permission_id)
                    VALUES (:role_id, :permission_id)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"role_id": role_id, "permission_id": permission_ids[permission]},
            )
    return role_ids


def seed_platform_users(connection: Connection, role_ids: dict[str, object]) -> dict[str, object]:
    identity_settings = get_identity_settings()
    password_hash = hash_password(PLATFORM_ADMIN_SEED_PASSWORD)
    user_ids: dict[str, object] = {}
    for user in USERS:
        validate_password_policy(PLATFORM_ADMIN_SEED_PASSWORD, user.email, identity_settings)
        user_id = execute_scalar(
            connection,
            """
            INSERT INTO platform.platform_users(email, display_name, status, password_hash, email_verified_at, mfa_required)
            VALUES (:email, :display_name, 'active', :password_hash, now(), false)
            ON CONFLICT (email) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                status = 'active',
                password_hash = EXCLUDED.password_hash,
                email_verified_at = COALESCE(platform.platform_users.email_verified_at, now()),
                mfa_required = false,
                deleted_at = NULL,
                updated_at = now()
            RETURNING id
            """,
            {"email": user.email, "display_name": user.display_name, "password_hash": password_hash},
        )
        user_ids[user.email] = user_id
        connection.execute(
            text(
                """
                INSERT INTO platform.platform_user_roles(platform_user_id, role_id)
                VALUES (:platform_user_id, :role_id)
                ON CONFLICT DO NOTHING
                """
            ),
            {"platform_user_id": user_id, "role_id": role_ids[user.role_key]},
        )
    return user_ids


def seed_catalogue(connection: Connection) -> dict[str, dict[str, object]]:
    infra_pools = {
        "india-production": ("India Production Pool", "IN", "dedicated_compute", "pg-in-prod", "os-in-prod", "gnxthire-in-prod"),
        "india-sandbox": ("India Sandbox Pool", "IN", "shared", "pg-in-sandbox", "os-in-sandbox", "gnxthire-in-sandbox"),
        "us-production": ("US Production Pool", "US", "dedicated_compute", "pg-us-prod", "os-us-prod", "gnxthire-us-prod"),
        "eu-production": ("EU Production Pool", "EU", "dedicated_db", "pg-eu-prod", "os-eu-prod", "gnxthire-eu-prod"),
    }
    infra_ids = {}
    for pool_key, (_name, region, isolation_tier, db_ref, search_ref, storage_ref) in infra_pools.items():
        infra_ids[pool_key] = execute_scalar(
            connection,
            """
            INSERT INTO platform.infra_pools(
              pool_key, region, isolation_tier, database_cluster_ref, search_cluster_ref, storage_bucket_prefix, status
            )
            VALUES (:pool_key, :region, :isolation_tier, :db_ref, :search_ref, :storage_ref, 'active')
            ON CONFLICT (pool_key) DO UPDATE
            SET region = EXCLUDED.region,
                isolation_tier = EXCLUDED.isolation_tier,
                database_cluster_ref = EXCLUDED.database_cluster_ref,
                search_cluster_ref = EXCLUDED.search_cluster_ref,
                storage_bucket_prefix = EXCLUDED.storage_bucket_prefix,
                status = 'active',
                updated_at = now()
            RETURNING id
            """,
            {
                "pool_key": pool_key,
                "region": region,
                "isolation_tier": isolation_tier,
                "db_ref": db_ref,
                "search_ref": search_ref,
                "storage_ref": storage_ref,
            },
        )

    plans = {
        "starter": ("Starter", "Entry plan for small hiring teams.", "monthly", Decimal("49"), "USD", 1, 10, 14),
        "growth": ("Growth", "Growing companies with active hiring.", "monthly", Decimal("149"), "USD", 5, 50, 14),
        "business": ("Business", "Established teams with analytics and automation.", "monthly", Decimal("399"), "USD", 20, 250, 0),
        "enterprise": ("Enterprise", "Custom high-scale plan with governance.", "annual", Decimal("0"), "USD", 50, None, 0),
    }
    plan_ids = {}
    for code, (name, description, interval, price, currency, min_seats, max_seats, trial_days) in plans.items():
        plan_ids[code] = execute_scalar(
            connection,
            """
            INSERT INTO platform.plans(
              code, name, description, status, billing_interval, base_price, currency, min_seats, max_seats, trial_days
            )
            VALUES (:code, :name, :description, 'active', :interval, :price, :currency, :min_seats, :max_seats, :trial_days)
            ON CONFLICT (code) DO UPDATE
            SET name = EXCLUDED.name,
                description = EXCLUDED.description,
                status = 'active',
                billing_interval = EXCLUDED.billing_interval,
                base_price = EXCLUDED.base_price,
                currency = EXCLUDED.currency,
                min_seats = EXCLUDED.min_seats,
                max_seats = EXCLUDED.max_seats,
                trial_days = EXCLUDED.trial_days,
                deleted_at = NULL,
                updated_at = now()
            RETURNING id
            """,
            {
                "code": code,
                "name": name,
                "description": description,
                "interval": interval,
                "price": price,
                "currency": currency,
                "min_seats": min_seats,
                "max_seats": max_seats,
                "trial_days": trial_days,
            },
        )

    quota_specs = [
        ("users_per_tenant", "Users per tenant", "users", "none", False),
        ("jobs_per_month", "Jobs per month", "jobs", "monthly", True),
        ("candidates_per_month", "Candidates per month", "candidates", "monthly", True),
        ("ai_screenings_per_month", "AI screenings per month", "screenings", "monthly", True),
        ("ai_interviews_per_month", "AI interviews per month", "interviews", "monthly", True),
        ("storage_gb", "Storage", "gb", "none", True),
        ("support_sessions_per_month", "Support sessions per month", "sessions", "monthly", True),
        ("api_requests_per_month", "API requests per month", "requests", "monthly", True),
    ]
    quota_ids = {}
    for quota_key, display_name, unit, reset_period, is_metered in quota_specs:
        quota_ids[quota_key] = execute_scalar(
            connection,
            """
            INSERT INTO platform.quota_definitions(quota_key, display_name, unit, reset_period, is_metered)
            VALUES (:quota_key, :display_name, :unit, :reset_period, :is_metered)
            ON CONFLICT (quota_key) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                unit = EXCLUDED.unit,
                reset_period = EXCLUDED.reset_period,
                is_metered = EXCLUDED.is_metered,
                updated_at = now()
            RETURNING id
            """,
            {
                "quota_key": quota_key,
                "display_name": display_name,
                "unit": unit,
                "reset_period": reset_period,
                "is_metered": is_metered,
            },
        )

    feature_specs = [
        ("tenant_user_management", "Tenant user management", "core", True, False),
        ("candidate_database", "Candidate database", "ats", True, False),
        ("requisition_management", "Requisition management", "ats", True, False),
        ("pipeline_management", "Pipeline management", "ats", True, False),
        ("ai_resume_screening", "AI resume screening", "ai", False, True),
        ("ai_interviewer", "AI interviewer", "ai", False, True),
        ("interview_scheduling", "Interview scheduling", "ats", True, False),
        ("offer_management", "Offer management", "ats", False, False),
        ("agency_portal", "Agency portal", "portal", False, False),
        ("client_portal", "Client portal", "portal", False, False),
        ("advanced_analytics", "Advanced analytics", "analytics", False, False),
        ("audit_logs", "Audit logs", "security", False, False),
        ("custom_branding", "Custom branding", "configuration", False, False),
        ("api_access", "API access", "integration", False, False),
        ("priority_support", "Priority support", "support", False, False),
    ]
    feature_ids = {}
    for feature_key, name, category, default_enabled, requires_governance in feature_specs:
        feature_ids[feature_key] = execute_scalar(
            connection,
            """
            INSERT INTO platform.feature_definitions(
              feature_key, name, description, category, default_enabled, requires_human_governance
            )
            VALUES (:feature_key, :name, :description, :category, :default_enabled, :requires_governance)
            ON CONFLICT (feature_key) DO UPDATE
            SET name = EXCLUDED.name,
                description = EXCLUDED.description,
                category = EXCLUDED.category,
                default_enabled = EXCLUDED.default_enabled,
                requires_human_governance = EXCLUDED.requires_human_governance,
                updated_at = now()
            RETURNING id
            """,
            {
                "feature_key": feature_key,
                "name": name,
                "description": f"Local/test feature for {name}.",
                "category": category,
                "default_enabled": default_enabled,
                "requires_governance": requires_governance,
            },
        )

    plan_features = {
        "starter": ["tenant_user_management", "candidate_database", "requisition_management", "pipeline_management", "interview_scheduling"],
        "growth": ["tenant_user_management", "candidate_database", "requisition_management", "pipeline_management", "interview_scheduling", "offer_management", "ai_resume_screening"],
        "business": ["tenant_user_management", "candidate_database", "requisition_management", "pipeline_management", "interview_scheduling", "offer_management", "ai_resume_screening", "advanced_analytics", "audit_logs", "api_access"],
        "enterprise": list(feature_ids),
    }
    plan_quotas = {
        "starter": [10, 10, 1000, 100, 10, 25, 1, 10000],
        "growth": [50, 50, 10000, 1000, 100, 100, 5, 100000],
        "business": [250, 250, 50000, 5000, 500, 500, 20, 1000000],
        "enterprise": [1000, 1000, 250000, 50000, 5000, 5000, 100, 10000000],
    }
    quota_keys = [key for key, *_ in quota_specs]
    for plan_code, plan_id in plan_ids.items():
        for feature_key in plan_features[plan_code]:
            connection.execute(
                text(
                    """
                    INSERT INTO platform.plan_feature_entitlements(plan_id, feature_definition_id, is_enabled)
                    VALUES (:plan_id, :feature_id, true)
                    ON CONFLICT (plan_id, feature_definition_id) DO UPDATE SET is_enabled = true
                    """
                ),
                {"plan_id": plan_id, "feature_id": feature_ids[feature_key]},
            )
        for quota_key, hard_limit in zip(quota_keys, plan_quotas[plan_code], strict=True):
            connection.execute(
                text(
                    """
                    INSERT INTO platform.plan_quota_limits(plan_id, quota_definition_id, hard_limit, soft_limit, overage_unit_price)
                    VALUES (:plan_id, :quota_id, :hard_limit, :soft_limit, 0)
                    ON CONFLICT (plan_id, quota_definition_id) DO UPDATE
                    SET hard_limit = EXCLUDED.hard_limit, soft_limit = EXCLUDED.soft_limit, overage_unit_price = 0
                    """
                ),
                {
                    "plan_id": plan_id,
                    "quota_id": quota_ids[quota_key],
                    "hard_limit": Decimal(hard_limit),
                    "soft_limit": Decimal(hard_limit) * Decimal("0.8"),
                },
            )

    addon_specs = {
        "extra-ai-screening-pack": ("Extra AI Screening Pack", "Additional resume screening credits.", Decimal("99"), "ai_screenings_per_month", 500, "ai_resume_screening"),
        "extra-interview-minutes": ("Extra Interview Minutes", "Additional AI interview capacity.", Decimal("149"), "ai_interviews_per_month", 50, "ai_interviewer"),
        "additional-storage": ("Additional Storage", "Storage expansion for attachments.", Decimal("49"), "storage_gb", 100, "candidate_database"),
        "priority-support": ("Priority Support", "Escalated support response.", Decimal("199"), "support_sessions_per_month", 10, "priority_support"),
        "advanced-compliance-pack": ("Advanced Compliance Pack", "Additional compliance controls.", Decimal("299"), "api_requests_per_month", 100000, "audit_logs"),
    }
    addon_ids = {}
    for code, (name, description, price, quota_key, delta, feature_key) in addon_specs.items():
        addon_id = execute_scalar(
            connection,
            """
            INSERT INTO platform.plan_addons(code, name, description, status, price, currency, billing_interval)
            VALUES (:code, :name, :description, 'active', :price, 'USD', 'monthly')
            ON CONFLICT (code) DO UPDATE
            SET name = EXCLUDED.name,
                description = EXCLUDED.description,
                status = 'active',
                price = EXCLUDED.price,
                deleted_at = NULL,
                updated_at = now()
            RETURNING id
            """,
            {"code": code, "name": name, "description": description, "price": price},
        )
        addon_ids[code] = addon_id
        connection.execute(
            text(
                """
                INSERT INTO platform.addon_quota_deltas(addon_id, quota_definition_id, delta_value)
                VALUES (:addon_id, :quota_id, :delta_value)
                ON CONFLICT (addon_id, quota_definition_id) DO UPDATE SET delta_value = EXCLUDED.delta_value
                """
            ),
            {"addon_id": addon_id, "quota_id": quota_ids[quota_key], "delta_value": Decimal(delta)},
        )
        connection.execute(
            text(
                """
                INSERT INTO platform.addon_feature_entitlements(addon_id, feature_definition_id, is_enabled)
                VALUES (:addon_id, :feature_id, true)
                ON CONFLICT (addon_id, feature_definition_id) DO UPDATE SET is_enabled = true
                """
            ),
            {"addon_id": addon_id, "feature_id": feature_ids[feature_key]},
        )

    return {"plans": plan_ids, "quotas": quota_ids, "features": feature_ids, "addons": addon_ids, "infra": infra_ids}


def seed_tenants(connection: Connection, ids: dict[str, dict[str, object]], user_ids: dict[str, object]) -> dict[str, object]:
    tenants = {
        "active": ("Acme Talent Systems", "Acme Talent Systems Pvt Ltd", "corporate", "admin@acme.local.gnxthire.test", "active", "business", "IN", "dedicated_compute", "india-production"),
        "trial": ("BrightPath Hiring", "BrightPath Hiring Inc", "corporate", "admin@brightpath.local.gnxthire.test", "trial", "growth", "US", "shared", "us-production"),
        "suspended": ("Northstar Staffing", "Northstar Staffing LLP", "staffing_agency", "admin@northstar.local.gnxthire.test", "suspended", "starter", "IN", "shared", "india-sandbox"),
        "provisioning": ("Orbit RPO", "Orbit RPO Services", "rpo", "admin@orbit.local.gnxthire.test", "provisioning", "enterprise", "EU", "dedicated_db", "eu-production"),
        "churned": ("Legacy Search Co", "Legacy Search Company", "executive_search", "admin@legacy.local.gnxthire.test", "churned", "starter", "US", "shared", "us-production"),
        "deleted": ("Archived Talent Labs", "Archived Talent Labs", "corporate", "admin@archived.local.gnxthire.test", "deleted", "starter", "IN", "shared", "india-sandbox"),
    }
    tenant_ids = {}
    for key, (name, legal, tenant_type, email, status, plan, region, isolation, pool) in tenants.items():
        tenant_ids[key] = execute_scalar(
            connection,
            """
            WITH updated AS (
              UPDATE platform.tenants
              SET name = :name,
                  legal_entity_name = :legal,
                  tenant_type = CAST(:tenant_type AS tenant_type_enum),
                  plan_id = :plan_id,
                  status = CAST(:status AS tenant_status_enum),
                  isolation_tier = CAST(:isolation AS isolation_tier_enum),
                  region = CAST(:region AS region_enum),
                  data_residency_zone = :zone,
                  infra_pool_id = :infra_pool_id,
                  activated_at = CASE WHEN CAST(:status AS text) IN ('active','suspended','churned','deleted') THEN now() ELSE NULL END,
                  suspended_at = CASE WHEN CAST(:status AS text) = 'suspended' THEN now() ELSE NULL END,
                  churned_at = CASE WHEN CAST(:status AS text) = 'churned' THEN now() ELSE NULL END,
                  deleted_at = CASE WHEN CAST(:status AS text) = 'deleted' THEN now() ELSE NULL END,
                  updated_at = now()
              WHERE primary_admin_email = :email
              RETURNING id
            ),
            inserted AS (
              INSERT INTO platform.tenants(
                name, legal_entity_name, tenant_type, primary_admin_email, plan_id, status, isolation_tier,
                region, data_residency_zone, infra_pool_id, activated_at, suspended_at, churned_at, deleted_at
              )
              SELECT
                :name, :legal, CAST(:tenant_type AS tenant_type_enum), :email, :plan_id,
                CAST(:status AS tenant_status_enum), CAST(:isolation AS isolation_tier_enum),
                CAST(:region AS region_enum), :zone, :infra_pool_id,
                CASE WHEN CAST(:status AS text) IN ('active','suspended','churned','deleted') THEN now() ELSE NULL END,
                CASE WHEN CAST(:status AS text) = 'suspended' THEN now() ELSE NULL END,
                CASE WHEN CAST(:status AS text) = 'churned' THEN now() ELSE NULL END,
                CASE WHEN CAST(:status AS text) = 'deleted' THEN now() ELSE NULL END
              WHERE NOT EXISTS (SELECT 1 FROM updated)
              RETURNING id
            )
            SELECT id FROM updated
            UNION ALL
            SELECT id FROM inserted
            LIMIT 1
            """,
            {
                "name": name,
                "legal": legal,
                "tenant_type": tenant_type,
                "email": email,
                "plan_id": ids["plans"][plan],
                "status": status,
                "isolation": isolation,
                "region": region,
                "zone": f"{region.lower()}-local",
                "infra_pool_id": ids["infra"][pool],
            },
        )

    domain_specs = [
        ("active", "acme.local.gnxthire.test", True, "verified"),
        ("active", "careers-acme.local.gnxthire.test", False, "pending"),
        ("trial", "brightpath.local.gnxthire.test", True, "verified"),
        ("suspended", "northstar.local.gnxthire.test", True, "failed"),
        ("provisioning", "orbit.local.gnxthire.test", True, "pending"),
    ]
    for tenant_key, domain, is_primary, status in domain_specs:
        connection.execute(
            text(
                """
                INSERT INTO platform.tenant_domains(tenant_id, domain, is_primary, verification_status, verified_at)
                VALUES (:tenant_id, :domain, :is_primary, :status, CASE WHEN :status = 'verified' THEN now() ELSE NULL END)
                ON CONFLICT (domain) DO UPDATE
                SET tenant_id = EXCLUDED.tenant_id,
                    is_primary = EXCLUDED.is_primary,
                    verification_status = EXCLUDED.verification_status,
                    verified_at = EXCLUDED.verified_at
                """
            ),
            {"tenant_id": tenant_ids[tenant_key], "domain": domain, "is_primary": is_primary, "status": status},
        )

    tenant_password_hash = hash_password(PLATFORM_ADMIN_SEED_PASSWORD)
    connection.execute(
        text(
            """
            INSERT INTO tenant.users(tenant_id, email, display_name, status, password_hash, email_verified_at, is_tenant_admin)
            VALUES (:tenant_id, :email, 'Tenant Admin Smoke User', 'active', :password_hash, now(), true)
            ON CONFLICT (tenant_id, email) DO UPDATE
            SET status = 'active', password_hash = EXCLUDED.password_hash, email_verified_at = now(), updated_at = now()
            """
        ),
        {
            "tenant_id": tenant_ids["active"],
            "email": "tenant.admin@local.gnxthire.test",
            "password_hash": tenant_password_hash,
        },
    )

    return tenant_ids


def seed_remaining_modules(
    connection: Connection,
    ids: dict[str, dict[str, object]],
    tenant_ids: dict[str, object],
    user_ids: dict[str, object],
) -> None:
    actor_id = user_ids[PLATFORM_ADMIN_SEED_EMAIL]
    active_tenant_id = tenant_ids["active"]
    trial_tenant_id = tenant_ids["trial"]

    jobs = [
        ("seed-completed-job", active_tenant_id, "success", "success", None),
        ("seed-failed-job", active_tenant_id, "failed", "failed", "storage_config_failed"),
        ("seed-running-job", tenant_ids["provisioning"], "running", "running", None),
        ("seed-retryable-job", trial_tenant_id, "failed", "failed", "search_index_timeout"),
    ]
    for key, tenant_id, job_status, step_status, error in jobs:
        job_id = execute_scalar(
            connection,
            """
            INSERT INTO platform.tenant_provisioning_jobs(
              tenant_id, idempotency_key, status, started_at, completed_at, failed_at, error_code, error_message, retry_count
            )
            VALUES (
              :tenant_id, :key, CAST(:status AS sync_status_enum),
              CASE WHEN CAST(:status AS text) IN ('running','success','failed') THEN now() ELSE NULL END,
              CASE WHEN CAST(:status AS text) = 'success' THEN now() ELSE NULL END,
              CASE WHEN CAST(:status AS text) = 'failed' THEN now() ELSE NULL END,
              CAST(:error_code AS text), CAST(:error_message AS text),
              CASE WHEN CAST(:error_code AS text) IS NULL THEN 0 ELSE 1 END
            )
            ON CONFLICT (tenant_id, idempotency_key) DO UPDATE
            SET status = EXCLUDED.status,
                started_at = EXCLUDED.started_at,
                completed_at = EXCLUDED.completed_at,
                failed_at = EXCLUDED.failed_at,
                error_code = EXCLUDED.error_code,
                error_message = EXCLUDED.error_message,
                retry_count = EXCLUDED.retry_count,
                updated_at = now()
            RETURNING id
            """,
            {
                "tenant_id": tenant_id,
                "key": key,
                "status": job_status,
                "error_code": error,
                "error_message": error.replace("_", " ") if error else None,
            },
        )
        for step in ["create_tenant_schema", "seed_tenant_roles", "configure_storage", "configure_search_index", "configure_notification_settings"]:
            connection.execute(
                text(
                    """
                    INSERT INTO platform.tenant_provisioning_steps(
                      provisioning_job_id, step_key, status, started_at, completed_at, error_message
                    )
                    VALUES (
                      :job_id, :step, CAST(:status AS sync_status_enum),
                      CASE WHEN CAST(:status AS text) IN ('running','success','failed') THEN now() ELSE NULL END,
                      CASE WHEN CAST(:status AS text) = 'success' THEN now() ELSE NULL END,
                      CASE WHEN CAST(:status AS text) = 'failed' THEN :error_message ELSE NULL END
                    )
                    ON CONFLICT (provisioning_job_id, step_key) DO UPDATE
                    SET status = EXCLUDED.status,
                        started_at = EXCLUDED.started_at,
                        completed_at = EXCLUDED.completed_at,
                        error_message = EXCLUDED.error_message,
                        updated_at = now()
                    """
                ),
                {"job_id": job_id, "step": step, "status": step_status, "error_message": "Seeded failure step"},
            )

    for key, default_enabled, rollout, kill_switch in [
        ("ai_screening_enabled", True, 100, False),
        ("ai_interviewer_enabled", False, 25, False),
        ("new_pipeline_ui_enabled", True, 50, False),
        ("advanced_reporting_enabled", False, 0, False),
        ("maintenance_banner_enabled", False, 0, True),
    ]:
        flag_id = execute_scalar(
            connection,
            """
            INSERT INTO platform.feature_flag_registry(flag_key, description, default_enabled, rollout_percentage, kill_switch)
            VALUES (:key, :description, :default_enabled, :rollout, :kill_switch)
            ON CONFLICT (flag_key) DO UPDATE
            SET description = EXCLUDED.description,
                default_enabled = EXCLUDED.default_enabled,
                rollout_percentage = EXCLUDED.rollout_percentage,
                kill_switch = EXCLUDED.kill_switch,
                updated_at = now()
            RETURNING id
            """,
            {
                "key": key,
                "description": f"Local/test flag for {key}.",
                "default_enabled": default_enabled,
                "rollout": Decimal(rollout),
                "kill_switch": kill_switch,
            },
        )
        for tenant_id, enabled in [(active_tenant_id, True), (trial_tenant_id, False)]:
            connection.execute(
                text(
                    """
                    DELETE FROM platform.feature_flag_tenant_overrides
                    WHERE tenant_id = :tenant_id AND feature_flag_id = :flag_id AND expires_at IS NULL
                    """
                ),
                {"tenant_id": tenant_id, "flag_id": flag_id},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO platform.feature_flag_tenant_overrides(
                      tenant_id, feature_flag_id, is_enabled, reason, created_by_platform_user_id, expires_at
                    )
                    VALUES (:tenant_id, :flag_id, :enabled, 'Seeded local/test override', :actor_id, NULL)
                    ON CONFLICT (tenant_id, feature_flag_id, expires_at) DO UPDATE
                    SET is_enabled = EXCLUDED.is_enabled,
                        reason = EXCLUDED.reason,
                        created_by_platform_user_id = EXCLUDED.created_by_platform_user_id
                    """
                ),
                {"tenant_id": tenant_id, "flag_id": flag_id, "enabled": enabled, "actor_id": actor_id},
            )

    for reason, starts, expires, ended in [
        ("Investigate local test ticket", "-1 hour", "2 hours", None),
        ("Expired local diagnostic access", "-3 hours", "-1 hour", None),
        ("Completed local support access", "-2 hours", "1 hour", "now"),
    ]:
        connection.execute(
            text(
                """
                INSERT INTO platform.support_sessions(tenant_id, platform_user_id, reason, started_at, expires_at, ended_at)
                SELECT :tenant_id, :user_id, :reason, now() + (:starts)::interval, now() + (:expires)::interval,
                       CASE WHEN :ended = 'now' THEN now() ELSE NULL END
                WHERE NOT EXISTS (
                  SELECT 1 FROM platform.support_sessions WHERE tenant_id = :tenant_id AND reason = :reason
                )
                """
            ),
            {
                "tenant_id": active_tenant_id,
                "user_id": actor_id,
                "reason": reason,
                "starts": starts,
                "expires": expires,
                "ended": ended,
            },
        )

    for subject, priority, status in [
        ("Candidate import is delayed", "P2", "open"),
        ("Billing plan mismatch", "P3", "in_progress"),
        ("AI screening confidence drop", "P1", "waiting_on_customer"),
        ("SSO setup completed", "P4", "closed"),
    ]:
        connection.execute(
            text(
                """
                INSERT INTO platform.support_tickets(
                  tenant_id, requester_email, subject, description, priority, status, assigned_platform_user_id, closed_at
                )
                SELECT :tenant_id, :email, :subject, :description,
                       CAST(:priority AS ticket_priority_enum), CAST(:status AS ticket_status_enum), :actor_id,
                       CASE WHEN CAST(:status AS text) = 'closed' THEN now() ELSE NULL END
                WHERE NOT EXISTS (SELECT 1 FROM platform.support_tickets WHERE subject = :subject)
                """
            ),
            {
                "tenant_id": active_tenant_id,
                "email": "support-requester@acme.local.gnxthire.test",
                "subject": subject,
                "description": f"Seeded local/test support ticket: {subject}.",
                "priority": priority,
                "status": status,
                "actor_id": actor_id,
            },
        )

    for policy_key, name, severity, response, resolution in [
        ("p1-critical", "P1 Critical Response", "critical", 15, 240),
        ("p2-breached", "P2 Breach Response", "breached", 60, 720),
        ("p3-warning", "P3 Warning Response", "warning", 240, 2880),
    ]:
        connection.execute(
            text(
                """
                INSERT INTO platform.sla_policies(policy_key, name, severity, response_minutes, resolution_minutes)
                VALUES (:policy_key, :name, :severity, :response, :resolution)
                ON CONFLICT (policy_key) DO UPDATE
                SET name = EXCLUDED.name,
                    severity = EXCLUDED.severity,
                    response_minutes = EXCLUDED.response_minutes,
                    resolution_minutes = EXCLUDED.resolution_minutes,
                    updated_at = now()
                """
            ),
            {"policy_key": policy_key, "name": name, "severity": severity, "response": response, "resolution": resolution},
        )

    for framework, name, regions in [
        ("GDPR", "GDPR", ["EU", "UK"]),
        ("SOC2", "SOC 2", ["US", "CA"]),
        ("ISO27001", "ISO 27001", ["US", "EU", "IN"]),
        ("DPDPA", "DPDP India", ["IN"]),
    ]:
        framework_id = execute_scalar(
            connection,
            """
            INSERT INTO platform.compliance_frameworks(framework, display_name, description)
            VALUES (:framework, :name, :description)
            ON CONFLICT (framework) DO UPDATE
            SET display_name = EXCLUDED.display_name, description = EXCLUDED.description
            RETURNING id
            """,
            {"framework": framework, "name": name, "description": f"Seeded local/test {name} framework."},
        )
        for region in regions:
            connection.execute(
                text(
                    """
                    INSERT INTO platform.compliance_framework_regions(framework_id, region)
                    VALUES (:framework_id, :region)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"framework_id": framework_id, "region": region},
            )
        connection.execute(
            text(
                """
                INSERT INTO platform.tenant_compliance_frameworks(tenant_id, framework_id, disabled_at)
                VALUES (:tenant_id, :framework_id, NULL)
                ON CONFLICT (tenant_id, framework_id, disabled_at) DO NOTHING
                """
            ),
            {"tenant_id": active_tenant_id, "framework_id": framework_id},
        )

    model_ids = {}
    for provider, model_key, name, tokens, embeddings, audio, video in [
        ("openai", "resume-screening-local-v1", "Resume Screening Model", 128000, False, False, False),
        ("openai", "candidate-ranking-local-v1", "Candidate Ranking Model", 128000, False, False, False),
        ("openai", "interview-scoring-local-v1", "Interview Scoring Model", 128000, False, True, True),
    ]:
        model_ids[model_key] = execute_scalar(
            connection,
            """
            INSERT INTO platform.ai_model_definitions(
              provider, model_key, display_name, max_context_tokens, supports_embeddings, supports_audio, supports_video, is_active
            )
            VALUES (:provider, :model_key, :name, :tokens, :embeddings, :audio, :video, true)
            ON CONFLICT (provider, model_key) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                max_context_tokens = EXCLUDED.max_context_tokens,
                supports_embeddings = EXCLUDED.supports_embeddings,
                supports_audio = EXCLUDED.supports_audio,
                supports_video = EXCLUDED.supports_video,
                is_active = true,
                updated_at = now()
            RETURNING id
            """,
            {
                "provider": provider,
                "model_key": model_key,
                "name": name,
                "tokens": tokens,
                "embeddings": embeddings,
                "audio": audio,
                "video": video,
            },
        )
    connection.execute(
        text(
            """
            INSERT INTO platform.ai_model_region_restrictions(model_definition_id, region, restriction_reason)
            VALUES (:model_id, 'EU', 'Seeded local/test regional restriction')
            ON CONFLICT (model_definition_id, region) DO UPDATE
            SET restriction_reason = EXCLUDED.restriction_reason
            """
        ),
        {"model_id": model_ids["interview-scoring-local-v1"]},
    )
    connection.execute(
        text(
            """
            DELETE FROM platform.ai_quality_metrics
            WHERE tenant_id = :tenant_id
              AND action_type = 'resume_screening'
              AND model_definition_id = :model_id
              AND sample_period_start = CURRENT_DATE - 30
              AND sample_period_end = CURRENT_DATE
            """
        ),
        {"tenant_id": active_tenant_id, "model_id": model_ids["resume-screening-local-v1"]},
    )
    connection.execute(
        text(
            """
            INSERT INTO platform.ai_quality_metrics(
              tenant_id, action_type, model_definition_id, sample_period_start, sample_period_end,
              sample_count, human_override_rate, bias_flag_rate, avg_confidence
            )
            VALUES (:tenant_id, 'resume_screening', :model_id, CURRENT_DATE - 30, CURRENT_DATE, 250, 7.5, 1.25, 0.87)
            """
        ),
        {"tenant_id": active_tenant_id, "model_id": model_ids["resume-screening-local-v1"]},
    )
    alert_id = execute_scalar(
        connection,
        """
        WITH updated AS (
          UPDATE platform.ai_governance_alerts
          SET severity = 'warning',
              title = 'Resume screening override rate increased',
              description = 'Seeded alert for local AI governance testing.',
              status = 'open',
              resolved_at = NULL
          WHERE tenant_id = :tenant_id
            AND alert_key = 'seeded_resume_screening_override_rate'
          RETURNING id
        ),
        inserted AS (
          INSERT INTO platform.ai_governance_alerts(
            tenant_id, action_type, severity, alert_key, title, description, status
          )
          SELECT
            :tenant_id, 'resume_screening', 'warning', 'seeded_resume_screening_override_rate',
            'Resume screening override rate increased',
            'Seeded alert for local AI governance testing.', 'open'
          WHERE NOT EXISTS (SELECT 1 FROM updated)
          RETURNING id
        )
        SELECT id FROM updated
        UNION ALL
        SELECT id FROM inserted
        LIMIT 1
        """,
        {"tenant_id": active_tenant_id},
    )
    connection.execute(
        text(
            """
            INSERT INTO platform.api_versions(version_label, released_at, migration_guide_url)
            VALUES ('v1-local', now() - interval '30 days', 'https://local.gnxthire.test/docs/api/v1')
            ON CONFLICT (version_label) DO UPDATE
            SET migration_guide_url = EXCLUDED.migration_guide_url
            """
        )
    )
    connection.execute(
        text(
            """
            INSERT INTO platform.deployments(environment, version_label, rollout_strategy, started_at, completed_at, status)
            SELECT 'staging', 'v1-local', 'rolling', now() - interval '2 hours', now() - interval '1 hour', 'succeeded'
            WHERE NOT EXISTS (
              SELECT 1 FROM platform.deployments WHERE environment = 'staging' AND version_label = 'v1-local'
            )
            """
        )
    )
    slo_id = execute_scalar(
        connection,
        """
        INSERT INTO platform.slo_definitions(slo_key, service_name, objective_percent, window_days)
        VALUES ('platform-admin-api-availability', 'platform-admin-api', 99.9000, 30)
        ON CONFLICT (slo_key) DO UPDATE
        SET service_name = EXCLUDED.service_name,
            objective_percent = EXCLUDED.objective_percent,
            window_days = EXCLUDED.window_days,
            updated_at = now()
        RETURNING id
        """,
        {},
    )
    connection.execute(
        text(
            """
            INSERT INTO platform.error_budget_status(slo_definition_id, period_start, period_end, consumed_percent, burn_rate)
            VALUES (:slo_id, CURRENT_DATE - 30, CURRENT_DATE, 22.5, 0.85)
            ON CONFLICT (slo_definition_id, period_start, period_end) DO UPDATE
            SET consumed_percent = EXCLUDED.consumed_percent, burn_rate = EXCLUDED.burn_rate
            """
        ),
        {"slo_id": slo_id},
    )
    connection.execute(
        text(
            """
            INSERT INTO platform.audit_logs(
              tenant_id, actor_type, actor_platform_user_id, action_key, object_schema, object_table,
              object_id, after_state, request_id
            )
            SELECT
              NULL, 'platform_user', :actor_id, 'platform_admin.seed_data_refreshed',
              'platform', 'tenants', NULL, '{"seeded": true}'::jsonb, 'seed-platform-admin'
            WHERE NOT EXISTS (
              SELECT 1 FROM platform.audit_logs WHERE request_id = 'seed-platform-admin'
            )
            """
        ),
        {"tenant_id": active_tenant_id, "actor_id": actor_id},
    )


def seed() -> None:
    require_local_or_test()
    engine = create_sync_engine()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))
        role_ids = seed_access_control(connection)
        user_ids = seed_platform_users(connection, role_ids)
        ids = seed_catalogue(connection)
        tenant_ids = seed_tenants(connection, ids, user_ids)
        seed_remaining_modules(connection, ids, tenant_ids, user_ids)

    print("Seeded Platform Admin local/test data.")
    print(f"Local password: {PLATFORM_ADMIN_SEED_PASSWORD}")
    for user in USERS:
        print(f"- {user.email} ({user.role_key})")
    print("- tenant.admin@local.gnxthire.test (tenant-user rejection smoke)")


if __name__ == "__main__":
    seed()
