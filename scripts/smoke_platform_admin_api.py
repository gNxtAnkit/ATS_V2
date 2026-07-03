from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import text

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = REPOSITORY_ROOT / "artifacts"
COVERAGE_PATH = ARTIFACTS_DIR / "platform-admin-api-coverage.md"
sys.path.insert(0, str(REPOSITORY_ROOT / "packages" / "backend-common" / "src"))

from gnxthire_common.db import create_sync_engine


IDENTITY_BASE_URL = os.getenv("IDENTITY_API_BASE_URL", "http://localhost:8001").rstrip("/")
PLATFORM_ADMIN_BASE_URL = os.getenv("PLATFORM_ADMIN_API_BASE_URL", "http://localhost:8002").rstrip("/")
SMOKE_MODE = os.getenv("PLATFORM_ADMIN_SMOKE_MODE", "http")
_IDENTITY_CLIENT: Any = None
_PLATFORM_CLIENT: Any = None


class PlatformAdminSmokeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    super_admin_email: str = Field(
        default="ankit@gnxtsystems.com",
        validation_alias="PLATFORM_ADMIN_SEED_EMAIL",
    )
    seed_password: str = Field(
        default="LocalTest@12345",
        validation_alias=AliasChoices("PLATFORM_ADMIN_SEED_PASSWORD", "PLATFORM_ADMIN_LOCAL_PASSWORD"),
    )


SMOKE_SETTINGS = PlatformAdminSmokeSettings()
SUPER_ADMIN_EMAIL = SMOKE_SETTINGS.super_admin_email.strip().lower()
LOCAL_PASSWORD = SMOKE_SETTINGS.seed_password


@dataclass(frozen=True)
class ApiResponse:
    status: int
    body: Any


@dataclass(frozen=True)
class SmokeResult:
    method: str
    endpoint: str
    status: str
    auth_tested: str
    permission_tested: str
    audit_tested: str
    notes: str


class SmokeFailure(RuntimeError):
    pass


def request_json(
    base_url: str,
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    expected: set[int] | None = None,
) -> ApiResponse:
    expected = expected or {200}
    headers = {"Accept": "application/json", "X-Request-ID": "smoke-platform-admin-api"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if SMOKE_MODE == "inprocess":
        client = _IDENTITY_CLIENT if base_url == IDENTITY_BASE_URL else _PLATFORM_CLIENT
        if client is None:
            raise SmokeFailure("In-process smoke client is not initialized.")
        response = client.request(method, path, headers=headers, json=body)
        parsed = response.json() if response.content else None
        if response.status_code not in expected:
            raise SmokeFailure(f"{method} {path} expected {sorted(expected)}, got {response.status_code}: {parsed}")
        return ApiResponse(status=response.status_code, body=parsed)

    request = Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            text = response.read().decode("utf-8")
            parsed = json.loads(text) if text else None
            status = response.status
    except HTTPError as exc:
        text = exc.read().decode("utf-8")
        parsed = json.loads(text) if text else None
        status = exc.code
    except URLError as exc:
        raise SmokeFailure(f"Cannot reach {base_url}: {exc}") from exc

    if status not in expected:
        raise SmokeFailure(f"{method} {path} expected {sorted(expected)}, got {status}: {parsed}")
    return ApiResponse(status=status, body=parsed)


def login_platform_admin(email: str) -> str:
    response = request_json(
        IDENTITY_BASE_URL,
        "POST",
        "/v1/identity/platform-admin/auth/login",
        body={"email": email, "password": LOCAL_PASSWORD},
    )
    return response.body["tokens"]["access_token"]


def login_tenant_user() -> str:
    response = request_json(
        IDENTITY_BASE_URL,
        "POST",
        "/v1/identity/auth/login",
        body={"email": "tenant.admin@local.gnxthire.test", "password": LOCAL_PASSWORD},
    )
    return response.body["tokens"]["access_token"]


def load_seed_ids() -> dict[str, Any]:
    engine = create_sync_engine()
    with engine.begin() as connection:
        def scalar(sql: str, params: dict[str, object] | None = None) -> Any:
            return connection.execute(text(sql), params or {}).scalar_one()

        def scalar_optional(sql: str, params: dict[str, object] | None = None) -> Any:
            return connection.execute(text(sql), params or {}).scalar_one_or_none()

        return {
            "tenant_id": str(scalar("SELECT id FROM platform.tenants WHERE primary_admin_email = 'admin@acme.local.gnxthire.test' AND deleted_at IS NULL ORDER BY updated_at DESC LIMIT 1")),
            "trial_tenant_id": str(scalar("SELECT id FROM platform.tenants WHERE primary_admin_email = 'admin@brightpath.local.gnxthire.test' AND deleted_at IS NULL ORDER BY updated_at DESC LIMIT 1")),
            "domain_id": str(scalar("SELECT id FROM platform.tenant_domains WHERE domain = 'brightpath.local.gnxthire.test'")),
            "provisioning_job_id": str(scalar("SELECT id FROM platform.tenant_provisioning_jobs WHERE idempotency_key = 'seed-retryable-job'")),
            "infra_pool_id": str(scalar("SELECT id FROM platform.infra_pools WHERE pool_key = 'india-sandbox'")),
            "plan_id": str(scalar("SELECT id FROM platform.plans WHERE code = 'starter'")),
            "quota_id": str(scalar("SELECT id FROM platform.quota_definitions WHERE quota_key = 'users_per_tenant'")),
            "feature_id": str(scalar("SELECT id FROM platform.feature_definitions WHERE feature_key = 'ai_resume_screening'")),
            "addon_id": str(scalar("SELECT id FROM platform.plan_addons WHERE code = 'extra-ai-screening-pack'")),
            "feature_flag_id": str(scalar("SELECT id FROM platform.feature_flag_registry WHERE flag_key = 'ai_screening_enabled'")),
            "platform_user_id": str(scalar("SELECT id FROM platform.platform_users WHERE email = 'support.admin@local.gnxthire.test'")),
            "role_id": str(scalar("SELECT id FROM platform.platform_roles WHERE role_key = 'support_admin'")),
            "permission_id": str(scalar("SELECT id FROM platform.platform_permissions WHERE permission_key = 'platform.tenant.read'")),
            "support_session_id": str(scalar("SELECT id FROM platform.support_sessions WHERE reason = 'Investigate local test ticket'")),
            "ticket_id": str(scalar("SELECT id FROM platform.support_tickets WHERE subject = 'Candidate import is delayed'")),
            "sla_policy_id": str(scalar("SELECT id FROM platform.sla_policies WHERE policy_key = 'p1-critical'")),
            "framework_id": str(scalar("SELECT id FROM platform.compliance_frameworks WHERE framework = 'GDPR'")),
            "model_id": str(scalar("SELECT id FROM platform.ai_model_definitions WHERE model_key = 'resume-screening-local-v1'")),
            "alert_id": str(scalar("SELECT id FROM platform.ai_governance_alerts WHERE alert_key = 'seeded_resume_screening_override_rate' ORDER BY opened_at DESC LIMIT 1")),
            "api_version_id": str(scalar("SELECT id FROM platform.api_versions WHERE version_label = 'v1-local'")),
            "deployment_id": str(scalar("SELECT id FROM platform.deployments WHERE version_label = 'v1-local' ORDER BY started_at DESC LIMIT 1")),
            "slo_id": str(scalar("SELECT id FROM platform.slo_definitions WHERE slo_key = 'platform-admin-api-availability'")),
            "audit_id": str(scalar_optional("SELECT id FROM platform.audit_logs WHERE request_id = 'seed-platform-admin' ORDER BY occurred_at DESC LIMIT 1")),
        }


def smoke_body(name: str, ids: dict[str, Any], suffix: str) -> dict[str, Any] | None:
    future = (datetime.now(UTC) + timedelta(hours=4)).isoformat()
    released = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    bodies: dict[str, dict[str, Any] | None] = {
        "POST /v1/platform-admin/tenants": {
            "name": f"Smoke Tenant {suffix}",
            "tenant_type": "corporate",
            "primary_admin_email": f"smoke-{suffix}@local.gnxthire.test",
            "plan_id": ids["plan_id"],
            "region": "IN",
            "infra_pool_id": ids["infra_pool_id"],
            "idempotency_key": f"smoke-tenant-{suffix}",
        },
        "PATCH /v1/platform-admin/tenants/{tenant_id}": {"legal_entity_name": "Acme Talent Systems Pvt Ltd"},
        "POST /v1/platform-admin/tenants/{tenant_id}/activate": {"reason": "Smoke activate"},
        "POST /v1/platform-admin/tenants/{tenant_id}/suspend": {"reason": "Smoke suspend"},
        "POST /v1/platform-admin/tenants/{tenant_id}/reactivate": {"reason": "Smoke reactivate"},
        "POST /v1/platform-admin/tenants/{tenant_id}/churn": {"reason": "Smoke churn"},
        "POST /v1/platform-admin/tenants/{tenant_id}/soft-delete": {"reason": "Smoke soft delete"},
        "POST /v1/platform-admin/tenants/{tenant_id}/restore": {"reason": "Smoke restore"},
        "POST /v1/platform-admin/tenants/{tenant_id}/domains": {"domain": f"smoke-{suffix}.local.gnxthire.test", "is_primary": False},
        "PATCH /v1/platform-admin/tenants/{tenant_id}/domains/{domain_id}": {"verification_status": "pending"},
        "POST /v1/platform-admin/tenants/{tenant_id}/domains/{domain_id}/verify": {"reason": "Smoke verify"},
        "POST /v1/platform-admin/provisioning-jobs/{job_id}/retry": None,
        "POST /v1/platform-admin/provisioning-jobs/{job_id}/cancel": None,
        "POST /v1/platform-admin/infra-pools": {
            "pool_key": f"smoke-pool-{suffix}",
            "region": "IN",
            "isolation_tier": "shared",
            "database_cluster_ref": f"pg-smoke-{suffix}",
        },
        "PATCH /v1/platform-admin/infra-pools/{infra_pool_id}": {"search_cluster_ref": "os-in-sandbox"},
        "POST /v1/platform-admin/infra-pools/{infra_pool_id}/activate": None,
        "POST /v1/platform-admin/infra-pools/{infra_pool_id}/deactivate": None,
        "POST /v1/platform-admin/plans": {
            "code": f"smoke-plan-{suffix}",
            "name": f"Smoke Plan {suffix}",
            "billing_interval": "monthly",
            "base_price": "1.00",
            "currency": "USD",
            "min_seats": 1,
            "max_seats": 5,
            "trial_days": 1,
        },
        "PATCH /v1/platform-admin/plans/{plan_id}": {"description": "Smoke-updated starter plan."},
        "POST /v1/platform-admin/plans/{plan_id}/activate": None,
        "POST /v1/platform-admin/plans/{plan_id}/retire": None,
        "PUT /v1/platform-admin/plans/{plan_id}/features": {"items": [{"feature_definition_id": ids["feature_id"], "is_enabled": True}]},
        "PUT /v1/platform-admin/plans/{plan_id}/quotas": {"items": [{"quota_definition_id": ids["quota_id"], "hard_limit": "10", "soft_limit": "8", "overage_unit_price": "0"}]},
        "POST /v1/platform-admin/quotas": {"quota_key": f"smoke_quota_{suffix}", "display_name": "Smoke quota", "unit": "items", "reset_period": "monthly", "is_metered": True},
        "PATCH /v1/platform-admin/quotas/{quota_definition_id}": {"display_name": "Users per tenant"},
        "POST /v1/platform-admin/features": {"feature_key": f"smoke_feature_{suffix}", "name": "Smoke feature", "category": "core"},
        "PATCH /v1/platform-admin/features/{feature_definition_id}": {"description": "Smoke-updated feature."},
        "POST /v1/platform-admin/addons": {"code": f"smoke-addon-{suffix}", "name": "Smoke add-on", "price": "1.00", "currency": "USD", "billing_interval": "monthly"},
        "PATCH /v1/platform-admin/addons/{addon_id}": {"description": "Smoke-updated add-on."},
        "POST /v1/platform-admin/addons/{addon_id}/activate": None,
        "POST /v1/platform-admin/addons/{addon_id}/retire": None,
        "PUT /v1/platform-admin/addons/{addon_id}/quota-deltas": {"items": [{"quota_definition_id": ids["quota_id"], "delta_value": "5"}]},
        "PUT /v1/platform-admin/addons/{addon_id}/features": {"items": [{"feature_definition_id": ids["feature_id"], "is_enabled": True}]},
        "POST /v1/platform-admin/feature-flags": {"flag_key": f"smoke_flag_{suffix}", "description": "Smoke flag", "default_enabled": False, "rollout_percentage": "0", "kill_switch": False},
        "PATCH /v1/platform-admin/feature-flags/{flag_id}": {"description": "Smoke-updated flag."},
        "PUT /v1/platform-admin/feature-flags/{flag_id}/tenant-overrides/{tenant_id}": {"is_enabled": True, "reason": "Smoke override"},
        "POST /v1/platform-admin/access-control/users": {"email": f"smoke-admin-{suffix}@local.gnxthire.test", "display_name": "Smoke Admin"},
        "PATCH /v1/platform-admin/access-control/users/{platform_user_id}": {"display_name": "Support Admin"},
        "POST /v1/platform-admin/access-control/users/{platform_user_id}/activate": None,
        "POST /v1/platform-admin/access-control/users/{platform_user_id}/deactivate": None,
        "POST /v1/platform-admin/access-control/users/{platform_user_id}/lock": None,
        "POST /v1/platform-admin/access-control/users/{platform_user_id}/unlock": None,
        "PUT /v1/platform-admin/access-control/users/{platform_user_id}/roles": {"role_ids": [ids["role_id"]]},
        "POST /v1/platform-admin/access-control/roles": {"role_key": f"smoke_role_{suffix}", "name": "Smoke Role"},
        "PATCH /v1/platform-admin/access-control/roles/{role_id}": {"description": "Smoke-updated role."},
        "PUT /v1/platform-admin/access-control/roles/{role_id}/permissions": {"permission_ids": [ids["permission_id"]]},
        "POST /v1/platform-admin/support-sessions": {"tenant_id": ids["tenant_id"], "reason": f"Smoke support {suffix}", "expires_at": future},
        "POST /v1/platform-admin/support-sessions/{support_session_id}/end": None,
        "POST /v1/platform-admin/support-tickets": {"tenant_id": ids["tenant_id"], "title": f"Smoke ticket {suffix}", "description": "Smoke ticket", "priority": "P3"},
        "PATCH /v1/platform-admin/support-tickets/{ticket_id}": {"description": "Smoke-updated ticket."},
        "POST /v1/platform-admin/support-tickets/{ticket_id}/assign": {"assigned_platform_user_id": ids["platform_user_id"]},
        "POST /v1/platform-admin/support-tickets/{ticket_id}/close": {"resolution_summary": "Smoke close"},
        "POST /v1/platform-admin/sla-policies": {"policy_key": f"smoke-sla-{suffix}", "name": "Smoke SLA", "severity": "warning", "response_minutes": 10, "resolution_minutes": 60},
        "PATCH /v1/platform-admin/sla-policies/{sla_policy_id}": {"name": "P1 Critical Response"},
        "POST /v1/platform-admin/compliance/frameworks": {"framework": "CCPA", "display_name": "CCPA", "description": "Smoke framework"},
        "PATCH /v1/platform-admin/compliance/frameworks/{framework_id}": {"description": "Smoke-updated framework."},
        "PUT /v1/platform-admin/compliance/frameworks/{framework_id}/regions": {"regions": ["EU", "UK"]},
        "PUT /v1/platform-admin/tenants/{tenant_id}/compliance-frameworks": {"framework_ids": [ids["framework_id"]]},
        "POST /v1/platform-admin/ai/models": {"provider": "openai", "model_key": f"smoke-model-{suffix}", "display_name": "Smoke model", "max_context_tokens": 4096},
        "PATCH /v1/platform-admin/ai/models/{model_id}": {"display_name": "Resume Screening Model"},
        "PUT /v1/platform-admin/ai/models/{model_id}/region-restrictions": {"regions": ["EU"]},
        "POST /v1/platform-admin/ai/governance-alerts/{alert_id}/acknowledge": None,
        "POST /v1/platform-admin/ai/governance-alerts/{alert_id}/resolve": None,
        "POST /v1/platform-admin/api-versions": {"version_label": f"smoke-v-{suffix}", "released_at": released},
        "PATCH /v1/platform-admin/api-versions/{api_version_id}": {"migration_guide_url": "https://local.gnxthire.test/docs/smoke"},
        "POST /v1/platform-admin/slo-definitions": {"slo_key": f"smoke-slo-{suffix}", "service_name": "platform-admin-api", "objective_percent": "99.5", "window_days": 30},
        "PATCH /v1/platform-admin/slo-definitions/{slo_id}": {"service_name": "platform-admin-api"},
    }
    return bodies.get(name)


def concrete_path(template: str, ids: dict[str, Any]) -> str:
    replacements = {
        "{tenant_id}": ids["tenant_id"],
        "{domain_id}": ids["domain_id"],
        "{job_id}": ids["provisioning_job_id"],
        "{infra_pool_id}": ids["infra_pool_id"],
        "{plan_id}": ids["plan_id"],
        "{quota_definition_id}": ids["quota_id"],
        "{feature_definition_id}": ids["feature_id"],
        "{addon_id}": ids["addon_id"],
        "{flag_id}": ids["feature_flag_id"],
        "{platform_user_id}": ids["platform_user_id"],
        "{role_id}": ids["role_id"],
        "{support_session_id}": ids["support_session_id"],
        "{ticket_id}": ids["ticket_id"],
        "{sla_policy_id}": ids["sla_policy_id"],
        "{framework_id}": ids["framework_id"],
        "{model_id}": ids["model_id"],
        "{alert_id}": ids["alert_id"],
        "{api_version_id}": ids["api_version_id"],
        "{deployment_id}": ids["deployment_id"],
        "{slo_id}": ids["slo_id"],
        "{audit_log_id}": ids["audit_id"],
    }
    path = template
    for placeholder, value in replacements.items():
        path = path.replace(placeholder, value)
    return path


def route_catalog(token: str) -> list[tuple[str, str]]:
    response = request_json(PLATFORM_ADMIN_BASE_URL, "GET", "/openapi.json", token=token)
    routes: list[tuple[str, str]] = []
    for path, operations in response.body["paths"].items():
        if not path.startswith("/v1/platform-admin"):
            continue
        if path.startswith("/v1/platform-admin/users") or path.startswith("/v1/platform-admin/roles") or path == "/v1/platform-admin/permissions":
            continue
        for method in operations:
            routes.append((method.upper(), path))
    return sorted(routes)


def run_smoke() -> list[SmokeResult]:
    ids = load_seed_ids()
    super_token = login_platform_admin(SUPER_ADMIN_EMAIL)
    auditor_token = login_platform_admin("auditor@local.gnxthire.test")
    tenant_token = login_tenant_user()
    suffix = datetime.now(UTC).strftime("%Y%m%d%H%M%S")

    request_json(PLATFORM_ADMIN_BASE_URL, "GET", "/v1/platform-admin/dashboard/summary", expected={401})
    request_json(PLATFORM_ADMIN_BASE_URL, "GET", "/v1/platform-admin/dashboard/summary", token=tenant_token, expected={403})
    request_json(PLATFORM_ADMIN_BASE_URL, "POST", "/v1/platform-admin/plans", token=auditor_token, body=smoke_body("POST /v1/platform-admin/plans", ids, suffix), expected={403})

    results = [
        SmokeResult("GET", "/v1/platform-admin/dashboard/summary", "passed", "401/403", "auditor mutation 403", "n/a", "Auth and tenant-token rejection verified."),
    ]
    created_tenant = request_json(
        PLATFORM_ADMIN_BASE_URL,
        "POST",
        "/v1/platform-admin/tenants",
        token=super_token,
        body=smoke_body("POST /v1/platform-admin/tenants", ids, suffix),
    )
    created_tenant_id = created_tenant.body.get("data", {}).get("id") if isinstance(created_tenant.body, dict) else None
    if isinstance(created_tenant_id, str):
        ids["lifecycle_tenant_id"] = created_tenant_id
    results.append(SmokeResult("POST", "/v1/platform-admin/tenants", "passed", "token", "super_admin", "mutation", f"HTTP {created_tenant.status}"))
    routes = route_catalog(super_token)
    covered = {("GET", "/v1/platform-admin/dashboard/summary"), ("POST", "/v1/platform-admin/tenants")}
    no_body_scenarios = {
        "POST /v1/platform-admin/access-control/users/{platform_user_id}/activate",
        "POST /v1/platform-admin/access-control/users/{platform_user_id}/deactivate",
        "POST /v1/platform-admin/access-control/users/{platform_user_id}/lock",
        "POST /v1/platform-admin/access-control/users/{platform_user_id}/unlock",
        "POST /v1/platform-admin/addons/{addon_id}/activate",
        "POST /v1/platform-admin/addons/{addon_id}/retire",
        "POST /v1/platform-admin/ai/governance-alerts/{alert_id}/acknowledge",
        "POST /v1/platform-admin/ai/governance-alerts/{alert_id}/resolve",
        "POST /v1/platform-admin/infra-pools/{infra_pool_id}/activate",
        "POST /v1/platform-admin/infra-pools/{infra_pool_id}/deactivate",
        "POST /v1/platform-admin/plans/{plan_id}/activate",
        "POST /v1/platform-admin/plans/{plan_id}/retire",
        "POST /v1/platform-admin/provisioning-jobs/{job_id}/cancel",
        "POST /v1/platform-admin/provisioning-jobs/{job_id}/retry",
        "POST /v1/platform-admin/support-sessions/{support_session_id}/end",
    }
    for method, template in routes:
        if (method, template) in covered:
            continue
        if template.endswith("/{domain_id}") and method == "DELETE":
            covered.add((method, template))
            results.append(SmokeResult(method, template, "skipped", "token", "destructive", "not-tested", "Skipped in broad smoke to preserve shared seeded domains."))
            continue
        if template.endswith("/tenant-overrides/{tenant_id}") and method == "DELETE":
            covered.add((method, template))
            results.append(SmokeResult(method, template, "skipped", "token", "destructive", "not-tested", "Skipped in broad smoke to preserve shared seeded overrides."))
            continue
        if template.endswith("/roles/{role_id}") and method == "DELETE":
            covered.add((method, template))
            results.append(SmokeResult(method, template, "skipped", "token", "destructive", "not-tested", "Skipped in broad smoke because system seeded roles are protected."))
            continue
        lifecycle_templates = {
            "/v1/platform-admin/tenants/{tenant_id}/activate",
            "/v1/platform-admin/tenants/{tenant_id}/churn",
            "/v1/platform-admin/tenants/{tenant_id}/reactivate",
            "/v1/platform-admin/tenants/{tenant_id}/restore",
            "/v1/platform-admin/tenants/{tenant_id}/soft-delete",
            "/v1/platform-admin/tenants/{tenant_id}/suspend",
        }
        if template in lifecycle_templates:
            covered.add((method, template))
            results.append(SmokeResult(method, template, "skipped", "token", "state-sensitive", "not-tested", "Skipped in broad smoke to avoid corrupting shared seeded tenants."))
            continue
        path_ids = dict(ids)
        if template.startswith("/v1/platform-admin/tenants/{tenant_id}"):
            path_ids["tenant_id"] = ids["trial_tenant_id"]
        if "tenant-overrides/{tenant_id}" in template:
            path_ids["tenant_id"] = ids["trial_tenant_id"]
        path = concrete_path(template, path_ids)
        if method == "GET":
            if "?" not in path and template.endswith(("tenants", "plans", "quotas", "features", "addons", "support-tickets", "audit-logs")):
                path = f"{path}?{urlencode({'limit': '20'})}"
            response = request_json(PLATFORM_ADMIN_BASE_URL, method, path, token=super_token)
            if isinstance(response.body, dict) and "data" not in response.body:
                raise SmokeFailure(f"{method} {path} returned no data envelope")
            covered.add((method, template))
            results.append(SmokeResult(method, template, "passed", "token", "super_admin", "read-only", f"HTTP {response.status}"))
            continue

        scenario_name = f"{method} {template}"
        body = smoke_body(scenario_name, ids, suffix)
        if f"{method} {template}" not in {
            "DELETE /v1/platform-admin/feature-flags/{flag_id}/tenant-overrides/{tenant_id}",
            "DELETE /v1/platform-admin/access-control/roles/{role_id}",
        } and body is None and method in {"POST", "PATCH", "PUT"} and scenario_name not in no_body_scenarios:
            results.append(SmokeResult(method, template, "not-run", "token", "not-tested", "not-tested", "No safe smoke body defined."))
            continue
        conflict_ok = {
            "POST /v1/platform-admin/compliance/frameworks",
            "POST /v1/platform-admin/tenants/{tenant_id}/activate",
            "POST /v1/platform-admin/tenants/{tenant_id}/churn",
            "POST /v1/platform-admin/tenants/{tenant_id}/reactivate",
            "POST /v1/platform-admin/tenants/{tenant_id}/restore",
            "POST /v1/platform-admin/tenants/{tenant_id}/soft-delete",
            "POST /v1/platform-admin/tenants/{tenant_id}/suspend",
            "POST /v1/platform-admin/addons/{addon_id}/activate",
            "POST /v1/platform-admin/addons/{addon_id}/retire",
            "POST /v1/platform-admin/ai/governance-alerts/{alert_id}/acknowledge",
            "POST /v1/platform-admin/ai/governance-alerts/{alert_id}/resolve",
            "POST /v1/platform-admin/infra-pools/{infra_pool_id}/activate",
            "POST /v1/platform-admin/infra-pools/{infra_pool_id}/deactivate",
            "POST /v1/platform-admin/plans/{plan_id}/activate",
            "POST /v1/platform-admin/plans/{plan_id}/retire",
            "POST /v1/platform-admin/provisioning-jobs/{job_id}/cancel",
            "POST /v1/platform-admin/provisioning-jobs/{job_id}/retry",
            "POST /v1/platform-admin/support-sessions/{support_session_id}/end",
        }
        expected_statuses = {200, 404, 409} if scenario_name in conflict_ok else {200}
        response = request_json(
            PLATFORM_ADMIN_BASE_URL,
            method,
            path,
            token=super_token,
            body=body,
            expected=expected_statuses,
        )
        if scenario_name == "POST /v1/platform-admin/tenants":
            created_id = response.body.get("data", {}).get("id") if isinstance(response.body, dict) else None
            if isinstance(created_id, str):
                ids["lifecycle_tenant_id"] = created_id
        covered.add((method, template))
        results.append(SmokeResult(method, template, "passed", "token", "super_admin", "mutation", f"HTTP {response.status}"))

    expected = set(routes)
    missing = expected - covered
    for method, path in sorted(missing):
        if not any(result.method == method and result.endpoint == path for result in results):
            results.append(SmokeResult(method, path, "not-run", "token", "not-tested", "not-tested", "No scenario executed."))
    return results


def write_coverage(results: list[SmokeResult]) -> None:
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    lines = [
        "# Platform Admin API Endpoint Coverage",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "| Method | Endpoint | Status | Auth Tested | Permission Tested | Audit Tested | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append(
            f"| {result.method} | `{result.endpoint}` | {result.status} | {result.auth_tested} | "
            f"{result.permission_tested} | {result.audit_tested} | {result.notes} |"
        )
    COVERAGE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    global _IDENTITY_CLIENT, _PLATFORM_CLIENT
    if SMOKE_MODE == "inprocess":
        os.environ["IDENTITY_RATE_LIMIT_BACKEND"] = "memory"
        from fastapi.testclient import TestClient
        from gnxthire_identity.main import create_app as create_identity_app
        from gnxthire_platform_admin.main import create_app as create_platform_app

        with ExitStack() as stack:
            _IDENTITY_CLIENT = stack.enter_context(TestClient(create_identity_app(), client=("127.0.0.1", 51999)))
            _PLATFORM_CLIENT = stack.enter_context(TestClient(create_platform_app(), client=("127.0.0.1", 51998)))
            results = run_smoke()
    else:
        results = run_smoke()
    write_coverage(results)
    failed = [result for result in results if result.status == "not-run"]
    print(f"Wrote {COVERAGE_PATH}")
    print(f"Passed endpoints: {sum(1 for result in results if result.status == 'passed')}")
    print(f"Not-run endpoints: {len(failed)}")
    if failed:
        raise SystemExit("Smoke completed with incomplete endpoint coverage; see coverage artifact.")


if __name__ == "__main__":
    main()
