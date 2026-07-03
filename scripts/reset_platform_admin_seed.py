from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy import text

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "packages" / "backend-common" / "src"))
sys.path.insert(0, str(REPOSITORY_ROOT / "services" / "identity" / "src"))

from gnxthire_common.config import get_settings
from gnxthire_common.db import create_sync_engine
from gnxthire_identity.config import get_identity_settings


def require_local_or_test() -> None:
    settings = get_settings()
    identity_settings = get_identity_settings()
    if settings.environment not in {"local", "test"} or identity_settings.app_env not in {"local", "test"}:
        raise SystemExit("Refusing to reset Platform Admin seed data outside local/test environments.")


def reset() -> None:
    require_local_or_test()
    engine = create_sync_engine()
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))

        connection.execute(text("DELETE FROM platform.ai_governance_alert_evidence WHERE alert_id IN (SELECT id FROM platform.ai_governance_alerts WHERE alert_key LIKE 'seeded_%')"))
        connection.execute(text("DELETE FROM platform.ai_governance_alerts WHERE alert_key LIKE 'seeded_%'"))
        connection.execute(text("DELETE FROM platform.ai_quality_metrics WHERE tenant_id IN (SELECT id FROM platform.tenants WHERE primary_admin_email::text LIKE '%@%.local.gnxthire.test')"))
        connection.execute(text("DELETE FROM platform.ai_model_region_restrictions WHERE model_definition_id IN (SELECT id FROM platform.ai_model_definitions WHERE model_key::text LIKE '%-local-v1')"))
        connection.execute(text("DELETE FROM platform.ai_model_definitions WHERE model_key::text LIKE '%-local-v1'"))
        connection.execute(text("DELETE FROM platform.error_budget_status WHERE slo_definition_id IN (SELECT id FROM platform.slo_definitions WHERE slo_key::text = 'platform-admin-api-availability')"))
        connection.execute(text("DELETE FROM platform.slo_definitions WHERE slo_key::text = 'platform-admin-api-availability'"))
        connection.execute(text("DELETE FROM platform.deployments WHERE version_label = 'v1-local'"))
        connection.execute(text("DELETE FROM platform.api_versions WHERE version_label::text = 'v1-local'"))
        connection.execute(text("DELETE FROM platform.tenant_compliance_frameworks WHERE tenant_id IN (SELECT id FROM platform.tenants WHERE primary_admin_email::text LIKE '%@%.local.gnxthire.test')"))
        connection.execute(text("DELETE FROM platform.compliance_framework_regions WHERE framework_id IN (SELECT id FROM platform.compliance_frameworks WHERE framework IN ('GDPR','SOC2','ISO27001','DPDPA'))"))
        connection.execute(text("DELETE FROM platform.compliance_frameworks WHERE framework IN ('GDPR','SOC2','ISO27001','DPDPA')"))
        connection.execute(text("DELETE FROM platform.sla_policies WHERE policy_key::text IN ('p1-critical','p2-breached','p3-warning')"))
        connection.execute(text("DELETE FROM platform.support_tickets WHERE requester_email::text LIKE '%@%.local.gnxthire.test' OR subject IN ('Candidate import is delayed','Billing plan mismatch','AI screening confidence drop','SSO setup completed')"))
        connection.execute(text("DELETE FROM platform.support_sessions WHERE reason LIKE '%local%'"))
        connection.execute(text("DELETE FROM platform.feature_flag_tenant_overrides WHERE tenant_id IN (SELECT id FROM platform.tenants WHERE primary_admin_email::text LIKE '%@%.local.gnxthire.test')"))
        connection.execute(text("DELETE FROM platform.feature_flag_registry WHERE flag_key::text IN ('ai_screening_enabled','ai_interviewer_enabled','new_pipeline_ui_enabled','advanced_reporting_enabled','maintenance_banner_enabled')"))
        connection.execute(text("DELETE FROM platform.tenant_provisioning_steps WHERE provisioning_job_id IN (SELECT id FROM platform.tenant_provisioning_jobs WHERE idempotency_key LIKE 'seed-%')"))
        connection.execute(text("DELETE FROM platform.tenant_provisioning_jobs WHERE idempotency_key LIKE 'seed-%'"))
        connection.execute(text("DELETE FROM tenant.users WHERE email::text = 'tenant.admin@local.gnxthire.test'"))
        connection.execute(text("DELETE FROM platform.tenant_domains WHERE domain::text LIKE '%.local.gnxthire.test'"))
        connection.execute(text("DELETE FROM platform.tenant_lifecycle_events WHERE tenant_id IN (SELECT id FROM platform.tenants WHERE primary_admin_email::text LIKE '%@%.local.gnxthire.test')"))
        connection.execute(
            text(
                """
                UPDATE platform.tenants
                SET status = 'deleted',
                    deleted_at = COALESCE(deleted_at, now()),
                    updated_at = now()
                WHERE primary_admin_email::text LIKE '%@%.local.gnxthire.test'
                """
            )
        )
        connection.execute(text("DELETE FROM platform.addon_feature_entitlements WHERE addon_id IN (SELECT id FROM platform.plan_addons WHERE code::text IN ('extra-ai-screening-pack','extra-interview-minutes','additional-storage','priority-support','advanced-compliance-pack'))"))
        connection.execute(text("DELETE FROM platform.addon_quota_deltas WHERE addon_id IN (SELECT id FROM platform.plan_addons WHERE code::text IN ('extra-ai-screening-pack','extra-interview-minutes','additional-storage','priority-support','advanced-compliance-pack'))"))
        connection.execute(text("DELETE FROM platform.plan_addons WHERE code::text IN ('extra-ai-screening-pack','extra-interview-minutes','additional-storage','priority-support','advanced-compliance-pack')"))
        connection.execute(text("DELETE FROM platform.plan_feature_entitlements WHERE plan_id IN (SELECT id FROM platform.plans WHERE code::text IN ('starter','growth','business','enterprise'))"))
        connection.execute(text("DELETE FROM platform.plan_quota_limits WHERE plan_id IN (SELECT id FROM platform.plans WHERE code::text IN ('starter','growth','business','enterprise'))"))
        connection.execute(text("DELETE FROM platform.feature_definitions WHERE feature_key::text IN ('tenant_user_management','candidate_database','requisition_management','pipeline_management','ai_resume_screening','ai_interviewer','interview_scheduling','offer_management','agency_portal','client_portal','advanced_analytics','audit_logs','custom_branding','api_access','priority_support')"))
        connection.execute(text("DELETE FROM platform.quota_definitions WHERE quota_key::text IN ('users_per_tenant','jobs_per_month','candidates_per_month','ai_screenings_per_month','ai_interviews_per_month','storage_gb','support_sessions_per_month','api_requests_per_month')"))
        connection.execute(
            text(
                """
                UPDATE platform.plans
                SET status = 'archived', deleted_at = COALESCE(deleted_at, now()), updated_at = now()
                WHERE code::text IN ('starter','growth','business','enterprise')
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE platform.infra_pools
                SET status = 'retired', updated_at = now()
                WHERE pool_key::text IN ('india-production','india-sandbox','us-production','eu-production')
                """
            )
        )
        connection.execute(text("DELETE FROM platform.platform_user_roles WHERE platform_user_id IN (SELECT id FROM platform.platform_users WHERE email::text LIKE '%@local.gnxthire.test')"))
        connection.execute(text("DELETE FROM platform.platform_user_mfa_factors WHERE platform_user_id IN (SELECT id FROM platform.platform_users WHERE email::text LIKE '%@local.gnxthire.test')"))
        connection.execute(text("DELETE FROM platform.platform_user_sessions WHERE platform_user_id IN (SELECT id FROM platform.platform_users WHERE email::text LIKE '%@local.gnxthire.test')"))
        connection.execute(text("DELETE FROM platform.platform_password_reset_tokens WHERE platform_user_id IN (SELECT id FROM platform.platform_users WHERE email::text LIKE '%@local.gnxthire.test')"))
        connection.execute(text("DELETE FROM platform.platform_email_verification_tokens WHERE platform_user_id IN (SELECT id FROM platform.platform_users WHERE email::text LIKE '%@local.gnxthire.test')"))
        connection.execute(text("DELETE FROM platform.platform_users WHERE email::text LIKE '%@local.gnxthire.test'"))

    print("Reset Platform Admin local/test seed data.")


if __name__ == "__main__":
    reset()
