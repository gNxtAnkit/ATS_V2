from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from gnxthire_common.errors import ConflictError, NotFoundError, ValidationFailure

from gnxthire_platform_admin.dependencies import (
    PlatformAdminActorContext,
    RequestMetadata,
    request_metadata,
    require_platform_permission,
    session_dependency,
)
from gnxthire_platform_admin.repository import PlatformAdminRepository, clean_update_payload
from gnxthire_platform_admin.schemas import (
    AddonCreateRequest,
    AddonQuotaDeltasReplaceRequest,
    AddonUpdateRequest,
    AiModelCreateRequest,
    AiModelUpdateRequest,
    ApiVersionCreateRequest,
    ApiVersionUpdateRequest,
    AssignTicketRequest,
    CloseTicketRequest,
    ComplianceFrameworkCreateRequest,
    ComplianceFrameworkUpdateRequest,
    Envelope,
    FeatureCreateRequest,
    FeatureEntitlementsReplaceRequest,
    FeatureFlagCreateRequest,
    FeatureFlagUpdateRequest,
    FeatureUpdateRequest,
    InfraPoolCreateRequest,
    InfraPoolUpdateRequest,
    ListEnvelope,
    ManualVerifyDomainRequest,
    Meta,
    PageMeta,
    PermissionIdsReplaceRequest,
    PlanCreateRequest,
    PlanQuotaLimitsReplaceRequest,
    PlanUpdateRequest,
    PlatformUserCreateRequest,
    PlatformUserUpdateRequest,
    QuotaCreateRequest,
    QuotaUpdateRequest,
    ReasonRequest,
    RegionsReplaceRequest,
    RoleCreateRequest,
    RoleIdsReplaceRequest,
    RoleUpdateRequest,
    SlaPolicyCreateRequest,
    SlaPolicyUpdateRequest,
    SloCreateRequest,
    SloUpdateRequest,
    SupportSessionCreateRequest,
    SupportTicketCreateRequest,
    SupportTicketUpdateRequest,
    TenantCreateRequest,
    TenantDomainCreateRequest,
    TenantDomainUpdateRequest,
    TenantFeatureFlagOverrideRequest,
    TenantFrameworksReplaceRequest,
    TenantUpdateRequest,
)


router = APIRouter(prefix="/v1/platform-admin")

TENANT_STATUSES = {"provisioning", "trial", "active", "suspended", "churned", "pending_deletion", "deleted"}
TENANT_TYPES = {"corporate", "staffing_agency", "rpo", "executive_search"}
REGIONS = {"US", "EU", "IN", "ME", "APAC", "UK", "CA", "AU"}
ISOLATION_TIERS = {"shared", "dedicated_compute", "dedicated_db", "fully_isolated"}
BILLING_INTERVALS = {"monthly", "annual", "custom"}
RESET_PERIODS = {"none", "daily", "monthly", "annual"}
PROVISIONING_RETRYABLE = {"failed", "partial_failure"}
PROVISIONING_CANCELABLE = {"pending", "running"}
TICKET_STATUSES = {"open", "in_progress", "waiting_on_customer", "resolved", "closed"}
TICKET_PRIORITIES = {"P1", "P2", "P3", "P4"}
SLA_SEVERITIES = {"warning", "breached", "critical"}
COMPLIANCE_FRAMEWORKS = {"SOC2", "ISO27001", "GDPR", "CCPA", "HIPAA", "OFCCP", "EEO", "AI_ACT_EU", "NYC_LL144", "DPDPA"}
AI_PROVIDERS = {"anthropic", "openai", "google", "azure_openai", "bedrock", "ollama", "custom"}
TENANT_TRANSITIONS: dict[str, set[str]] = {
    "provisioning": {"trial", "active", "suspended", "pending_deletion"},
    "trial": {"active", "suspended", "churned", "pending_deletion"},
    "active": {"suspended", "churned", "pending_deletion"},
    "suspended": {"active", "churned", "pending_deletion"},
    "churned": {"pending_deletion"},
    "pending_deletion": {"deleted", "active"},
    "deleted": {"active"},
}


def _repo(session: Session) -> PlatformAdminRepository:
    return PlatformAdminRepository(session)


def _single(data: Any, metadata: RequestMetadata) -> Envelope:
    return Envelope(data=data, meta=Meta(request_id=metadata.request_id))


def _list(
    data: list[dict[str, Any]],
    *,
    limit: int,
    next_cursor: str | None,
    has_more: bool,
    metadata: RequestMetadata,
) -> ListEnvelope:
    return ListEnvelope(
        data=data,
        page=PageMeta(limit=limit, next_cursor=next_cursor, has_more=has_more),
        meta=Meta(request_id=metadata.request_id),
    )


def _audit(
    repository: PlatformAdminRepository,
    actor: PlatformAdminActorContext,
    metadata: RequestMetadata,
    *,
    action_key: str,
    object_table: str,
    object_id: UUID | None,
    tenant_id: UUID | None = None,
    before_state: Mapping[str, Any] | None = None,
    after_state: Mapping[str, Any] | None = None,
) -> None:
    repository.insert_audit_log(
        request_id=metadata.request_id,
        actor_platform_user_id=actor.platform_user_id,
        action_key=action_key,
        object_schema="platform",
        object_table=object_table,
        object_id=object_id,
        tenant_id=tenant_id,
        before_state=before_state,
        after_state=after_state,
        ip_address=metadata.ip_address,
        user_agent=metadata.user_agent,
    )


def _validate(value: str, allowed: set[str], field: str) -> None:
    if value not in allowed:
        raise ValidationFailure(f"Invalid {field}", safe_detail=f"Invalid {field}")


def _public_platform_user(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in row.items()
        if key not in {"password_hash"}
    }


def _require_tenant(repository: PlatformAdminRepository, tenant_id: UUID, *, include_deleted: bool = False) -> dict[str, Any]:
    deleted_filter = "" if include_deleted else " AND deleted_at IS NULL"
    tenant = repository.one(f"SELECT * FROM platform.tenants WHERE id = :id{deleted_filter}", {"id": tenant_id})
    if tenant is None:
        raise NotFoundError("Tenant not found", safe_detail="Tenant not found")
    return tenant


def _active_plan(repository: PlatformAdminRepository, plan_id: UUID | None) -> None:
    if plan_id is None:
        return
    plan = repository.one(
        "SELECT id, status::text AS status FROM platform.plans WHERE id = :id AND deleted_at IS NULL",
        {"id": plan_id},
    )
    if plan is None:
        raise ValidationFailure("Plan not found", safe_detail="Plan not found")
    if plan["status"] != "active":
        raise ConflictError("Inactive plan cannot be assigned", safe_detail="Inactive plan cannot be assigned")


def _active_infra_pool(repository: PlatformAdminRepository, infra_pool_id: UUID | None) -> None:
    if infra_pool_id is None:
        return
    pool = repository.one("SELECT id, status FROM platform.infra_pools WHERE id = :id", {"id": infra_pool_id})
    if pool is None:
        raise ValidationFailure("Infrastructure pool not found", safe_detail="Infrastructure pool not found")
    if pool["status"] != "active":
        raise ConflictError("Inactive infrastructure pool cannot be assigned", safe_detail="Inactive infrastructure pool cannot be assigned")


@router.get("/dashboard/summary", response_model=Envelope)
def dashboard_summary(
    metadata: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(session_dependency),
    actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.dashboard.read")),
) -> Envelope:
    repository = _repo(session)
    tenants_by_status = repository.many(
        "SELECT status::text AS status, count(*)::int AS count FROM platform.tenants WHERE deleted_at IS NULL GROUP BY status ORDER BY status",
        {},
    )
    data = {
        "tenants_by_status": tenants_by_status,
        "plans": repository.one("SELECT count(*)::int AS total FROM platform.plans WHERE deleted_at IS NULL", {}),
        "plans_by_status": repository.many("SELECT status::text AS status, count(*)::int AS count FROM platform.plans WHERE deleted_at IS NULL GROUP BY status", {}),
        "provisioning_failures": repository.one("SELECT count(*)::int AS total FROM platform.tenant_provisioning_jobs WHERE status IN ('failed','partial_failure')", {}),
        "open_support_tickets": repository.one("SELECT count(*)::int AS total FROM platform.support_tickets WHERE status <> 'closed'", {}),
        "active_support_sessions": repository.one("SELECT count(*)::int AS total FROM platform.support_sessions WHERE ended_at IS NULL AND expires_at > now()", {}),
        "active_feature_flags": repository.one("SELECT count(*)::int AS total FROM platform.feature_flag_registry WHERE default_enabled", {}),
        "enabled_kill_switches": repository.one("SELECT count(*)::int AS total FROM platform.feature_flag_registry WHERE kill_switch", {}),
        "open_ai_governance_alerts": repository.one("SELECT count(*)::int AS total FROM platform.ai_governance_alerts WHERE status IN ('open','acknowledged')", {}),
        "recent_tenant_lifecycle_events": repository.many("SELECT * FROM platform.tenant_lifecycle_events ORDER BY occurred_at DESC LIMIT 20", {}),
        "recent_audit_events": repository.many("SELECT * FROM platform.audit_logs ORDER BY occurred_at DESC LIMIT 20", {}),
    }
    return _single(data, metadata)


@router.get("/tenants", response_model=ListEnvelope)
def list_tenants(
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = Query(default=None),
    status: str | None = None,
    tenant_type: str | None = None,
    plan_id: UUID | None = None,
    region: str | None = None,
    data_residency_zone: str | None = None,
    isolation_tier: str | None = None,
    infra_pool_id: UUID | None = None,
    search: str | None = None,
    metadata: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(session_dependency),
    actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.read")),
) -> ListEnvelope:
    repository = _repo(session)
    rows, next_cursor, has_more = repository.list_page(
        table="platform.tenants",
        limit=limit,
        cursor=cursor,
        filters={
            "status": status,
            "tenant_type": tenant_type,
            "plan_id": plan_id,
            "region": region,
            "data_residency_zone": data_residency_zone,
            "isolation_tier": isolation_tier,
            "infra_pool_id": infra_pool_id,
        },
        search_columns=("name", "primary_admin_email", "legal_entity_name"),
        search=search,
    )
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/tenants", response_model=Envelope)
def create_tenant(
    payload: TenantCreateRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(session_dependency),
    actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.create")),
) -> Envelope:
    repository = _repo(session)
    _validate(payload.tenant_type, TENANT_TYPES, "tenant_type")
    _validate(payload.region, REGIONS, "region")
    _validate(payload.isolation_tier, ISOLATION_TIERS, "isolation_tier")
    _active_plan(repository, payload.plan_id)
    _active_infra_pool(repository, payload.infra_pool_id)
    tenant = repository.execute_returning_one(
        """
        INSERT INTO platform.tenants (
          name, legal_entity_name, tenant_type, primary_admin_email, plan_id,
          status, isolation_tier, region, data_residency_zone, infra_pool_id
        )
        VALUES (
          :name, :legal_entity_name, :tenant_type, :primary_admin_email, :plan_id,
          'provisioning', :isolation_tier, :region, :data_residency_zone, :infra_pool_id
        )
        RETURNING *
        """,
        payload.model_dump(),
    )
    provisioning_job = repository.execute_returning_one(
        """
        INSERT INTO platform.tenant_provisioning_jobs (tenant_id, idempotency_key, status)
        VALUES (:tenant_id, :idempotency_key, 'pending')
        RETURNING *
        """,
        {"tenant_id": tenant["id"], "idempotency_key": payload.idempotency_key},
    )
    for step_key in ("tenant_schema_context", "tenant_defaults", "tenant_admin_invitation"):
        repository.execute(
            """
            INSERT INTO platform.tenant_provisioning_steps (
              provisioning_job_id, step_key, status
            )
            VALUES (:job_id, :step_key, 'pending')
            """,
            {"job_id": provisioning_job["id"], "step_key": step_key},
        )
    repository.execute(
        """
        INSERT INTO platform.tenant_lifecycle_events (
          tenant_id, event_key, from_status, to_status, actor_platform_user_id, reason
        )
        VALUES (:tenant_id, 'platform.tenant.created', NULL, 'provisioning', :actor_id, 'Tenant created')
        """,
        {"tenant_id": tenant["id"], "actor_id": actor.platform_user_id},
    )
    repository.execute(
        """
        INSERT INTO events.event_outbox (tenant_id, aggregate_reference_id, event_type, payload)
        VALUES (:tenant_id, :aggregate_reference_id, 'platform.tenant.created', CAST(:payload AS jsonb))
        """,
        {
            "tenant_id": tenant["id"],
            "aggregate_reference_id": tenant["id"],
            "payload": json.dumps(
                {
                    "tenant_id": str(tenant["id"]),
                    "provisioning_job_id": str(provisioning_job["id"]),
                    "status": tenant["status"],
                }
            ),
        },
    )
    _audit(
        repository,
        actor,
        metadata,
        action_key="platform.tenant.created",
        object_table="tenants",
        object_id=tenant["id"],
        tenant_id=tenant["id"],
        after_state=tenant,
    )
    return _single({"tenant": tenant, "provisioning_job": provisioning_job}, metadata)


@router.get("/tenants/{tenant_id}", response_model=Envelope)
def get_tenant(
    tenant_id: UUID,
    metadata: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(session_dependency),
    actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.read")),
) -> Envelope:
    return _single(_require_tenant(_repo(session), tenant_id), metadata)


@router.patch("/tenants/{tenant_id}", response_model=Envelope)
def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdateRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(session_dependency),
    actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.update")),
) -> Envelope:
    repository = _repo(session)
    before = _require_tenant(repository, tenant_id, include_deleted=True)
    values = payload.model_dump(exclude={"lock_version"})
    if values.get("region") is not None:
        _validate(values["region"], REGIONS, "region")
    if values.get("isolation_tier") is not None:
        _validate(values["isolation_tier"], ISOLATION_TIERS, "isolation_tier")
    if "plan_id" in values:
        _active_plan(repository, values["plan_id"])
    if "infra_pool_id" in values:
        _active_infra_pool(repository, values["infra_pool_id"])
    after = repository.update_by_id(
        table="platform.tenants",
        entity_id=tenant_id,
        values=values,
        lock_version=payload.lock_version,
    )
    _audit(repository, actor, metadata, action_key="platform.tenant.updated", object_table="tenants", object_id=tenant_id, tenant_id=tenant_id, before_state=before, after_state=after)
    return _single(after, metadata)


def _transition_tenant(
    tenant_id: UUID,
    new_status: str,
    action_key: str,
    payload: ReasonRequest | None,
    metadata: RequestMetadata,
    session: Session,
    actor: PlatformAdminActorContext,
) -> Envelope:
    repository = _repo(session)
    before = _require_tenant(repository, tenant_id)
    old_status = before["status"]
    if new_status not in TENANT_TRANSITIONS.get(old_status, set()):
        raise ConflictError("Invalid tenant status transition", safe_detail="Invalid tenant status transition")
    reason = payload.reason if payload else None
    if new_status in {"suspended", "churned", "pending_deletion"} and not reason:
        raise ValidationFailure("Reason is required", safe_detail="Reason is required")
    timestamp_sets = {
        "active": "activated_at = COALESCE(activated_at, now()), suspended_at = NULL",
        "suspended": "suspended_at = now()",
        "churned": "churned_at = now()",
        "pending_deletion": "deleted_at = COALESCE(deleted_at, now())",
        "deleted": "deleted_at = COALESCE(deleted_at, now())",
    }
    if action_key == "platform.tenant.restored":
        timestamp_sets["active"] = "activated_at = COALESCE(activated_at, now()), suspended_at = NULL, deleted_at = NULL"
    extra_set = ", " + timestamp_sets[new_status] if new_status in timestamp_sets else ""
    after = repository.execute_returning_one(
        f"UPDATE platform.tenants SET status = :status, updated_at = now(){extra_set} WHERE id = :id RETURNING *",
        {"status": new_status, "id": tenant_id},
    )
    repository.execute(
        """
        INSERT INTO platform.tenant_lifecycle_events (
          tenant_id, event_key, from_status, to_status, actor_platform_user_id, reason
        )
        VALUES (:tenant_id, :event_key, :from_status, :to_status, :actor_id, :reason)
        """,
        {
            "tenant_id": tenant_id,
            "event_key": action_key,
            "from_status": old_status,
            "to_status": new_status,
            "actor_id": actor.platform_user_id,
            "reason": reason,
        },
    )
    _audit(repository, actor, metadata, action_key=action_key, object_table="tenants", object_id=tenant_id, tenant_id=tenant_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.post("/tenants/{tenant_id}/activate", response_model=Envelope)
def activate_tenant(tenant_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.lifecycle.manage"))) -> Envelope:
    return _transition_tenant(tenant_id, "active", "platform.tenant.activated", None, metadata, session, actor)


@router.post("/tenants/{tenant_id}/suspend", response_model=Envelope)
def suspend_tenant(tenant_id: UUID, payload: ReasonRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.lifecycle.manage"))) -> Envelope:
    return _transition_tenant(tenant_id, "suspended", "platform.tenant.suspended", payload, metadata, session, actor)


@router.post("/tenants/{tenant_id}/reactivate", response_model=Envelope)
def reactivate_tenant(tenant_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.lifecycle.manage"))) -> Envelope:
    return _transition_tenant(tenant_id, "active", "platform.tenant.reactivated", None, metadata, session, actor)


@router.post("/tenants/{tenant_id}/churn", response_model=Envelope)
def churn_tenant(tenant_id: UUID, payload: ReasonRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.lifecycle.manage"))) -> Envelope:
    return _transition_tenant(tenant_id, "churned", "platform.tenant.churned", payload, metadata, session, actor)


@router.post("/tenants/{tenant_id}/soft-delete", response_model=Envelope)
def soft_delete_tenant(tenant_id: UUID, payload: ReasonRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.lifecycle.manage"))) -> Envelope:
    return _transition_tenant(tenant_id, "pending_deletion", "platform.tenant.soft_deleted", payload, metadata, session, actor)


@router.post("/tenants/{tenant_id}/restore", response_model=Envelope)
def restore_tenant(tenant_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.lifecycle.manage"))) -> Envelope:
    return _transition_tenant(tenant_id, "active", "platform.tenant.restored", None, metadata, session, actor)


@router.get("/tenants/{tenant_id}/lifecycle-events", response_model=ListEnvelope)
def tenant_lifecycle_events(tenant_id: UUID, limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.read"))) -> ListEnvelope:
    repository = _repo(session)
    _require_tenant(repository, tenant_id)
    rows, next_cursor, has_more = repository.list_page(table="platform.tenant_lifecycle_events", limit=limit, cursor=cursor, filters={"tenant_id": tenant_id}, order_column="occurred_at")
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.get("/tenants/{tenant_id}/subscription-summary", response_model=Envelope)
def tenant_subscription_summary(tenant_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.entitlement.read"))) -> Envelope:
    repository = _repo(session)
    tenant = _require_tenant(repository, tenant_id)
    subscription = repository.one("SELECT * FROM billing.subscriptions WHERE tenant_id = :tenant_id AND status IN ('trialing','active','past_due','suspended') ORDER BY created_at DESC LIMIT 1", {"tenant_id": tenant_id})
    addons = repository.many("SELECT * FROM billing.tenant_addon_subscriptions WHERE tenant_id = :tenant_id AND status = 'active'", {"tenant_id": tenant_id})
    return _single({"tenant": tenant, "subscription": subscription, "active_addons": addons}, metadata)


@router.get("/tenants/{tenant_id}/effective-entitlements", response_model=Envelope)
def effective_entitlements(
    tenant_id: UUID,
    metadata: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(session_dependency),
    actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.entitlement.read")),
) -> Envelope:
    repository = _repo(session)
    tenant = _require_tenant(repository, tenant_id)
    subscription = repository.one(
        "SELECT * FROM billing.subscriptions WHERE tenant_id = :tenant_id AND status IN ('trialing','active','past_due','suspended') ORDER BY created_at DESC LIMIT 1",
        {"tenant_id": tenant_id},
    )
    plan_id = subscription["plan_id"] if subscription else tenant.get("plan_id")
    plan_features = []
    plan_quotas = []
    if plan_id is not None:
        plan_features = repository.many(
            """
            SELECT fd.feature_key::text AS feature_key, fd.name, pfe.is_enabled, 'plan' AS source
            FROM platform.plan_feature_entitlements pfe
            JOIN platform.feature_definitions fd ON fd.id = pfe.feature_definition_id
            WHERE pfe.plan_id = :plan_id
            ORDER BY fd.feature_key
            """,
            {"plan_id": plan_id},
        )
        plan_quotas = repository.many(
            """
            SELECT q.quota_key::text AS quota_key, q.unit, pql.soft_limit, pql.hard_limit,
                   pql.overage_unit_price, 'plan' AS source
            FROM platform.plan_quota_limits pql
            JOIN platform.quota_definitions q ON q.id = pql.quota_definition_id
            WHERE pql.plan_id = :plan_id
            ORDER BY q.quota_key
            """,
            {"plan_id": plan_id},
        )
    active_addons = repository.many(
        """
        SELECT tas.*, pa.code::text AS addon_code, pa.name AS addon_name
        FROM billing.tenant_addon_subscriptions tas
        JOIN platform.plan_addons pa ON pa.id = tas.addon_id
        WHERE tas.tenant_id = :tenant_id AND tas.status = 'active'
          AND (tas.ends_at IS NULL OR tas.ends_at > now())
        """,
        {"tenant_id": tenant_id},
    )
    addon_features = repository.many(
        """
        SELECT pa.code::text AS addon_code, fd.feature_key::text AS feature_key, afe.is_enabled, 'addon' AS source
        FROM billing.tenant_addon_subscriptions tas
        JOIN platform.plan_addons pa ON pa.id = tas.addon_id
        JOIN platform.addon_feature_entitlements afe ON afe.addon_id = pa.id
        JOIN platform.feature_definitions fd ON fd.id = afe.feature_definition_id
        WHERE tas.tenant_id = :tenant_id AND tas.status = 'active'
          AND (tas.ends_at IS NULL OR tas.ends_at > now())
        ORDER BY pa.code, fd.feature_key
        """,
        {"tenant_id": tenant_id},
    )
    addon_quota_deltas = repository.many(
        """
        SELECT pa.code::text AS addon_code, q.quota_key::text AS quota_key, aqd.delta_value, 'addon' AS source
        FROM billing.tenant_addon_subscriptions tas
        JOIN platform.plan_addons pa ON pa.id = tas.addon_id
        JOIN platform.addon_quota_deltas aqd ON aqd.addon_id = pa.id
        JOIN platform.quota_definitions q ON q.id = aqd.quota_definition_id
        WHERE tas.tenant_id = :tenant_id AND tas.status = 'active'
          AND (tas.ends_at IS NULL OR tas.ends_at > now())
        ORDER BY pa.code, q.quota_key
        """,
        {"tenant_id": tenant_id},
    )
    quota_overrides = repository.many(
        """
        SELECT q.quota_key::text AS quota_key, tqo.override_limit, tqo.reason, 'tenant_override' AS source
        FROM billing.tenant_quota_overrides tqo
        JOIN platform.quota_definitions q ON q.id = tqo.quota_definition_id
        WHERE tqo.tenant_id = :tenant_id
          AND tqo.starts_at <= now()
          AND (tqo.ends_at IS NULL OR tqo.ends_at > now())
        ORDER BY q.quota_key
        """,
        {"tenant_id": tenant_id},
    )
    flags = repository.many(
        """
        SELECT f.flag_key::text AS flag_key, f.default_enabled, f.rollout_percentage, f.kill_switch,
               o.is_enabled AS tenant_override_enabled, o.reason AS tenant_override_reason, o.expires_at
        FROM platform.feature_flag_registry f
        LEFT JOIN platform.feature_flag_tenant_overrides o
          ON o.feature_flag_id = f.id
         AND o.tenant_id = :tenant_id
         AND (o.expires_at IS NULL OR o.expires_at > now())
        ORDER BY f.flag_key
        """,
        {"tenant_id": tenant_id},
    )
    return _single(
        {
            "tenant_id": tenant_id,
            "plan_id": plan_id,
            "subscription": subscription,
            "enabled_features": [item for item in plan_features + addon_features if item["is_enabled"]],
            "disabled_features": [item for item in plan_features + addon_features if not item["is_enabled"]],
            "quota_limits": plan_quotas,
            "quota_deltas": addon_quota_deltas,
            "quota_overrides": quota_overrides,
            "active_addons": active_addons,
            "feature_flags": flags,
            "warnings": [] if subscription or tenant.get("plan_id") else ["No active subscription or tenant plan is assigned"],
        },
        metadata,
    )


@router.get("/tenants/{tenant_id}/health", response_model=Envelope)
def tenant_health(tenant_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.read"))) -> Envelope:
    repository = _repo(session)
    tenant = _require_tenant(repository, tenant_id)
    failed_jobs = repository.one("SELECT count(*)::int AS total FROM platform.tenant_provisioning_jobs WHERE tenant_id = :tenant_id AND status IN ('failed','partial_failure')", {"tenant_id": tenant_id})
    open_tickets = repository.one("SELECT count(*)::int AS total FROM platform.support_tickets WHERE tenant_id = :tenant_id AND status <> 'closed'", {"tenant_id": tenant_id})
    active_support_sessions = repository.one("SELECT count(*)::int AS total FROM platform.support_sessions WHERE tenant_id = :tenant_id AND ended_at IS NULL AND expires_at > now()", {"tenant_id": tenant_id})
    return _single({"tenant": tenant, "failed_provisioning_jobs": failed_jobs, "open_support_tickets": open_tickets, "active_support_sessions": active_support_sessions}, metadata)


@router.get("/tenants/{tenant_id}/domains", response_model=ListEnvelope)
def list_tenant_domains(tenant_id: UUID, limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.read"))) -> ListEnvelope:
    repository = _repo(session)
    _require_tenant(repository, tenant_id)
    rows, next_cursor, has_more = repository.list_page(table="platform.tenant_domains", limit=limit, cursor=cursor, filters={"tenant_id": tenant_id})
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/tenants/{tenant_id}/domains", response_model=Envelope)
def add_tenant_domain(tenant_id: UUID, payload: TenantDomainCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.domain.manage"))) -> Envelope:
    repository = _repo(session)
    _require_tenant(repository, tenant_id)
    domain = repository.execute_returning_one(
        """
        INSERT INTO platform.tenant_domains (tenant_id, domain, is_primary)
        VALUES (:tenant_id, :domain, :is_primary)
        RETURNING *
        """,
        {"tenant_id": tenant_id, **payload.model_dump()},
    )
    _audit(repository, actor, metadata, action_key="platform.tenant_domain.added", object_table="tenant_domains", object_id=domain["id"], tenant_id=tenant_id, after_state=domain)
    return _single(domain, metadata)


@router.patch("/tenants/{tenant_id}/domains/{domain_id}", response_model=Envelope)
def update_tenant_domain(tenant_id: UUID, domain_id: UUID, payload: TenantDomainUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.domain.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.one("SELECT * FROM platform.tenant_domains WHERE id = :id AND tenant_id = :tenant_id", {"id": domain_id, "tenant_id": tenant_id})
    if before is None:
        raise NotFoundError("Domain not found", safe_detail="Domain not found")
    values = clean_update_payload(payload.model_dump())
    if values.get("verification_status") is not None and values["verification_status"] not in {"pending", "verified", "failed", "revoked"}:
        raise ValidationFailure("Invalid verification_status", safe_detail="Invalid verification_status")
    after = repository.update_by_id(table="platform.tenant_domains", entity_id=domain_id, values=values, touch_updated_at=False)
    _audit(repository, actor, metadata, action_key="platform.tenant_domain.updated", object_table="tenant_domains", object_id=domain_id, tenant_id=tenant_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.post("/tenants/{tenant_id}/domains/{domain_id}/verify", response_model=Envelope)
def verify_tenant_domain(tenant_id: UUID, domain_id: UUID, payload: ManualVerifyDomainRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.domain.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.one("SELECT * FROM platform.tenant_domains WHERE id = :id AND tenant_id = :tenant_id", {"id": domain_id, "tenant_id": tenant_id})
    if before is None:
        raise NotFoundError("Domain not found", safe_detail="Domain not found")
    after = repository.execute_returning_one("UPDATE platform.tenant_domains SET verification_status = 'verified', verified_at = now() WHERE id = :id RETURNING *", {"id": domain_id})
    _audit(repository, actor, metadata, action_key="platform.tenant_domain.verified", object_table="tenant_domains", object_id=domain_id, tenant_id=tenant_id, before_state=before, after_state={**after, "manual_reason": payload.reason})
    return _single(after, metadata)


@router.delete("/tenants/{tenant_id}/domains/{domain_id}", response_model=Envelope)
def delete_tenant_domain(tenant_id: UUID, domain_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.tenant.domain.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.one("SELECT * FROM platform.tenant_domains WHERE id = :id AND tenant_id = :tenant_id", {"id": domain_id, "tenant_id": tenant_id})
    if before is None:
        raise NotFoundError("Domain not found", safe_detail="Domain not found")
    after = repository.execute_returning_one("UPDATE platform.tenant_domains SET verification_status = 'revoked' WHERE id = :id RETURNING *", {"id": domain_id})
    _audit(repository, actor, metadata, action_key="platform.tenant_domain.deleted", object_table="tenant_domains", object_id=domain_id, tenant_id=tenant_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.get("/provisioning-jobs", response_model=ListEnvelope)
def list_provisioning_jobs(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, status: str | None = None, tenant_id: UUID | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.provisioning.read"))) -> ListEnvelope:
    repository = _repo(session)
    rows, next_cursor, has_more = repository.list_page(table="platform.tenant_provisioning_jobs", limit=limit, cursor=cursor, filters={"status": status, "tenant_id": tenant_id})
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.get("/provisioning-jobs/{job_id}", response_model=Envelope)
def get_provisioning_job(job_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.provisioning.read"))) -> Envelope:
    repository = _repo(session)
    job = repository.require_by_id("platform.tenant_provisioning_jobs", job_id)
    steps = repository.many("SELECT * FROM platform.tenant_provisioning_steps WHERE provisioning_job_id = :id ORDER BY created_at, id", {"id": job_id})
    return _single({"job": job, "steps": steps}, metadata)


@router.get("/tenants/{tenant_id}/provisioning-jobs", response_model=ListEnvelope)
def list_tenant_provisioning_jobs(tenant_id: UUID, limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.provisioning.read"))) -> ListEnvelope:
    repository = _repo(session)
    _require_tenant(repository, tenant_id)
    rows, next_cursor, has_more = repository.list_page(table="platform.tenant_provisioning_jobs", limit=limit, cursor=cursor, filters={"tenant_id": tenant_id})
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


def _provisioning_action(job_id: UUID, target_status: str, action_key: str, metadata: RequestMetadata, session: Session, actor: PlatformAdminActorContext) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.tenant_provisioning_jobs", job_id)
    status = before["status"]
    if target_status == "pending" and status not in PROVISIONING_RETRYABLE:
        raise ConflictError("Provisioning job is not retryable", safe_detail="Provisioning job is not retryable")
    if target_status == "skipped" and status not in PROVISIONING_CANCELABLE:
        raise ConflictError("Provisioning job cannot be cancelled", safe_detail="Provisioning job cannot be cancelled")
    after = repository.execute_returning_one(
        """
        UPDATE platform.tenant_provisioning_jobs
        SET status = CAST(:status AS sync_status_enum),
            retry_count = CASE WHEN CAST(:status AS text) = 'pending' THEN retry_count + 1 ELSE retry_count END,
            completed_at = NULL, failed_at = NULL, updated_at = now()
        WHERE id = :id
        RETURNING *
        """,
        {"id": job_id, "status": target_status},
    )
    _audit(repository, actor, metadata, action_key=action_key, object_table="tenant_provisioning_jobs", object_id=job_id, tenant_id=before["tenant_id"], before_state=before, after_state=after)
    return _single(after, metadata)


@router.post("/provisioning-jobs/{job_id}/retry", response_model=Envelope)
def retry_provisioning_job(job_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.provisioning.manage"))) -> Envelope:
    return _provisioning_action(job_id, "pending", "platform.provisioning.retry_requested", metadata, session, actor)


@router.post("/provisioning-jobs/{job_id}/cancel", response_model=Envelope)
def cancel_provisioning_job(job_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.provisioning.manage"))) -> Envelope:
    return _provisioning_action(job_id, "skipped", "platform.provisioning.cancel_requested", metadata, session, actor)


@router.get("/infra-pools", response_model=ListEnvelope)
def list_infra_pools(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, status: str | None = None, region: str | None = None, isolation_tier: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.infra_pool.read"))) -> ListEnvelope:
    repository = _repo(session)
    rows, next_cursor, has_more = repository.list_page(table="platform.infra_pools", limit=limit, cursor=cursor, filters={"status": status, "region": region, "isolation_tier": isolation_tier}, search_columns=("pool_key",), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/infra-pools", response_model=Envelope)
def create_infra_pool(payload: InfraPoolCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.infra_pool.manage"))) -> Envelope:
    _validate(payload.region, REGIONS, "region")
    _validate(payload.isolation_tier, ISOLATION_TIERS, "isolation_tier")
    repository = _repo(session)
    row = repository.execute_returning_one(
        """
        INSERT INTO platform.infra_pools (
          pool_key, region, isolation_tier, database_cluster_ref, search_cluster_ref, storage_bucket_prefix, status
        )
        VALUES (
          :pool_key, :region, :isolation_tier, :database_cluster_ref, :search_cluster_ref, :storage_bucket_prefix, 'active'
        )
        RETURNING *
        """,
        payload.model_dump(),
    )
    _audit(repository, actor, metadata, action_key="platform.infra_pool.created", object_table="infra_pools", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.get("/infra-pools/{infra_pool_id}", response_model=Envelope)
def get_infra_pool(infra_pool_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.infra_pool.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.infra_pools", infra_pool_id), metadata)


@router.patch("/infra-pools/{infra_pool_id}", response_model=Envelope)
def update_infra_pool(infra_pool_id: UUID, payload: InfraPoolUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.infra_pool.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.infra_pools", infra_pool_id)
    after = repository.update_by_id(table="platform.infra_pools", entity_id=infra_pool_id, values=payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.infra_pool.updated", object_table="infra_pools", object_id=infra_pool_id, before_state=before, after_state=after)
    return _single(after, metadata)


def _set_infra_pool_status(infra_pool_id: UUID, status: str, action_key: str, metadata: RequestMetadata, session: Session, actor: PlatformAdminActorContext) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.infra_pools", infra_pool_id)
    if status != "active":
        active_tenant_count = repository.one("SELECT count(*)::int AS total FROM platform.tenants WHERE infra_pool_id = :id AND status IN ('trial','active','suspended') AND deleted_at IS NULL", {"id": infra_pool_id})
        if active_tenant_count and active_tenant_count["total"] > 0:
            raise ConflictError("Infrastructure pool has active tenants", safe_detail="Infrastructure pool has active tenants")
    after = repository.update_by_id(table="platform.infra_pools", entity_id=infra_pool_id, values={"status": status})
    _audit(repository, actor, metadata, action_key=action_key, object_table="infra_pools", object_id=infra_pool_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.post("/infra-pools/{infra_pool_id}/activate", response_model=Envelope)
def activate_infra_pool(infra_pool_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.infra_pool.manage"))) -> Envelope:
    return _set_infra_pool_status(infra_pool_id, "active", "platform.infra_pool.activated", metadata, session, actor)


@router.post("/infra-pools/{infra_pool_id}/deactivate", response_model=Envelope)
def deactivate_infra_pool(infra_pool_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.infra_pool.manage"))) -> Envelope:
    return _set_infra_pool_status(infra_pool_id, "retired", "platform.infra_pool.deactivated", metadata, session, actor)


@router.get("/plans", response_model=ListEnvelope)
def list_plans(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, status: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.plan.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.plans", limit=limit, cursor=cursor, filters={"status": status}, search_columns=("code", "name"), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/plans", response_model=Envelope)
def create_plan(payload: PlanCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.plan.manage"))) -> Envelope:
    _validate(payload.billing_interval, BILLING_INTERVALS, "billing_interval")
    repository = _repo(session)
    row = repository.execute_returning_one(
        """
        INSERT INTO platform.plans (
          code, name, description, status, billing_interval, base_price, currency, min_seats, max_seats, trial_days
        )
        VALUES (
          :code, :name, :description, 'draft', :billing_interval, :base_price, :currency, :min_seats, :max_seats, :trial_days
        )
        RETURNING *
        """,
        payload.model_dump(),
    )
    _audit(repository, actor, metadata, action_key="platform.plan.created", object_table="plans", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.get("/plans/{plan_id}", response_model=Envelope)
def get_plan(plan_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.plan.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.plans", plan_id), metadata)


@router.patch("/plans/{plan_id}", response_model=Envelope)
def update_plan(plan_id: UUID, payload: PlanUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.plan.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.plans", plan_id)
    values = payload.model_dump(exclude={"lock_version"})
    if values.get("billing_interval") is not None:
        _validate(values["billing_interval"], BILLING_INTERVALS, "billing_interval")
    after = repository.update_by_id(table="platform.plans", entity_id=plan_id, values=values, lock_version=payload.lock_version)
    _audit(repository, actor, metadata, action_key="platform.plan.updated", object_table="plans", object_id=plan_id, before_state=before, after_state=after)
    return _single(after, metadata)


def _set_plan_status(plan_id: UUID, status: str, action_key: str, metadata: RequestMetadata, session: Session, actor: PlatformAdminActorContext) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.plans", plan_id)
    after = repository.update_by_id(table="platform.plans", entity_id=plan_id, values={"status": status})
    _audit(repository, actor, metadata, action_key=action_key, object_table="plans", object_id=plan_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.post("/plans/{plan_id}/activate", response_model=Envelope)
def activate_plan(plan_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.plan.manage"))) -> Envelope:
    return _set_plan_status(plan_id, "active", "platform.plan.activated", metadata, session, actor)


@router.post("/plans/{plan_id}/retire", response_model=Envelope)
def retire_plan(plan_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.plan.manage"))) -> Envelope:
    return _set_plan_status(plan_id, "archived", "platform.plan.retired", metadata, session, actor)


@router.get("/plans/{plan_id}/features", response_model=ListEnvelope)
def get_plan_features(plan_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature.read"))) -> ListEnvelope:
    repository = _repo(session)
    repository.require_by_id("platform.plans", plan_id)
    rows = repository.many("SELECT * FROM platform.plan_feature_entitlements WHERE plan_id = :plan_id ORDER BY created_at, id", {"plan_id": plan_id})
    return _list(rows, limit=len(rows), next_cursor=None, has_more=False, metadata=metadata)


@router.put("/plans/{plan_id}/features", response_model=Envelope)
def replace_plan_features(plan_id: UUID, payload: FeatureEntitlementsReplaceRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.many("SELECT * FROM platform.plan_feature_entitlements WHERE plan_id = :plan_id", {"plan_id": plan_id})
    repository.require_by_id("platform.plans", plan_id)
    repository.execute("DELETE FROM platform.plan_feature_entitlements WHERE plan_id = :plan_id", {"plan_id": plan_id})
    for item in payload.items:
        repository.require_by_id("platform.feature_definitions", item.feature_definition_id)
        repository.execute("INSERT INTO platform.plan_feature_entitlements (plan_id, feature_definition_id, is_enabled) VALUES (:plan_id, :feature_definition_id, :is_enabled)", {"plan_id": plan_id, **item.model_dump()})
    after = repository.many("SELECT * FROM platform.plan_feature_entitlements WHERE plan_id = :plan_id", {"plan_id": plan_id})
    _audit(repository, actor, metadata, action_key="platform.plan.features_updated", object_table="plan_feature_entitlements", object_id=plan_id, before_state={"items": before}, after_state={"items": after})
    return _single({"items": after}, metadata)


@router.get("/plans/{plan_id}/quotas", response_model=ListEnvelope)
def get_plan_quotas(plan_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.quota.read"))) -> ListEnvelope:
    repository = _repo(session)
    repository.require_by_id("platform.plans", plan_id)
    rows = repository.many("SELECT * FROM platform.plan_quota_limits WHERE plan_id = :plan_id ORDER BY created_at, id", {"plan_id": plan_id})
    return _list(rows, limit=len(rows), next_cursor=None, has_more=False, metadata=metadata)


@router.put("/plans/{plan_id}/quotas", response_model=Envelope)
def replace_plan_quotas(plan_id: UUID, payload: PlanQuotaLimitsReplaceRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.quota.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.many("SELECT * FROM platform.plan_quota_limits WHERE plan_id = :plan_id", {"plan_id": plan_id})
    repository.require_by_id("platform.plans", plan_id)
    repository.execute("DELETE FROM platform.plan_quota_limits WHERE plan_id = :plan_id", {"plan_id": plan_id})
    for item in payload.items:
        repository.require_by_id("platform.quota_definitions", item.quota_definition_id)
        repository.execute("INSERT INTO platform.plan_quota_limits (plan_id, quota_definition_id, hard_limit, soft_limit, overage_unit_price) VALUES (:plan_id, :quota_definition_id, :hard_limit, :soft_limit, :overage_unit_price)", {"plan_id": plan_id, **item.model_dump()})
    after = repository.many("SELECT * FROM platform.plan_quota_limits WHERE plan_id = :plan_id", {"plan_id": plan_id})
    _audit(repository, actor, metadata, action_key="platform.plan.quotas_updated", object_table="plan_quota_limits", object_id=plan_id, before_state={"items": before}, after_state={"items": after})
    return _single({"items": after}, metadata)


@router.get("/quotas", response_model=ListEnvelope)
def list_quotas(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.quota.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.quota_definitions", limit=limit, cursor=cursor, search_columns=("quota_key", "display_name"), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/quotas", response_model=Envelope)
def create_quota(payload: QuotaCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.quota.manage"))) -> Envelope:
    _validate(payload.reset_period, RESET_PERIODS, "reset_period")
    repository = _repo(session)
    row = repository.execute_returning_one(
        "INSERT INTO platform.quota_definitions (quota_key, display_name, unit, reset_period, is_metered) VALUES (:quota_key, :display_name, :unit, :reset_period, :is_metered) RETURNING *",
        payload.model_dump(),
    )
    _audit(repository, actor, metadata, action_key="platform.quota.created", object_table="quota_definitions", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.get("/quotas/{quota_definition_id}", response_model=Envelope)
def get_quota(quota_definition_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.quota.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.quota_definitions", quota_definition_id), metadata)


@router.patch("/quotas/{quota_definition_id}", response_model=Envelope)
def update_quota(quota_definition_id: UUID, payload: QuotaUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.quota.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.quota_definitions", quota_definition_id)
    values = payload.model_dump()
    if values.get("reset_period") is not None:
        _validate(values["reset_period"], RESET_PERIODS, "reset_period")
    after = repository.update_by_id(table="platform.quota_definitions", entity_id=quota_definition_id, values=values)
    _audit(repository, actor, metadata, action_key="platform.quota.updated", object_table="quota_definitions", object_id=quota_definition_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.get("/features", response_model=ListEnvelope)
def list_features(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, category: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.feature_definitions", limit=limit, cursor=cursor, filters={"category": category}, search_columns=("feature_key", "name"), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/features", response_model=Envelope)
def create_feature(payload: FeatureCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature.manage"))) -> Envelope:
    repository = _repo(session)
    row = repository.execute_returning_one(
        "INSERT INTO platform.feature_definitions (feature_key, name, description, category, default_enabled, requires_human_governance) VALUES (:feature_key, :name, :description, :category, :default_enabled, :requires_human_governance) RETURNING *",
        payload.model_dump(),
    )
    _audit(repository, actor, metadata, action_key="platform.feature.created", object_table="feature_definitions", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.get("/features/{feature_definition_id}", response_model=Envelope)
def get_feature(feature_definition_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.feature_definitions", feature_definition_id), metadata)


@router.patch("/features/{feature_definition_id}", response_model=Envelope)
def update_feature(feature_definition_id: UUID, payload: FeatureUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.feature_definitions", feature_definition_id)
    after = repository.update_by_id(table="platform.feature_definitions", entity_id=feature_definition_id, values=payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.feature.updated", object_table="feature_definitions", object_id=feature_definition_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.get("/addons", response_model=ListEnvelope)
def list_addons(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, status: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.addon.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.plan_addons", limit=limit, cursor=cursor, filters={"status": status}, search_columns=("code", "name"), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/addons", response_model=Envelope)
def create_addon(payload: AddonCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.addon.manage"))) -> Envelope:
    _validate(payload.billing_interval, BILLING_INTERVALS, "billing_interval")
    repository = _repo(session)
    row = repository.execute_returning_one(
        "INSERT INTO platform.plan_addons (code, name, description, status, price, currency, billing_interval) VALUES (:code, :name, :description, 'draft', :price, :currency, :billing_interval) RETURNING *",
        payload.model_dump(),
    )
    _audit(repository, actor, metadata, action_key="platform.addon.created", object_table="plan_addons", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.get("/addons/{addon_id}", response_model=Envelope)
def get_addon(addon_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.addon.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.plan_addons", addon_id), metadata)


@router.patch("/addons/{addon_id}", response_model=Envelope)
def update_addon(addon_id: UUID, payload: AddonUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.addon.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.plan_addons", addon_id)
    values = payload.model_dump()
    if values.get("billing_interval") is not None:
        _validate(values["billing_interval"], BILLING_INTERVALS, "billing_interval")
    after = repository.update_by_id(table="platform.plan_addons", entity_id=addon_id, values=values)
    _audit(repository, actor, metadata, action_key="platform.addon.updated", object_table="plan_addons", object_id=addon_id, before_state=before, after_state=after)
    return _single(after, metadata)


def _set_addon_status(addon_id: UUID, status: str, action_key: str, metadata: RequestMetadata, session: Session, actor: PlatformAdminActorContext) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.plan_addons", addon_id)
    after = repository.update_by_id(table="platform.plan_addons", entity_id=addon_id, values={"status": status})
    _audit(repository, actor, metadata, action_key=action_key, object_table="plan_addons", object_id=addon_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.post("/addons/{addon_id}/activate", response_model=Envelope)
def activate_addon(addon_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.addon.manage"))) -> Envelope:
    return _set_addon_status(addon_id, "active", "platform.addon.activated", metadata, session, actor)


@router.post("/addons/{addon_id}/retire", response_model=Envelope)
def retire_addon(addon_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.addon.manage"))) -> Envelope:
    return _set_addon_status(addon_id, "archived", "platform.addon.retired", metadata, session, actor)


@router.get("/addons/{addon_id}/quota-deltas", response_model=ListEnvelope)
def get_addon_quota_deltas(addon_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.quota.read"))) -> ListEnvelope:
    repository = _repo(session)
    repository.require_by_id("platform.plan_addons", addon_id)
    rows = repository.many("SELECT * FROM platform.addon_quota_deltas WHERE addon_id = :addon_id ORDER BY created_at, id", {"addon_id": addon_id})
    return _list(rows, limit=len(rows), next_cursor=None, has_more=False, metadata=metadata)


@router.put("/addons/{addon_id}/quota-deltas", response_model=Envelope)
def replace_addon_quota_deltas(addon_id: UUID, payload: AddonQuotaDeltasReplaceRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.quota.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.many("SELECT * FROM platform.addon_quota_deltas WHERE addon_id = :addon_id", {"addon_id": addon_id})
    repository.require_by_id("platform.plan_addons", addon_id)
    repository.execute("DELETE FROM platform.addon_quota_deltas WHERE addon_id = :addon_id", {"addon_id": addon_id})
    for item in payload.items:
        repository.require_by_id("platform.quota_definitions", item.quota_definition_id)
        repository.execute("INSERT INTO platform.addon_quota_deltas (addon_id, quota_definition_id, delta_value) VALUES (:addon_id, :quota_definition_id, :delta_value)", {"addon_id": addon_id, **item.model_dump()})
    after = repository.many("SELECT * FROM platform.addon_quota_deltas WHERE addon_id = :addon_id", {"addon_id": addon_id})
    _audit(repository, actor, metadata, action_key="platform.addon.quota_deltas_updated", object_table="addon_quota_deltas", object_id=addon_id, before_state={"items": before}, after_state={"items": after})
    return _single({"items": after}, metadata)


@router.get("/addons/{addon_id}/features", response_model=ListEnvelope)
def get_addon_features(addon_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature.read"))) -> ListEnvelope:
    repository = _repo(session)
    repository.require_by_id("platform.plan_addons", addon_id)
    rows = repository.many("SELECT * FROM platform.addon_feature_entitlements WHERE addon_id = :addon_id ORDER BY created_at, id", {"addon_id": addon_id})
    return _list(rows, limit=len(rows), next_cursor=None, has_more=False, metadata=metadata)


@router.put("/addons/{addon_id}/features", response_model=Envelope)
def replace_addon_features(addon_id: UUID, payload: FeatureEntitlementsReplaceRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.many("SELECT * FROM platform.addon_feature_entitlements WHERE addon_id = :addon_id", {"addon_id": addon_id})
    repository.require_by_id("platform.plan_addons", addon_id)
    repository.execute("DELETE FROM platform.addon_feature_entitlements WHERE addon_id = :addon_id", {"addon_id": addon_id})
    for item in payload.items:
        repository.require_by_id("platform.feature_definitions", item.feature_definition_id)
        repository.execute("INSERT INTO platform.addon_feature_entitlements (addon_id, feature_definition_id, is_enabled) VALUES (:addon_id, :feature_definition_id, :is_enabled)", {"addon_id": addon_id, **item.model_dump()})
    after = repository.many("SELECT * FROM platform.addon_feature_entitlements WHERE addon_id = :addon_id", {"addon_id": addon_id})
    _audit(repository, actor, metadata, action_key="platform.addon.features_updated", object_table="addon_feature_entitlements", object_id=addon_id, before_state={"items": before}, after_state={"items": after})
    return _single({"items": after}, metadata)


@router.get("/feature-flags", response_model=ListEnvelope)
def list_feature_flags(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature_flag.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.feature_flag_registry", limit=limit, cursor=cursor, search_columns=("flag_key", "description"), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/feature-flags", response_model=Envelope)
def create_feature_flag(payload: FeatureFlagCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature_flag.manage"))) -> Envelope:
    repository = _repo(session)
    row = repository.execute_returning_one(
        "INSERT INTO platform.feature_flag_registry (flag_key, description, default_enabled, rollout_percentage, kill_switch) VALUES (:flag_key, :description, :default_enabled, :rollout_percentage, :kill_switch) RETURNING *",
        payload.model_dump(),
    )
    _audit(repository, actor, metadata, action_key="platform.feature_flag.created", object_table="feature_flag_registry", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.get("/feature-flags/{flag_id}", response_model=Envelope)
def get_feature_flag(flag_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature_flag.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.feature_flag_registry", flag_id), metadata)


@router.patch("/feature-flags/{flag_id}", response_model=Envelope)
def update_feature_flag(flag_id: UUID, payload: FeatureFlagUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature_flag.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.feature_flag_registry", flag_id)
    after = repository.update_by_id(table="platform.feature_flag_registry", entity_id=flag_id, values=payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.feature_flag.updated", object_table="feature_flag_registry", object_id=flag_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.get("/feature-flags/{flag_id}/tenant-overrides", response_model=ListEnvelope)
def list_feature_flag_overrides(flag_id: UUID, limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature_flag.read"))) -> ListEnvelope:
    repository = _repo(session)
    repository.require_by_id("platform.feature_flag_registry", flag_id)
    rows, next_cursor, has_more = repository.list_page(table="platform.feature_flag_tenant_overrides", limit=limit, cursor=cursor, filters={"feature_flag_id": flag_id})
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.put("/feature-flags/{flag_id}/tenant-overrides/{tenant_id}", response_model=Envelope)
def upsert_feature_flag_override(flag_id: UUID, tenant_id: UUID, payload: TenantFeatureFlagOverrideRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature_flag.manage"))) -> Envelope:
    repository = _repo(session)
    repository.require_by_id("platform.feature_flag_registry", flag_id)
    _require_tenant(repository, tenant_id)
    before = repository.one("SELECT * FROM platform.feature_flag_tenant_overrides WHERE feature_flag_id = :flag_id AND tenant_id = :tenant_id AND expires_at IS NULL ORDER BY created_at DESC LIMIT 1", {"flag_id": flag_id, "tenant_id": tenant_id})
    if before is None:
        after = repository.execute_returning_one(
            """
            INSERT INTO platform.feature_flag_tenant_overrides (
              tenant_id, feature_flag_id, is_enabled, reason, created_by_platform_user_id, expires_at
            )
            VALUES (:tenant_id, :feature_flag_id, :is_enabled, :reason, :created_by_platform_user_id, :expires_at)
            RETURNING *
            """,
            {"tenant_id": tenant_id, "feature_flag_id": flag_id, "created_by_platform_user_id": actor.platform_user_id, **payload.model_dump()},
        )
    else:
        after = repository.update_by_id(
            table="platform.feature_flag_tenant_overrides",
            entity_id=before["id"],
            values=payload.model_dump(),
            touch_updated_at=False,
        )
    _audit(repository, actor, metadata, action_key="platform.feature_flag.tenant_override_updated", object_table="feature_flag_tenant_overrides", object_id=after["id"], tenant_id=tenant_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.delete("/feature-flags/{flag_id}/tenant-overrides/{tenant_id}", response_model=Envelope)
def delete_feature_flag_override(flag_id: UUID, tenant_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.feature_flag.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.one("SELECT * FROM platform.feature_flag_tenant_overrides WHERE feature_flag_id = :flag_id AND tenant_id = :tenant_id AND expires_at IS NULL", {"flag_id": flag_id, "tenant_id": tenant_id})
    if before is None:
        raise NotFoundError("Feature flag override not found", safe_detail="Feature flag override not found")
    after = repository.execute_returning_one("UPDATE platform.feature_flag_tenant_overrides SET expires_at = now() WHERE id = :id RETURNING *", {"id": before["id"]})
    _audit(repository, actor, metadata, action_key="platform.feature_flag.tenant_override_deleted", object_table="feature_flag_tenant_overrides", object_id=before["id"], tenant_id=tenant_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.get("/users", response_model=ListEnvelope)
def list_users(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, status: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.user.read"))) -> ListEnvelope:
    repository = _repo(session)
    rows, next_cursor, has_more = repository.list_page(table="platform.platform_users", limit=limit, cursor=cursor, filters={"status": status}, search_columns=("email", "display_name"), search=None)
    rows = [_public_platform_user(row) for row in rows]
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/users", response_model=Envelope)
def create_user(payload: PlatformUserCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.user.manage"))) -> Envelope:
    repository = _repo(session)
    row = repository.execute_returning_one("INSERT INTO platform.platform_users (email, display_name, status) VALUES (:email, :display_name, 'invited') RETURNING id, email::text AS email, display_name, status::text AS status, email_verified_at, mfa_required, last_login_at, created_at, updated_at, deleted_at", payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.user.created", object_table="platform_users", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.get("/users/{platform_user_id}", response_model=Envelope)
def get_user(platform_user_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.user.read"))) -> Envelope:
    return _single(_public_platform_user(_repo(session).require_by_id("platform.platform_users", platform_user_id)), metadata)


@router.patch("/users/{platform_user_id}", response_model=Envelope)
def update_user(platform_user_id: UUID, payload: PlatformUserUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.user.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.platform_users", platform_user_id)
    after = repository.update_by_id(table="platform.platform_users", entity_id=platform_user_id, values=payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.user.updated", object_table="platform_users", object_id=platform_user_id, before_state=before, after_state=after)
    return _single(_public_platform_user(after), metadata)


def _active_super_admin_count(repository: PlatformAdminRepository) -> int:
    row = repository.one(
        """
        SELECT count(DISTINCT u.id)::int AS total
        FROM platform.platform_users u
        JOIN platform.platform_user_roles ur ON ur.platform_user_id = u.id
        JOIN platform.platform_roles r ON r.id = ur.role_id
        WHERE u.status = 'active' AND u.deleted_at IS NULL AND r.role_key = 'super_admin'
        """,
        {},
    )
    return int(row["total"] if row else 0)


def _set_user_status(platform_user_id: UUID, status: str, action_key: str, metadata: RequestMetadata, session: Session, actor: PlatformAdminActorContext) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.platform_users", platform_user_id)
    role_keys = {
        row["role_key"]
        for row in repository.many(
            "SELECT r.role_key::text AS role_key FROM platform.platform_user_roles ur JOIN platform.platform_roles r ON r.id = ur.role_id WHERE ur.platform_user_id = :id",
            {"id": platform_user_id},
        )
    }
    if before["status"] == "active" and status != "active" and "super_admin" in role_keys and _active_super_admin_count(repository) <= 1:
        raise ConflictError("Cannot deactivate the last active super admin", safe_detail="Cannot deactivate the last active super admin")
    after = repository.update_by_id(table="platform.platform_users", entity_id=platform_user_id, values={"status": status})
    _audit(repository, actor, metadata, action_key=action_key, object_table="platform_users", object_id=platform_user_id, before_state=before, after_state=after)
    return _single(_public_platform_user(after), metadata)


@router.post("/users/{platform_user_id}/activate", response_model=Envelope)
def activate_user(platform_user_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.user.manage"))) -> Envelope:
    return _set_user_status(platform_user_id, "active", "platform.user.activated", metadata, session, actor)


@router.post("/users/{platform_user_id}/deactivate", response_model=Envelope)
def deactivate_user(platform_user_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.user.manage"))) -> Envelope:
    return _set_user_status(platform_user_id, "suspended", "platform.user.deactivated", metadata, session, actor)


@router.post("/users/{platform_user_id}/lock", response_model=Envelope)
def lock_user(platform_user_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.user.manage"))) -> Envelope:
    return _set_user_status(platform_user_id, "locked", "platform.user.locked", metadata, session, actor)


@router.post("/users/{platform_user_id}/unlock", response_model=Envelope)
def unlock_user(platform_user_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.user.manage"))) -> Envelope:
    return _set_user_status(platform_user_id, "active", "platform.user.unlocked", metadata, session, actor)


@router.get("/users/{platform_user_id}/roles", response_model=ListEnvelope)
def get_user_roles(platform_user_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.role.read"))) -> ListEnvelope:
    rows = _repo(session).many("SELECT r.* FROM platform.platform_user_roles ur JOIN platform.platform_roles r ON r.id = ur.role_id WHERE ur.platform_user_id = :id ORDER BY r.role_key", {"id": platform_user_id})
    return _list(rows, limit=len(rows), next_cursor=None, has_more=False, metadata=metadata)


@router.put("/users/{platform_user_id}/roles", response_model=Envelope)
def replace_user_roles(platform_user_id: UUID, payload: RoleIdsReplaceRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.user.manage"))) -> Envelope:
    role_ids = payload.role_ids
    repository = _repo(session)
    repository.require_by_id("platform.platform_users", platform_user_id)
    before = repository.many("SELECT * FROM platform.platform_user_roles WHERE platform_user_id = :id", {"id": platform_user_id})
    if platform_user_id == actor.platform_user_id:
        existing_super = repository.one("SELECT 1 FROM platform.platform_user_roles ur JOIN platform.platform_roles r ON r.id = ur.role_id WHERE ur.platform_user_id = :id AND r.role_key = 'super_admin'", {"id": platform_user_id})
        requested_super = any(repository.one("SELECT 1 FROM platform.platform_roles WHERE id = :id AND role_key = 'super_admin'", {"id": role_id}) for role_id in role_ids)
        if existing_super and not requested_super and _active_super_admin_count(repository) <= 1:
            raise ConflictError("Cannot remove your own final super-admin role", safe_detail="Cannot remove your own final super-admin role")
    repository.execute("DELETE FROM platform.platform_user_roles WHERE platform_user_id = :id", {"id": platform_user_id})
    for role_id in role_ids:
        repository.require_by_id("platform.platform_roles", role_id)
        repository.execute("INSERT INTO platform.platform_user_roles (platform_user_id, role_id) VALUES (:platform_user_id, :role_id)", {"platform_user_id": platform_user_id, "role_id": role_id})
    after = repository.many("SELECT * FROM platform.platform_user_roles WHERE platform_user_id = :id", {"id": platform_user_id})
    _audit(repository, actor, metadata, action_key="platform.user.roles_updated", object_table="platform_user_roles", object_id=platform_user_id, before_state={"items": before}, after_state={"items": after})
    return _single({"items": after}, metadata)


@router.get("/roles", response_model=ListEnvelope)
def list_roles(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.role.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.platform_roles", limit=limit, cursor=cursor, search_columns=("role_key", "name"), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/roles", response_model=Envelope)
def create_role(payload: RoleCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.role.manage"))) -> Envelope:
    repository = _repo(session)
    row = repository.execute_returning_one("INSERT INTO platform.platform_roles (role_key, name, description) VALUES (:role_key, :name, :description) RETURNING *", payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.role.created", object_table="platform_roles", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.get("/roles/{role_id}", response_model=Envelope)
def get_role(role_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.role.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.platform_roles", role_id), metadata)


@router.patch("/roles/{role_id}", response_model=Envelope)
def update_role(role_id: UUID, payload: RoleUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.role.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.platform_roles", role_id)
    after = repository.update_by_id(table="platform.platform_roles", entity_id=role_id, values=payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.role.updated", object_table="platform_roles", object_id=role_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.delete("/roles/{role_id}", response_model=Envelope)
def delete_role(role_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.role.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.platform_roles", role_id)
    if before["role_key"] in {"super_admin", "support_admin", "ai_governance_admin"}:
        raise ConflictError("System roles cannot be deleted", safe_detail="System roles cannot be deleted")
    repository.execute("DELETE FROM platform.platform_user_roles WHERE role_id = :id", {"id": role_id})
    repository.execute("DELETE FROM platform.platform_role_permissions WHERE role_id = :id", {"id": role_id})
    repository.execute("DELETE FROM platform.platform_roles WHERE id = :id", {"id": role_id})
    _audit(repository, actor, metadata, action_key="platform.role.deleted", object_table="platform_roles", object_id=role_id, before_state=before, after_state={})
    return _single({"deleted": True}, metadata)


@router.get("/roles/{role_id}/permissions", response_model=ListEnvelope)
def get_role_permissions(role_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.role.read"))) -> ListEnvelope:
    rows = _repo(session).many("SELECT p.* FROM platform.platform_role_permissions rp JOIN platform.platform_permissions p ON p.id = rp.permission_id WHERE rp.role_id = :id ORDER BY p.permission_key", {"id": role_id})
    return _list(rows, limit=len(rows), next_cursor=None, has_more=False, metadata=metadata)


@router.put("/roles/{role_id}/permissions", response_model=Envelope)
def replace_role_permissions(role_id: UUID, payload: PermissionIdsReplaceRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.role.manage"))) -> Envelope:
    permission_ids = payload.permission_ids
    repository = _repo(session)
    repository.require_by_id("platform.platform_roles", role_id)
    before = repository.many("SELECT * FROM platform.platform_role_permissions WHERE role_id = :id", {"id": role_id})
    repository.execute("DELETE FROM platform.platform_role_permissions WHERE role_id = :id", {"id": role_id})
    for permission_id in permission_ids:
        repository.require_by_id("platform.platform_permissions", permission_id)
        repository.execute("INSERT INTO platform.platform_role_permissions (role_id, permission_id) VALUES (:role_id, :permission_id)", {"role_id": role_id, "permission_id": permission_id})
    after = repository.many("SELECT * FROM platform.platform_role_permissions WHERE role_id = :id", {"id": role_id})
    _audit(repository, actor, metadata, action_key="platform.role.permissions_updated", object_table="platform_role_permissions", object_id=role_id, before_state={"items": before}, after_state={"items": after})
    return _single({"items": after}, metadata)


@router.get("/permissions", response_model=ListEnvelope)
def list_permissions(limit: int = Query(default=200, ge=1, le=500), cursor: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.role.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.platform_permissions", limit=limit, cursor=cursor, search_columns=("permission_key", "description"), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.get("/support-sessions", response_model=ListEnvelope)
def list_support_sessions(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, tenant_id: UUID | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.support_session.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.support_sessions", limit=limit, cursor=cursor, filters={"tenant_id": tenant_id})
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/support-sessions", response_model=Envelope)
def create_support_session(payload: SupportSessionCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.support_session.manage"))) -> Envelope:
    if payload.expires_at <= datetime.now(UTC):
        raise ValidationFailure("expires_at must be in the future", safe_detail="expires_at must be in the future")
    repository = _repo(session)
    tenant = _require_tenant(repository, payload.tenant_id)
    if tenant["status"] in {"churned", "pending_deletion", "deleted"}:
        raise ConflictError("Support session is not allowed for this tenant status", safe_detail="Support session is not allowed for this tenant status")
    row = repository.execute_returning_one(
        "INSERT INTO platform.support_sessions (tenant_id, platform_user_id, reason, expires_at) VALUES (:tenant_id, :platform_user_id, :reason, :expires_at) RETURNING *",
        {"tenant_id": payload.tenant_id, "platform_user_id": actor.platform_user_id, "reason": payload.reason, "expires_at": payload.expires_at},
    )
    _audit(repository, actor, metadata, action_key="platform.support_session.created", object_table="support_sessions", object_id=row["id"], tenant_id=payload.tenant_id, after_state=row)
    return _single(row, metadata)


@router.get("/support-sessions/{support_session_id}", response_model=Envelope)
def get_support_session(support_session_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.support_session.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.support_sessions", support_session_id), metadata)


@router.post("/support-sessions/{support_session_id}/end", response_model=Envelope)
def end_support_session(support_session_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.support_session.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.support_sessions", support_session_id)
    after = repository.execute_returning_one("UPDATE platform.support_sessions SET ended_at = COALESCE(ended_at, now()) WHERE id = :id RETURNING *", {"id": support_session_id})
    _audit(repository, actor, metadata, action_key="platform.support_session.ended", object_table="support_sessions", object_id=support_session_id, tenant_id=before["tenant_id"], before_state=before, after_state=after)
    return _single(after, metadata)


@router.get("/support-tickets", response_model=ListEnvelope)
def list_support_tickets(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, tenant_id: UUID | None = None, status: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.support_ticket.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.support_tickets", limit=limit, cursor=cursor, filters={"tenant_id": tenant_id, "status": status}, search_columns=("subject", "description"), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/support-tickets", response_model=Envelope)
def create_support_ticket(payload: SupportTicketCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.support_ticket.manage"))) -> Envelope:
    _validate(payload.priority, TICKET_PRIORITIES, "priority")
    repository = _repo(session)
    _require_tenant(repository, payload.tenant_id)
    row = repository.execute_returning_one(
        """
        INSERT INTO platform.support_tickets (tenant_id, requester_email, subject, description, priority)
        VALUES (:tenant_id, :requester_email, :subject, :description, :priority)
        RETURNING *
        """,
        {
            "tenant_id": payload.tenant_id,
            "requester_email": actor.email,
            "subject": payload.title,
            "description": payload.description,
            "priority": payload.priority,
        },
    )
    _audit(repository, actor, metadata, action_key="platform.support_ticket.created", object_table="support_tickets", object_id=row["id"], tenant_id=payload.tenant_id, after_state=row)
    return _single(row, metadata)


@router.get("/support-tickets/{ticket_id}", response_model=Envelope)
def get_support_ticket(ticket_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.support_ticket.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.support_tickets", ticket_id), metadata)


@router.patch("/support-tickets/{ticket_id}", response_model=Envelope)
def update_support_ticket(ticket_id: UUID, payload: SupportTicketUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.support_ticket.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.support_tickets", ticket_id)
    values = payload.model_dump()
    if values.get("title") is not None:
        values["subject"] = values.pop("title")
    if values.get("status") is not None:
        _validate(values["status"], TICKET_STATUSES, "status")
    if values.get("priority") is not None:
        _validate(values["priority"], TICKET_PRIORITIES, "priority")
    after = repository.update_by_id(table="platform.support_tickets", entity_id=ticket_id, values=values)
    _audit(repository, actor, metadata, action_key="platform.support_ticket.updated", object_table="support_tickets", object_id=ticket_id, tenant_id=before["tenant_id"], before_state=before, after_state=after)
    return _single(after, metadata)


@router.post("/support-tickets/{ticket_id}/assign", response_model=Envelope)
def assign_support_ticket(ticket_id: UUID, payload: AssignTicketRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.support_ticket.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.support_tickets", ticket_id)
    assignee = repository.require_by_id("platform.platform_users", payload.assigned_platform_user_id)
    if assignee["status"] != "active":
        raise ConflictError("Ticket assignee must be active", safe_detail="Ticket assignee must be active")
    after = repository.update_by_id(table="platform.support_tickets", entity_id=ticket_id, values={"assigned_platform_user_id": payload.assigned_platform_user_id, "status": "in_progress"})
    _audit(repository, actor, metadata, action_key="platform.support_ticket.assigned", object_table="support_tickets", object_id=ticket_id, tenant_id=before["tenant_id"], before_state=before, after_state=after)
    return _single(after, metadata)


@router.post("/support-tickets/{ticket_id}/close", response_model=Envelope)
def close_support_ticket(ticket_id: UUID, payload: CloseTicketRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.support_ticket.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.support_tickets", ticket_id)
    after = repository.execute_returning_one("UPDATE platform.support_tickets SET status = 'closed', closed_at = now(), updated_at = now() WHERE id = :id RETURNING *", {"id": ticket_id})
    _audit(repository, actor, metadata, action_key="platform.support_ticket.closed", object_table="support_tickets", object_id=ticket_id, tenant_id=before["tenant_id"], before_state=before, after_state={**after, "resolution_summary": payload.resolution_summary})
    return _single(after, metadata)


@router.get("/sla-policies", response_model=ListEnvelope)
def list_sla_policies(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.sla.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.sla_policies", limit=limit, cursor=cursor, search_columns=("policy_key", "name"), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/sla-policies", response_model=Envelope)
def create_sla_policy(payload: SlaPolicyCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.sla.manage"))) -> Envelope:
    _validate(payload.severity, SLA_SEVERITIES, "severity")
    repository = _repo(session)
    row = repository.execute_returning_one("INSERT INTO platform.sla_policies (policy_key, name, severity, response_minutes, resolution_minutes) VALUES (:policy_key, :name, :severity, :response_minutes, :resolution_minutes) RETURNING *", payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.sla_policy.created", object_table="sla_policies", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.get("/sla-policies/{sla_policy_id}", response_model=Envelope)
def get_sla_policy(sla_policy_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.sla.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.sla_policies", sla_policy_id), metadata)


@router.patch("/sla-policies/{sla_policy_id}", response_model=Envelope)
def update_sla_policy(sla_policy_id: UUID, payload: SlaPolicyUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.sla.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.sla_policies", sla_policy_id)
    values = payload.model_dump()
    if values.get("severity") is not None:
        _validate(values["severity"], SLA_SEVERITIES, "severity")
    response_minutes = values["response_minutes"] if values.get("response_minutes") is not None else before["response_minutes"]
    resolution_minutes = values["resolution_minutes"] if values.get("resolution_minutes") is not None else before["resolution_minutes"]
    if resolution_minutes < response_minutes:
        raise ValidationFailure("resolution_minutes must be greater than or equal to response_minutes", safe_detail="resolution_minutes must be greater than or equal to response_minutes")
    after = repository.update_by_id(table="platform.sla_policies", entity_id=sla_policy_id, values=values)
    _audit(repository, actor, metadata, action_key="platform.sla_policy.updated", object_table="sla_policies", object_id=sla_policy_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.get("/compliance/frameworks", response_model=ListEnvelope)
def list_compliance_frameworks(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.compliance.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.compliance_frameworks", limit=limit, cursor=cursor, search_columns=("framework", "display_name"), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/compliance/frameworks", response_model=Envelope)
def create_compliance_framework(payload: ComplianceFrameworkCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.compliance.manage"))) -> Envelope:
    _validate(payload.framework, COMPLIANCE_FRAMEWORKS, "framework")
    repository = _repo(session)
    row = repository.execute_returning_one("INSERT INTO platform.compliance_frameworks (framework, display_name, description) VALUES (:framework, :display_name, :description) RETURNING *", payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.compliance.framework_created", object_table="compliance_frameworks", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.get("/compliance/frameworks/{framework_id}", response_model=Envelope)
def get_compliance_framework(framework_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.compliance.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.compliance_frameworks", framework_id), metadata)


@router.patch("/compliance/frameworks/{framework_id}", response_model=Envelope)
def update_compliance_framework(framework_id: UUID, payload: ComplianceFrameworkUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.compliance.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.compliance_frameworks", framework_id)
    after = repository.update_by_id(table="platform.compliance_frameworks", entity_id=framework_id, values=payload.model_dump(), touch_updated_at=False)
    _audit(repository, actor, metadata, action_key="platform.compliance.framework_updated", object_table="compliance_frameworks", object_id=framework_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.get("/compliance/frameworks/{framework_id}/regions", response_model=ListEnvelope)
def get_compliance_framework_regions(framework_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.compliance.read"))) -> ListEnvelope:
    rows = _repo(session).many("SELECT * FROM platform.compliance_framework_regions WHERE framework_id = :id ORDER BY region", {"id": framework_id})
    return _list(rows, limit=len(rows), next_cursor=None, has_more=False, metadata=metadata)


@router.put("/compliance/frameworks/{framework_id}/regions", response_model=Envelope)
def replace_compliance_framework_regions(framework_id: UUID, payload: RegionsReplaceRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.compliance.manage"))) -> Envelope:
    repository = _repo(session)
    repository.require_by_id("platform.compliance_frameworks", framework_id)
    for region in payload.regions:
        _validate(region, REGIONS, "region")
    before = repository.many("SELECT * FROM platform.compliance_framework_regions WHERE framework_id = :id", {"id": framework_id})
    repository.execute("DELETE FROM platform.compliance_framework_regions WHERE framework_id = :id", {"id": framework_id})
    for region in payload.regions:
        repository.execute("INSERT INTO platform.compliance_framework_regions (framework_id, region) VALUES (:framework_id, :region)", {"framework_id": framework_id, "region": region})
    after = repository.many("SELECT * FROM platform.compliance_framework_regions WHERE framework_id = :id", {"id": framework_id})
    _audit(repository, actor, metadata, action_key="platform.compliance.framework_regions_updated", object_table="compliance_framework_regions", object_id=framework_id, before_state={"items": before}, after_state={"items": after})
    return _single({"items": after}, metadata)


@router.get("/tenants/{tenant_id}/compliance-frameworks", response_model=ListEnvelope)
def get_tenant_compliance_frameworks(tenant_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.compliance.read"))) -> ListEnvelope:
    rows = _repo(session).many("SELECT * FROM platform.tenant_compliance_frameworks WHERE tenant_id = :tenant_id AND disabled_at IS NULL ORDER BY created_at, id", {"tenant_id": tenant_id})
    return _list(rows, limit=len(rows), next_cursor=None, has_more=False, metadata=metadata)


@router.put("/tenants/{tenant_id}/compliance-frameworks", response_model=Envelope)
def replace_tenant_compliance_frameworks(tenant_id: UUID, payload: TenantFrameworksReplaceRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.compliance.manage"))) -> Envelope:
    repository = _repo(session)
    _require_tenant(repository, tenant_id)
    before = repository.many("SELECT * FROM platform.tenant_compliance_frameworks WHERE tenant_id = :tenant_id AND disabled_at IS NULL", {"tenant_id": tenant_id})
    repository.execute("UPDATE platform.tenant_compliance_frameworks SET disabled_at = COALESCE(disabled_at, now()) WHERE tenant_id = :tenant_id AND disabled_at IS NULL", {"tenant_id": tenant_id})
    for framework_id in payload.framework_ids:
        repository.require_by_id("platform.compliance_frameworks", framework_id)
        repository.execute("INSERT INTO platform.tenant_compliance_frameworks (tenant_id, framework_id) VALUES (:tenant_id, :framework_id)", {"tenant_id": tenant_id, "framework_id": framework_id})
    after = repository.many("SELECT * FROM platform.tenant_compliance_frameworks WHERE tenant_id = :tenant_id AND disabled_at IS NULL", {"tenant_id": tenant_id})
    _audit(repository, actor, metadata, action_key="platform.compliance.tenant_frameworks_updated", object_table="tenant_compliance_frameworks", object_id=tenant_id, tenant_id=tenant_id, before_state={"items": before}, after_state={"items": after})
    return _single({"items": after}, metadata)


@router.get("/ai/models", response_model=ListEnvelope)
def list_ai_models(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, provider: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.ai_governance.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.ai_model_definitions", limit=limit, cursor=cursor, filters={"provider": provider}, search_columns=("model_key", "display_name"), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/ai/models", response_model=Envelope)
def create_ai_model(payload: AiModelCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.ai_governance.manage"))) -> Envelope:
    _validate(payload.provider, AI_PROVIDERS, "provider")
    repository = _repo(session)
    row = repository.execute_returning_one(
        """
        INSERT INTO platform.ai_model_definitions (
          provider, model_key, display_name, max_context_tokens, supports_embeddings,
          supports_audio, supports_video, is_active
        )
        VALUES (
          :provider, :model_key, :display_name, :max_context_tokens, :supports_embeddings,
          :supports_audio, :supports_video, :is_active
        )
        RETURNING *
        """,
        payload.model_dump(),
    )
    _audit(repository, actor, metadata, action_key="platform.ai_model.created", object_table="ai_model_definitions", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.get("/ai/models/{model_id}", response_model=Envelope)
def get_ai_model(model_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.ai_governance.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.ai_model_definitions", model_id), metadata)


@router.patch("/ai/models/{model_id}", response_model=Envelope)
def update_ai_model(model_id: UUID, payload: AiModelUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.ai_governance.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.ai_model_definitions", model_id)
    after = repository.update_by_id(table="platform.ai_model_definitions", entity_id=model_id, values=payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.ai_model.updated", object_table="ai_model_definitions", object_id=model_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.get("/ai/models/{model_id}/region-restrictions", response_model=ListEnvelope)
def get_ai_model_region_restrictions(model_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.ai_governance.read"))) -> ListEnvelope:
    rows = _repo(session).many("SELECT * FROM platform.ai_model_region_restrictions WHERE model_definition_id = :id ORDER BY region", {"id": model_id})
    return _list(rows, limit=len(rows), next_cursor=None, has_more=False, metadata=metadata)


@router.put("/ai/models/{model_id}/region-restrictions", response_model=Envelope)
def replace_ai_model_region_restrictions(model_id: UUID, payload: RegionsReplaceRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.ai_governance.manage"))) -> Envelope:
    repository = _repo(session)
    repository.require_by_id("platform.ai_model_definitions", model_id)
    for region in payload.regions:
        _validate(region, REGIONS, "region")
    before = repository.many("SELECT * FROM platform.ai_model_region_restrictions WHERE model_definition_id = :id", {"id": model_id})
    repository.execute("DELETE FROM platform.ai_model_region_restrictions WHERE model_definition_id = :id", {"id": model_id})
    for region in payload.regions:
        repository.execute("INSERT INTO platform.ai_model_region_restrictions (model_definition_id, region) VALUES (:model_id, :region)", {"model_id": model_id, "region": region})
    after = repository.many("SELECT * FROM platform.ai_model_region_restrictions WHERE model_definition_id = :id", {"id": model_id})
    _audit(repository, actor, metadata, action_key="platform.ai_region_restrictions.updated", object_table="ai_model_region_restrictions", object_id=model_id, before_state={"items": before}, after_state={"items": after})
    return _single({"items": after}, metadata)


@router.get("/ai/quality-metrics", response_model=ListEnvelope)
def list_ai_quality_metrics(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, tenant_id: UUID | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.ai_governance.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.ai_quality_metrics", limit=limit, cursor=cursor, filters={"tenant_id": tenant_id})
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.get("/ai/governance-alerts", response_model=ListEnvelope)
def list_ai_governance_alerts(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, status: str | None = None, tenant_id: UUID | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.ai_governance.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.ai_governance_alerts", limit=limit, cursor=cursor, filters={"status": status, "tenant_id": tenant_id}, search_columns=("alert_key", "title"), search=None, order_column="opened_at")
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.get("/ai/governance-alerts/{alert_id}", response_model=Envelope)
def get_ai_governance_alert(alert_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.ai_governance.read"))) -> Envelope:
    repository = _repo(session)
    alert = repository.require_by_id("platform.ai_governance_alerts", alert_id)
    evidence = repository.many("SELECT * FROM platform.ai_governance_alert_evidence WHERE alert_id = :id ORDER BY created_at, id", {"id": alert_id})
    return _single({"alert": alert, "evidence": evidence}, metadata)


def _set_ai_alert_status(alert_id: UUID, status: str, action_key: str, metadata: RequestMetadata, session: Session, actor: PlatformAdminActorContext) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.ai_governance_alerts", alert_id)
    if before["status"] not in {"open", "acknowledged"}:
        raise ConflictError("AI governance alert is already closed", safe_detail="AI governance alert is already closed")
    resolved_fragment = ", resolved_at = now()" if status == "resolved" else ""
    after = repository.execute_returning_one(f"UPDATE platform.ai_governance_alerts SET status = :status{resolved_fragment} WHERE id = :id RETURNING *", {"id": alert_id, "status": status})
    _audit(repository, actor, metadata, action_key=action_key, object_table="ai_governance_alerts", object_id=alert_id, tenant_id=before["tenant_id"], before_state=before, after_state=after)
    return _single(after, metadata)


@router.post("/ai/governance-alerts/{alert_id}/acknowledge", response_model=Envelope)
def acknowledge_ai_governance_alert(alert_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.ai_governance.manage"))) -> Envelope:
    return _set_ai_alert_status(alert_id, "acknowledged", "platform.ai_governance_alert.acknowledged", metadata, session, actor)


@router.post("/ai/governance-alerts/{alert_id}/resolve", response_model=Envelope)
def resolve_ai_governance_alert(alert_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.ai_governance.manage"))) -> Envelope:
    return _set_ai_alert_status(alert_id, "resolved", "platform.ai_governance_alert.resolved", metadata, session, actor)


@router.get("/api-versions", response_model=ListEnvelope)
def list_api_versions(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.operations.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.api_versions", limit=limit, cursor=cursor, search_columns=("version_label",), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/api-versions", response_model=Envelope)
def create_api_version(payload: ApiVersionCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.operations.manage"))) -> Envelope:
    repository = _repo(session)
    row = repository.execute_returning_one("INSERT INTO platform.api_versions (version_label, released_at, deprecated_at, sunset_at, migration_guide_url) VALUES (:version_label, :released_at, :deprecated_at, :sunset_at, :migration_guide_url) RETURNING *", payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.api_version.created", object_table="api_versions", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.patch("/api-versions/{api_version_id}", response_model=Envelope)
def update_api_version(api_version_id: UUID, payload: ApiVersionUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.operations.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.api_versions", api_version_id)
    after = repository.update_by_id(table="platform.api_versions", entity_id=api_version_id, values=payload.model_dump(), touch_updated_at=False)
    _audit(repository, actor, metadata, action_key="platform.api_version.updated", object_table="api_versions", object_id=api_version_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.get("/deployments", response_model=ListEnvelope)
def list_deployments(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, environment: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.operations.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.deployments", limit=limit, cursor=cursor, filters={"environment": environment}, order_column="started_at")
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.get("/deployments/{deployment_id}", response_model=Envelope)
def get_deployment(deployment_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.operations.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.deployments", deployment_id), metadata)


@router.get("/slo-definitions", response_model=ListEnvelope)
def list_slo_definitions(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, service_name: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.operations.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.slo_definitions", limit=limit, cursor=cursor, filters={"service_name": service_name}, search_columns=("slo_key", "service_name"), search=None)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.post("/slo-definitions", response_model=Envelope)
def create_slo_definition(payload: SloCreateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.operations.manage"))) -> Envelope:
    repository = _repo(session)
    row = repository.execute_returning_one("INSERT INTO platform.slo_definitions (slo_key, service_name, objective_percent, window_days) VALUES (:slo_key, :service_name, :objective_percent, :window_days) RETURNING *", payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.slo.created", object_table="slo_definitions", object_id=row["id"], after_state=row)
    return _single(row, metadata)


@router.patch("/slo-definitions/{slo_id}", response_model=Envelope)
def update_slo_definition(slo_id: UUID, payload: SloUpdateRequest, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.operations.manage"))) -> Envelope:
    repository = _repo(session)
    before = repository.require_by_id("platform.slo_definitions", slo_id)
    after = repository.update_by_id(table="platform.slo_definitions", entity_id=slo_id, values=payload.model_dump())
    _audit(repository, actor, metadata, action_key="platform.slo.updated", object_table="slo_definitions", object_id=slo_id, before_state=before, after_state=after)
    return _single(after, metadata)


@router.get("/error-budgets", response_model=ListEnvelope)
def list_error_budgets(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.operations.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(table="platform.error_budget_status", limit=limit, cursor=cursor)
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.get("/audit-logs", response_model=ListEnvelope)
def list_audit_logs(limit: int = Query(default=50, ge=1, le=200), cursor: str | None = None, tenant_id: UUID | None = None, actor_type: str | None = None, actor_platform_user_id: UUID | None = None, action_key: str | None = None, object_schema: str | None = None, object_table: str | None = None, object_id: UUID | None = None, request_id: str | None = None, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.audit_log.read"))) -> ListEnvelope:
    rows, next_cursor, has_more = _repo(session).list_page(
        table="platform.audit_logs",
        limit=limit,
        cursor=cursor,
        filters={
            "tenant_id": tenant_id,
            "actor_type": actor_type,
            "actor_platform_user_id": actor_platform_user_id,
            "action_key": action_key,
            "object_schema": object_schema,
            "object_table": object_table,
            "object_id": object_id,
            "request_id": request_id,
        },
        order_column="occurred_at",
    )
    return _list(rows, limit=limit, next_cursor=next_cursor, has_more=has_more, metadata=metadata)


@router.get("/audit-logs/{audit_log_id}", response_model=Envelope)
def get_audit_log(audit_log_id: UUID, metadata: RequestMetadata = Depends(request_metadata), session: Session = Depends(session_dependency), actor: PlatformAdminActorContext = Depends(require_platform_permission("platform.audit_log.read"))) -> Envelope:
    return _single(_repo(session).require_by_id("platform.audit_logs", audit_log_id), metadata)


SCOPE_TAGS = {
    "dashboard": "Platform Admin / Dashboard",
    "tenant": "Platform Admin / Tenancy",
    "tenant_domain": "Platform Admin / Tenant Domains",
    "provisioning": "Platform Admin / Provisioning",
    "infra_pool": "Platform Admin / Infrastructure Pools",
    "plan": "Platform Admin / Catalogue / Plans",
    "quota": "Platform Admin / Catalogue / Quotas",
    "feature": "Platform Admin / Catalogue / Features",
    "addon": "Platform Admin / Catalogue / Add-ons",
    "entitlement": "Platform Admin / Entitlements",
    "feature_flag": "Platform Admin / Feature Flags",
    "access_control": "Platform Admin / Access Control",
    "support": "Platform Admin / Support",
    "compliance": "Platform Admin / Compliance",
    "ai_governance": "Platform Admin / AI Governance",
    "operations": "Platform Admin / Operations",
    "audit": "Platform Admin / Audit Logs",
}


def _route_scope(path: str) -> str:
    if path.endswith("/dashboard/summary"):
        return "dashboard"
    if "/domains" in path:
        return "tenant_domain"
    if "/effective-entitlements" in path or "/subscription-summary" in path:
        return "entitlement"
    if "/provisioning-jobs" in path:
        return "provisioning"
    if path.startswith("/v1/platform-admin/infra-pools"):
        return "infra_pool"
    if path.startswith("/v1/platform-admin/plans"):
        if path.endswith("/features") or "/features" in path:
            return "feature"
        if path.endswith("/quotas") or "/quotas" in path:
            return "quota"
        return "plan"
    if path.startswith("/v1/platform-admin/quotas"):
        return "quota"
    if path.startswith("/v1/platform-admin/features"):
        return "feature"
    if path.startswith("/v1/platform-admin/addons"):
        return "addon"
    if path.startswith("/v1/platform-admin/feature-flags"):
        return "feature_flag"
    if path.startswith("/v1/platform-admin/users") or path.startswith("/v1/platform-admin/roles") or path.startswith("/v1/platform-admin/permissions"):
        return "access_control"
    if path.startswith("/v1/platform-admin/access-control"):
        return "access_control"
    if path.startswith("/v1/platform-admin/support") or path.startswith("/v1/platform-admin/sla"):
        return "support"
    if "/compliance" in path:
        return "compliance"
    if path.startswith("/v1/platform-admin/ai"):
        return "ai_governance"
    if path.startswith("/v1/platform-admin/api-versions") or path.startswith("/v1/platform-admin/deployments") or path.startswith("/v1/platform-admin/slo-definitions") or path.startswith("/v1/platform-admin/error-budgets"):
        return "operations"
    if path.startswith("/v1/platform-admin/audit-logs"):
        return "audit"
    return "tenant"


def _route_permission(path: str, methods: set[str]) -> str:
    is_read = methods == {"GET"}
    scope = _route_scope(path)
    if scope == "dashboard":
        return "platform.dashboard.read"
    if scope == "tenant_domain":
        return "platform.tenant.read" if is_read else "platform.tenant.domain.manage"
    if scope == "provisioning":
        return "platform.provisioning.read" if is_read else "platform.provisioning.manage"
    if scope == "infra_pool":
        return "platform.infra_pool.read" if is_read else "platform.infra_pool.manage"
    if scope == "plan":
        return "platform.plan.read" if is_read else "platform.plan.manage"
    if scope == "quota":
        return "platform.quota.read" if is_read else "platform.quota.manage"
    if scope == "feature":
        return "platform.feature.read" if is_read else "platform.feature.manage"
    if scope == "addon":
        return "platform.addon.read" if is_read else "platform.addon.manage"
    if scope == "entitlement":
        return "platform.entitlement.read"
    if scope == "feature_flag":
        return "platform.feature_flag.read" if is_read else "platform.feature_flag.manage"
    if scope == "access_control":
        if "/roles" in path or path.endswith("/permissions"):
            return "platform.role.read" if is_read else "platform.role.manage"
        return "platform.user.read" if is_read else "platform.user.manage"
    if scope == "support":
        if "/support-sessions" in path:
            return "platform.support_session.read" if is_read else "platform.support_session.manage"
        if "/sla-policies" in path:
            return "platform.sla.read" if is_read else "platform.sla.manage"
        return "platform.support_ticket.read" if is_read else "platform.support_ticket.manage"
    if scope == "compliance":
        return "platform.compliance.read" if is_read else "platform.compliance.manage"
    if scope == "ai_governance":
        return "platform.ai_governance.read" if is_read else "platform.ai_governance.manage"
    if scope == "operations":
        return "platform.operations.read" if is_read else "platform.operations.manage"
    if scope == "audit":
        return "platform.audit_log.read"
    if path == "/v1/platform-admin/tenants" and "POST" in methods:
        return "platform.tenant.create"
    return "platform.tenant.read" if is_read else "platform.tenant.update"


def _apply_scope_metadata() -> None:
    for route in router.routes:
        if not isinstance(route, APIRoute):
            continue
        scope = _route_scope(route.path)
        permission = _route_permission(route.path, set(route.methods or ()))
        route.tags = [SCOPE_TAGS[scope]]
        route.openapi_extra = {
            **(route.openapi_extra or {}),
            "x-platform-admin-scope": scope,
            "x-required-platform-permission": permission,
        }


def _add_access_control_aliases() -> None:
    original_routes = [route for route in router.routes if isinstance(route, APIRoute)]
    for route in original_routes:
        if route.path.startswith("/v1/platform-admin/users"):
            alias_path = route.path.replace("/v1/platform-admin/users", "/v1/platform-admin/access-control/users", 1)
        elif route.path.startswith("/v1/platform-admin/roles"):
            alias_path = route.path.replace("/v1/platform-admin/roles", "/v1/platform-admin/access-control/roles", 1)
        elif route.path.startswith("/v1/platform-admin/permissions"):
            alias_path = route.path.replace(
                "/v1/platform-admin/permissions",
                "/v1/platform-admin/access-control/permissions",
                1,
            )
        else:
            continue
        registered_alias_path = alias_path.removeprefix("/v1/platform-admin")
        router.add_api_route(
            registered_alias_path,
            route.endpoint,
            methods=list(route.methods or ()),
            response_model=route.response_model,
            status_code=route.status_code,
            tags=[SCOPE_TAGS["access_control"]],
            summary=route.summary,
            description=route.description,
            response_description=route.response_description,
            deprecated=route.deprecated,
            include_in_schema=True,
            openapi_extra={
                **(route.openapi_extra or {}),
                "x-platform-admin-scope": "access_control",
                "x-required-platform-permission": _route_permission(alias_path, set(route.methods or ())),
                "x-legacy-path": route.path,
            },
        )


_add_access_control_aliases()
_apply_scope_metadata()
