from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Meta(BaseModel):
    request_id: str


class PageMeta(BaseModel):
    limit: int
    next_cursor: str | None
    has_more: bool


class Envelope(BaseModel):
    data: Any
    meta: Meta


class ListEnvelope(BaseModel):
    data: list[dict[str, Any]]
    page: PageMeta
    meta: Meta


class ReasonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=1000)


class TenantCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=300)
    tenant_type: str
    primary_admin_email: str = Field(min_length=3, max_length=320)
    legal_entity_name: str | None = Field(default=None, max_length=300)
    plan_id: UUID | None = None
    isolation_tier: str = "shared"
    region: str = "US"
    data_residency_zone: str | None = Field(default=None, max_length=100)
    infra_pool_id: UUID | None = None
    idempotency_key: str = Field(min_length=16, max_length=255)


class TenantUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=300)
    legal_entity_name: str | None = Field(default=None, max_length=300)
    plan_id: UUID | None = None
    isolation_tier: str | None = None
    region: str | None = None
    data_residency_zone: str | None = Field(default=None, max_length=100)
    infra_pool_id: UUID | None = None
    lock_version: int | None = Field(default=None, ge=0)


class TenantDomainCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: str = Field(min_length=3, max_length=253)
    is_primary: bool = False

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        normalized = value.strip().lower().rstrip(".")
        labels = normalized.split(".")
        if len(labels) < 2 or any(not label or len(label) > 63 for label in labels):
            raise ValueError("invalid domain")
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-")
        if any(set(label) - allowed or label.startswith("-") or label.endswith("-") for label in labels):
            raise ValueError("invalid domain")
        return normalized


class TenantDomainUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_primary: bool | None = None
    verification_status: str | None = None


class ManualVerifyDomainRequest(ReasonRequest):
    pass


class PlanCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    billing_interval: str
    base_price: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    min_seats: int = Field(default=1, ge=1)
    max_seats: int | None = Field(default=None, ge=1)
    trial_days: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_seats(self) -> PlanCreateRequest:
        if self.max_seats is not None and self.max_seats < self.min_seats:
            raise ValueError("max_seats must be greater than or equal to min_seats")
        return self


class PlanUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    billing_interval: str | None = None
    base_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    min_seats: int | None = Field(default=None, ge=1)
    max_seats: int | None = Field(default=None, ge=1)
    trial_days: int | None = Field(default=None, ge=0)
    lock_version: int | None = Field(default=None, ge=0)


class QuotaCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quota_key: str = Field(min_length=1, max_length=120)
    display_name: str = Field(min_length=1, max_length=200)
    unit: str = Field(min_length=1, max_length=50)
    reset_period: str
    is_metered: bool = True


class QuotaUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    unit: str | None = Field(default=None, min_length=1, max_length=50)
    reset_period: str | None = None
    is_metered: bool | None = None


class FeatureCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature_key: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: str = Field(default="core", min_length=1, max_length=100)
    default_enabled: bool = False
    requires_human_governance: bool = False


class FeatureUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=100)
    default_enabled: bool | None = None
    requires_human_governance: bool | None = None


class EntitledFeatureItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature_definition_id: UUID
    is_enabled: bool = True


class PlanQuotaItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quota_definition_id: UUID
    hard_limit: Decimal | None = Field(default=None, ge=0)
    soft_limit: Decimal | None = Field(default=None, ge=0)
    overage_unit_price: Decimal = Field(default=Decimal("0"), ge=0)

    @model_validator(mode="after")
    def validate_limits(self) -> PlanQuotaItem:
        if self.hard_limit is not None and self.soft_limit is not None and self.soft_limit > self.hard_limit:
            raise ValueError("soft_limit must be less than or equal to hard_limit")
        return self


class FeatureEntitlementsReplaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[EntitledFeatureItem] = Field(default_factory=list, max_length=500)


class PlanQuotaLimitsReplaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PlanQuotaItem] = Field(default_factory=list, max_length=500)


class AddonCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    price: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    billing_interval: str = "monthly"


class AddonUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    billing_interval: str | None = None


class AddonQuotaDeltaItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quota_definition_id: UUID
    delta_value: Decimal

    @field_validator("delta_value")
    @classmethod
    def validate_non_zero(cls, value: Decimal) -> Decimal:
        if value == 0:
            raise ValueError("delta_value must be non-zero")
        return value


class AddonQuotaDeltasReplaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AddonQuotaDeltaItem] = Field(default_factory=list, max_length=500)


class FeatureFlagCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flag_key: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    default_enabled: bool = False
    rollout_percentage: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    kill_switch: bool = False


class FeatureFlagUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str | None = Field(default=None, min_length=1, max_length=500)
    default_enabled: bool | None = None
    rollout_percentage: Decimal | None = Field(default=None, ge=0, le=100)
    kill_switch: bool | None = None


class TenantFeatureFlagOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_enabled: bool
    reason: str | None = Field(default=None, max_length=1000)
    expires_at: datetime | None = None


class InfraPoolCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pool_key: str = Field(min_length=1, max_length=120)
    region: str
    isolation_tier: str = "shared"
    database_cluster_ref: str | None = Field(default=None, max_length=500)
    search_cluster_ref: str | None = Field(default=None, max_length=500)
    storage_bucket_prefix: str | None = Field(default=None, max_length=500)


class InfraPoolUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    database_cluster_ref: str | None = Field(default=None, max_length=500)
    search_cluster_ref: str | None = Field(default=None, max_length=500)
    storage_bucket_prefix: str | None = Field(default=None, max_length=500)


class PlatformUserCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=1, max_length=200)


class PlatformUserUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    mfa_required: bool | None = None


class RoleCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_key: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class RoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class RoleIdsReplaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_ids: list[UUID] = Field(default_factory=list, max_length=200)


class PermissionIdsReplaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    permission_ids: list[UUID] = Field(default_factory=list, max_length=500)


class SupportSessionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    reason: str = Field(min_length=1, max_length=1000)
    expires_at: datetime


class SupportTicketCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=4000)
    priority: str = "P3"


class SupportTicketUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, min_length=1, max_length=4000)
    priority: str | None = None
    status: str | None = None


class AssignTicketRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assigned_platform_user_id: UUID


class CloseTicketRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resolution_summary: str = Field(min_length=1, max_length=2000)


class SlaPolicyCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_key: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    severity: str
    response_minutes: int = Field(gt=0)
    resolution_minutes: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_resolution(self) -> SlaPolicyCreateRequest:
        if self.resolution_minutes < self.response_minutes:
            raise ValueError("resolution_minutes must be greater than or equal to response_minutes")
        return self


class SlaPolicyUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    severity: str | None = None
    response_minutes: int | None = Field(default=None, gt=0)
    resolution_minutes: int | None = Field(default=None, gt=0)


class ComplianceFrameworkCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    framework: str
    display_name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ComplianceFrameworkUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class RegionsReplaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    regions: list[str] = Field(default_factory=list, max_length=100)


class TenantFrameworksReplaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    framework_ids: list[UUID] = Field(default_factory=list, max_length=100)


class AiModelCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model_key: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=200)
    max_context_tokens: int | None = Field(default=None, gt=0)
    supports_embeddings: bool = False
    supports_audio: bool = False
    supports_video: bool = False
    is_active: bool = True


class AiModelUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    max_context_tokens: int | None = Field(default=None, gt=0)
    supports_embeddings: bool | None = None
    supports_audio: bool | None = None
    supports_video: bool | None = None
    is_active: bool | None = None


class ApiVersionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_label: str = Field(min_length=1, max_length=100)
    released_at: datetime
    deprecated_at: datetime | None = None
    sunset_at: datetime | None = None
    migration_guide_url: str | None = None


class ApiVersionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deprecated_at: datetime | None = None
    sunset_at: datetime | None = None
    migration_guide_url: str | None = None


class SloCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slo_key: str = Field(min_length=1, max_length=120)
    service_name: str = Field(min_length=1, max_length=200)
    objective_percent: Decimal = Field(ge=0, le=100)
    window_days: int = Field(gt=0)


class SloUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_name: str | None = Field(default=None, min_length=1, max_length=200)
    objective_percent: Decimal | None = Field(default=None, ge=0, le=100)
    window_days: int | None = Field(default=None, gt=0)
