# db/models/platform.py
from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .core import (
    Base,
    ConfidenceScoreDomain,
    CreatedAtMixin,
    CurrencyCodeDomain,
    LockVersionMixin,
    Percent0100Domain,
    PositiveMoneyDomain,
    SoftDeleteMixin,
    TimestampMixin,
    AbacEffectEnum,
    AiActionTypeEnum,
    AiAutonomyModeEnum,
    AiProviderEnum,
    AiSessionStatusEnum,
    ApplicationStatusEnum,
    ApprovalStatusEnum,
    ApproverResolutionEnum,
    AuditActorTypeEnum,
    BillingIntervalEnum,
    CallDirectionEnum,
    ClientStatusEnum,
    CompetencyLevelEnum,
    ComplianceFrameworkEnum,
    ConditionOperatorEnum,
    ConfigScopeEnum,
    ConfigValueTypeEnum,
    ConnectorAuthTypeEnum,
    ConnectorCategoryEnum,
    ConnectorStatusEnum,
    ConsentTypeEnum,
    ContractTypeEnum,
    DataTierEnum,
    DelegationStatusEnum,
    DsrStatusEnum,
    DsrTypeEnum,
    EmploymentTypeEnum,
    ExclusivityEnum,
    FeeStructureEnum,
    FieldRedactionEnum,
    GuaranteeStatusEnum,
    HeadcountTypeEnum,
    InterviewStatusEnum,
    InterviewTypeEnum,
    InvoiceStatusEnum,
    IsolationTierEnum,
    JobDescriptionStatusEnum,
    MandateStatusEnum,
    MfaMethodEnum,
    NotifCategoryEnum,
    NotifChannelEnum,
    NotifDeliveryStatusEnum,
    NotifRecipientTypeEnum,
    OfferStatusEnum,
    PaymentStatusEnum,
    PlanStatusEnum,
    PlatformUserStatusEnum,
    PostingStatusEnum,
    RegionEnum,
    ReportFormatEnum,
    RequisitionStatusEnum,
    ReviewItemStatusEnum,
    RolloutStrategyEnum,
    SecurityEventOutcomeEnum,
    SecurityEventSeverityEnum,
    SecurityEventTypeEnum,
    SlaSeverityEnum,
    SsoProviderEnum,
    SsoStatusEnum,
    StageDirectionEnum,
    SubmittalStatusEnum,
    SuppressionReasonEnum,
    SyncStatusEnum,
    SyncTypeEnum,
    TenantStatusEnum,
    TenantTypeEnum,
    TenantUserStatusEnum,
    TicketPriorityEnum,
    TicketStatusEnum,
    UsageSourceEnum,
    WfInstanceStatusEnum,
    WfStepTypeEnum,
    WfTemplateStatusEnum,
)



class PlatformAllowedJsonbColumns(Base):
    __tablename__ = "allowed_jsonb_columns"
    __table_args__ = {"schema": "platform"}

    schema_name: Mapped[str] = mapped_column(Text(), primary_key=True)
    table_name: Mapped[str] = mapped_column(Text(), primary_key=True)
    column_name: Mapped[str] = mapped_column(Text(), primary_key=True)
    allowed_reason: Mapped[str] = mapped_column(Text(), nullable=False)


class PlatformAllowedArrayColumns(Base):
    __tablename__ = "allowed_array_columns"
    __table_args__ = {"schema": "platform"}

    schema_name: Mapped[str] = mapped_column(Text(), primary_key=True)
    table_name: Mapped[str] = mapped_column(Text(), primary_key=True)
    column_name: Mapped[str] = mapped_column(Text(), primary_key=True)
    allowed_reason: Mapped[str] = mapped_column(Text(), nullable=False)


class PlatformPlans(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "plans"
    __table_args__ = (
        UniqueConstraint('code', name='uq_plans_code'),
        CheckConstraint('min_seats >= 1'),
        CheckConstraint('max_seats IS NULL OR max_seats >= min_seats'),
        CheckConstraint('trial_days >= 0'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    code: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(PlanStatusEnum, nullable=False, server_default=text("'draft'"))
    billing_interval: Mapped[str] = mapped_column(BillingIntervalEnum, nullable=False)
    base_price: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False, server_default=text('0'))
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False, server_default=text("'USD'"))
    min_seats: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('1'))
    max_seats: Mapped[int | None] = mapped_column(Integer())
    trial_days: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))


class PlatformQuotaDefinitions(TimestampMixin, Base):
    __tablename__ = "quota_definitions"
    __table_args__ = (
        UniqueConstraint('quota_key', name='uq_quota_definitions_quota_key'),
        CheckConstraint("reset_period IN ('none','daily','monthly','annual')"),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    quota_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    display_name: Mapped[str] = mapped_column(Text(), nullable=False)
    unit: Mapped[str] = mapped_column(Text(), nullable=False)
    reset_period: Mapped[str] = mapped_column(Text(), nullable=False)
    is_metered: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class PlatformPlanQuotaLimits(CreatedAtMixin, Base):
    __tablename__ = "plan_quota_limits"
    __table_args__ = (
        UniqueConstraint('plan_id', 'quota_definition_id', name='uq_plan_quota_limits_plan_quota'),
        ForeignKeyConstraint(['plan_id'], ['platform.plans.id'], name='fk_plan_quota_limits_plan'),
        ForeignKeyConstraint(['quota_definition_id'], ['platform.quota_definitions.id'], name='fk_plan_quota_limits_quota'),
        CheckConstraint('hard_limit IS NULL OR hard_limit >= 0'),
        CheckConstraint('soft_limit IS NULL OR soft_limit >= 0'),
        CheckConstraint('hard_limit IS NULL OR soft_limit IS NULL OR soft_limit <= hard_limit', name='chk_plan_quota_limits_soft_lte_hard'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    plan_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    quota_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    hard_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    soft_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    overage_unit_price: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False, server_default=text('0'))

    rel_fk_plan_quota_limits_plan: Mapped["PlatformPlans"] = relationship("PlatformPlans", viewonly=True, foreign_keys="[PlatformPlanQuotaLimits.plan_id]")
    rel_fk_plan_quota_limits_quota: Mapped["PlatformQuotaDefinitions"] = relationship("PlatformQuotaDefinitions", viewonly=True, foreign_keys="[PlatformPlanQuotaLimits.quota_definition_id]")


class PlatformFeatureDefinitions(TimestampMixin, Base):
    __tablename__ = "feature_definitions"
    __table_args__ = (
        UniqueConstraint('feature_key', name='uq_feature_definitions_feature_key'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    feature_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    category: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'core'"))
    default_enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    requires_human_governance: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))


class PlatformPlanFeatureEntitlements(CreatedAtMixin, Base):
    __tablename__ = "plan_feature_entitlements"
    __table_args__ = (
        UniqueConstraint('plan_id', 'feature_definition_id', name='uq_plan_feature_entitlements_plan_feature'),
        ForeignKeyConstraint(['plan_id'], ['platform.plans.id'], name='fk_plan_feature_entitlements_plan'),
        ForeignKeyConstraint(['feature_definition_id'], ['platform.feature_definitions.id'], name='fk_plan_feature_entitlements_feature'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    plan_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    feature_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_plan_feature_entitlements_plan: Mapped["PlatformPlans"] = relationship("PlatformPlans", viewonly=True, foreign_keys="[PlatformPlanFeatureEntitlements.plan_id]")
    rel_fk_plan_feature_entitlements_feature: Mapped["PlatformFeatureDefinitions"] = relationship("PlatformFeatureDefinitions", viewonly=True, foreign_keys="[PlatformPlanFeatureEntitlements.feature_definition_id]")


class PlatformPlanAddons(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "plan_addons"
    __table_args__ = (
        UniqueConstraint('code', name='uq_plan_addons_code'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    code: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(PlanStatusEnum, nullable=False, server_default=text("'draft'"))
    price: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False, server_default=text('0'))
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False, server_default=text("'USD'"))
    billing_interval: Mapped[str] = mapped_column(BillingIntervalEnum, nullable=False, server_default=text("'monthly'"))


class PlatformAddonQuotaDeltas(CreatedAtMixin, Base):
    __tablename__ = "addon_quota_deltas"
    __table_args__ = (
        UniqueConstraint('addon_id', 'quota_definition_id', name='uq_addon_quota_deltas_addon_quota'),
        ForeignKeyConstraint(['addon_id'], ['platform.plan_addons.id'], name='fk_addon_quota_deltas_addon'),
        ForeignKeyConstraint(['quota_definition_id'], ['platform.quota_definitions.id'], name='fk_addon_quota_deltas_quota'),
        CheckConstraint('delta_value <> 0'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    addon_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    quota_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    delta_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    rel_fk_addon_quota_deltas_addon: Mapped["PlatformPlanAddons"] = relationship("PlatformPlanAddons", viewonly=True, foreign_keys="[PlatformAddonQuotaDeltas.addon_id]")
    rel_fk_addon_quota_deltas_quota: Mapped["PlatformQuotaDefinitions"] = relationship("PlatformQuotaDefinitions", viewonly=True, foreign_keys="[PlatformAddonQuotaDeltas.quota_definition_id]")


class PlatformAddonFeatureEntitlements(CreatedAtMixin, Base):
    __tablename__ = "addon_feature_entitlements"
    __table_args__ = (
        UniqueConstraint('addon_id', 'feature_definition_id', name='uq_addon_feature_entitlements_addon_feature'),
        ForeignKeyConstraint(['addon_id'], ['platform.plan_addons.id'], name='fk_addon_feature_entitlements_addon'),
        ForeignKeyConstraint(['feature_definition_id'], ['platform.feature_definitions.id'], name='fk_addon_feature_entitlements_feature'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    addon_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    feature_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_addon_feature_entitlements_addon: Mapped["PlatformPlanAddons"] = relationship("PlatformPlanAddons", viewonly=True, foreign_keys="[PlatformAddonFeatureEntitlements.addon_id]")
    rel_fk_addon_feature_entitlements_feature: Mapped["PlatformFeatureDefinitions"] = relationship("PlatformFeatureDefinitions", viewonly=True, foreign_keys="[PlatformAddonFeatureEntitlements.feature_definition_id]")


class PlatformInfraPools(TimestampMixin, Base):
    __tablename__ = "infra_pools"
    __table_args__ = (
        UniqueConstraint('pool_key', name='uq_infra_pools_pool_key'),
        CheckConstraint("status IN ('active','draining','retired')"),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    pool_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    region: Mapped[str] = mapped_column(RegionEnum, nullable=False)
    isolation_tier: Mapped[str] = mapped_column(IsolationTierEnum, nullable=False, server_default=text("'shared'"))
    database_cluster_ref: Mapped[str | None] = mapped_column(Text())
    search_cluster_ref: Mapped[str | None] = mapped_column(Text())
    storage_bucket_prefix: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'active'"))


class PlatformTenants(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "tenants"
    __table_args__ = (
        UniqueConstraint('id', name='uq_tenants_id'),
        ForeignKeyConstraint(['plan_id'], ['platform.plans.id'], name='fk_tenants_plan'),
        ForeignKeyConstraint(['infra_pool_id'], ['platform.infra_pools.id'], name='fk_tenants_infra_pool'),
        CheckConstraint("status <> 'active' OR activated_at IS NOT NULL", name='chk_tenants_active_has_activated'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    legal_entity_name: Mapped[str | None] = mapped_column(Text())
    tenant_type: Mapped[str] = mapped_column(TenantTypeEnum, nullable=False)
    primary_admin_email: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    plan_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(TenantStatusEnum, nullable=False, server_default=text("'provisioning'"))
    isolation_tier: Mapped[str] = mapped_column(IsolationTierEnum, nullable=False, server_default=text("'shared'"))
    region: Mapped[str] = mapped_column(RegionEnum, nullable=False, server_default=text("'US'"))
    data_residency_zone: Mapped[str | None] = mapped_column(Text())
    infra_pool_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    churned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_tenants_plan: Mapped["PlatformPlans"] = relationship("PlatformPlans", viewonly=True, foreign_keys="[PlatformTenants.plan_id]")
    rel_fk_tenants_infra_pool: Mapped["PlatformInfraPools"] = relationship("PlatformInfraPools", viewonly=True, foreign_keys="[PlatformTenants.infra_pool_id]")


class PlatformTenantDomains(CreatedAtMixin, Base):
    __tablename__ = "tenant_domains"
    __table_args__ = (
        UniqueConstraint('domain', name='uq_tenant_domains_domain'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_tenant_domains_tenant'),
        CheckConstraint("verification_status IN ('pending','verified','failed','revoked')"),
        Index('uq_tenant_domains_one_primary', 'tenant_id', unique=True, postgresql_where=text('is_primary')),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    domain: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    verification_status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'pending'"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_tenant_domains_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[PlatformTenantDomains.tenant_id]")


class PlatformTenantLifecycleEvents(Base):
    __tablename__ = "tenant_lifecycle_events"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_tenant_lifecycle_events_tenant'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    event_key: Mapped[str] = mapped_column(Text(), nullable=False)
    from_status: Mapped[str | None] = mapped_column(TenantStatusEnum)
    to_status: Mapped[str | None] = mapped_column(TenantStatusEnum)
    actor_platform_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    reason: Mapped[str | None] = mapped_column(Text())

    rel_fk_tenant_lifecycle_events_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[PlatformTenantLifecycleEvents.tenant_id]")


class PlatformTenantProvisioningJobs(TimestampMixin, Base):
    __tablename__ = "tenant_provisioning_jobs"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'idempotency_key', name='uq_tenant_provisioning_jobs_idempotency'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_tenant_provisioning_jobs_tenant'),
        CheckConstraint('retry_count >= 0'),
        CheckConstraint('completed_at IS NULL OR failed_at IS NULL', name='chk_tenant_provisioning_jobs_finished_once'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False, server_default=text("'pending'"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(Text())
    error_message: Mapped[str | None] = mapped_column(Text())
    retry_count: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_tenant_provisioning_jobs_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[PlatformTenantProvisioningJobs.tenant_id]")


class PlatformTenantProvisioningSteps(TimestampMixin, Base):
    __tablename__ = "tenant_provisioning_steps"
    __table_args__ = (
        UniqueConstraint('provisioning_job_id', 'step_key', name='uq_tenant_provisioning_steps_job_step'),
        ForeignKeyConstraint(['provisioning_job_id'], ['platform.tenant_provisioning_jobs.id'], name='fk_tenant_provisioning_steps_job'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    provisioning_job_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    step_key: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False, server_default=text("'pending'"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text())

    rel_fk_tenant_provisioning_steps_job: Mapped["PlatformTenantProvisioningJobs"] = relationship("PlatformTenantProvisioningJobs", viewonly=True, foreign_keys="[PlatformTenantProvisioningSteps.provisioning_job_id]")


class PlatformPlatformPermissions(CreatedAtMixin, Base):
    __tablename__ = "platform_permissions"
    __table_args__ = (
        UniqueConstraint('permission_key', name='uq_platform_permissions_key'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    permission_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())


class PlatformPlatformRoles(TimestampMixin, Base):
    __tablename__ = "platform_roles"
    __table_args__ = (
        UniqueConstraint('role_key', name='uq_platform_roles_key'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    role_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())


class PlatformPlatformRolePermissions(CreatedAtMixin, Base):
    __tablename__ = "platform_role_permissions"
    __table_args__ = (
        ForeignKeyConstraint(['role_id'], ['platform.platform_roles.id'], name='fk_platform_role_permissions_role'),
        ForeignKeyConstraint(['permission_id'], ['platform.platform_permissions.id'], name='fk_platform_role_permissions_permission'),
        {"schema": "platform"},
    )

    role_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    rel_fk_platform_role_permissions_role: Mapped["PlatformPlatformRoles"] = relationship("PlatformPlatformRoles", viewonly=True, foreign_keys="[PlatformPlatformRolePermissions.role_id]")
    rel_fk_platform_role_permissions_permission: Mapped["PlatformPlatformPermissions"] = relationship("PlatformPlatformPermissions", viewonly=True, foreign_keys="[PlatformPlatformRolePermissions.permission_id]")


class PlatformPlatformUsers(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "platform_users"
    __table_args__ = (
        UniqueConstraint('email', name='uq_platform_users_email'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    email: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    display_name: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(PlatformUserStatusEnum, nullable=False, server_default=text("'invited'"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_hash: Mapped[str | None] = mapped_column(Text())
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mfa_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))


class PlatformPlatformUserSessions(CreatedAtMixin, Base):
    __tablename__ = "platform_user_sessions"
    __table_args__ = (
        UniqueConstraint('session_token_hash', name='uq_platform_user_sessions_token_hash'),
        ForeignKeyConstraint(['platform_user_id'], ['platform.platform_users.id'], name='fk_platform_user_sessions_user'),
        CheckConstraint('expires_at > created_at', name='chk_platform_user_sessions_expires_after_created'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    platform_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    session_token_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(postgresql.INET())
    user_agent: Mapped[str | None] = mapped_column(Text())
    mfa_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_platform_user_sessions_user: Mapped["PlatformPlatformUsers"] = relationship("PlatformPlatformUsers", viewonly=True, foreign_keys="[PlatformPlatformUserSessions.platform_user_id]")


class PlatformPlatformPasswordResetTokens(CreatedAtMixin, Base):
    __tablename__ = "platform_password_reset_tokens"
    __table_args__ = (
        UniqueConstraint('token_hmac', name='uq_platform_password_reset_tokens_hmac'),
        ForeignKeyConstraint(['platform_user_id'], ['platform.platform_users.id'], name='fk_platform_password_reset_tokens_user'),
        CheckConstraint("status IN ('pending','used','expired','revoked')"),
        CheckConstraint('expires_at > requested_at', name='chk_platform_password_reset_tokens_expires_after_requested'),
        Index('uq_platform_password_reset_tokens_one_active', 'platform_user_id', unique=True, postgresql_where=text("status = 'pending'")),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    platform_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    token_hmac: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'pending'"))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_platform_password_reset_tokens_user: Mapped["PlatformPlatformUsers"] = relationship("PlatformPlatformUsers", viewonly=True, foreign_keys="[PlatformPlatformPasswordResetTokens.platform_user_id]")


class PlatformPlatformEmailVerificationTokens(CreatedAtMixin, Base):
    __tablename__ = "platform_email_verification_tokens"
    __table_args__ = (
        UniqueConstraint('token_hmac', name='uq_platform_email_verification_tokens_hmac'),
        ForeignKeyConstraint(['platform_user_id'], ['platform.platform_users.id'], name='fk_platform_email_verification_tokens_user'),
        CheckConstraint("status IN ('pending','used','expired','revoked')"),
        CheckConstraint('expires_at > requested_at', name='chk_platform_email_verification_tokens_expires_after_requested'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    platform_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    token_hmac: Mapped[str] = mapped_column(Text(), nullable=False)
    email: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'pending'"))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_platform_email_verification_tokens_user: Mapped["PlatformPlatformUsers"] = relationship("PlatformPlatformUsers", viewonly=True, foreign_keys="[PlatformPlatformEmailVerificationTokens.platform_user_id]")


class PlatformPlatformUserMfaFactors(CreatedAtMixin, Base):
    __tablename__ = "platform_user_mfa_factors"
    __table_args__ = (
        ForeignKeyConstraint(['platform_user_id'], ['platform.platform_users.id'], name='fk_platform_user_mfa_factors_user'),
        Index('uq_platform_user_mfa_factors_primary', 'platform_user_id', unique=True, postgresql_where=text('is_primary AND disabled_at IS NULL')),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    platform_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    method: Mapped[str] = mapped_column(MfaMethodEnum, nullable=False)
    secret_ref: Mapped[str | None] = mapped_column(Text())
    phone_e164: Mapped[str | None] = mapped_column(Text())
    is_primary: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    enabled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_platform_user_mfa_factors_user: Mapped["PlatformPlatformUsers"] = relationship("PlatformPlatformUsers", viewonly=True, foreign_keys="[PlatformPlatformUserMfaFactors.platform_user_id]")


class PlatformPlatformUserRoles(CreatedAtMixin, Base):
    __tablename__ = "platform_user_roles"
    __table_args__ = (
        ForeignKeyConstraint(['platform_user_id'], ['platform.platform_users.id'], name='fk_platform_user_roles_user'),
        ForeignKeyConstraint(['role_id'], ['platform.platform_roles.id'], name='fk_platform_user_roles_role'),
        {"schema": "platform"},
    )

    platform_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    rel_fk_platform_user_roles_user: Mapped["PlatformPlatformUsers"] = relationship("PlatformPlatformUsers", viewonly=True, foreign_keys="[PlatformPlatformUserRoles.platform_user_id]")
    rel_fk_platform_user_roles_role: Mapped["PlatformPlatformRoles"] = relationship("PlatformPlatformRoles", viewonly=True, foreign_keys="[PlatformPlatformUserRoles.role_id]")


class PlatformSupportSessions(CreatedAtMixin, Base):
    __tablename__ = "support_sessions"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_support_sessions_tenant'),
        ForeignKeyConstraint(['platform_user_id'], ['platform.platform_users.id'], name='fk_support_sessions_platform_user'),
        CheckConstraint('expires_at > started_at', name='chk_support_sessions_time'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    platform_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    reason: Mapped[str] = mapped_column(Text(), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_support_sessions_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[PlatformSupportSessions.tenant_id]")
    rel_fk_support_sessions_platform_user: Mapped["PlatformPlatformUsers"] = relationship("PlatformPlatformUsers", viewonly=True, foreign_keys="[PlatformSupportSessions.platform_user_id]")


class PlatformAuditLogs(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_audit_logs_tenant'),
        {"schema": "platform", "postgresql_partition_by": "RANGE (occurred_at)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    actor_type: Mapped[str] = mapped_column(AuditActorTypeEnum, nullable=False)
    actor_tenant_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    actor_platform_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    action_key: Mapped[str] = mapped_column(Text(), nullable=False)
    object_schema: Mapped[str] = mapped_column(Text(), nullable=False)
    object_table: Mapped[str] = mapped_column(Text(), nullable=False)
    object_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    before_state: Mapped[dict[str, Any] | None] = mapped_column(postgresql.JSONB())
    after_state: Mapped[dict[str, Any] | None] = mapped_column(postgresql.JSONB())
    diff_state: Mapped[dict[str, Any] | None] = mapped_column(postgresql.JSONB())
    ip_address: Mapped[str | None] = mapped_column(postgresql.INET())
    user_agent: Mapped[str | None] = mapped_column(Text())
    request_id: Mapped[str | None] = mapped_column(Text())
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, server_default=text('now()'))

    rel_fk_audit_logs_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[PlatformAuditLogs.tenant_id]")


class PlatformSupportTickets(TimestampMixin, Base):
    __tablename__ = "support_tickets"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_support_tickets_tenant'),
        ForeignKeyConstraint(['assigned_platform_user_id'], ['platform.platform_users.id'], name='fk_support_tickets_assigned_user'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    requester_email: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    subject: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    priority: Mapped[str] = mapped_column(TicketPriorityEnum, nullable=False, server_default=text("'P3'"))
    status: Mapped[str] = mapped_column(TicketStatusEnum, nullable=False, server_default=text("'open'"))
    assigned_platform_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_support_tickets_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[PlatformSupportTickets.tenant_id]")
    rel_fk_support_tickets_assigned_user: Mapped["PlatformPlatformUsers"] = relationship("PlatformPlatformUsers", viewonly=True, foreign_keys="[PlatformSupportTickets.assigned_platform_user_id]")


class PlatformSlaPolicies(TimestampMixin, Base):
    __tablename__ = "sla_policies"
    __table_args__ = (
        UniqueConstraint('policy_key', name='uq_sla_policies_key'),
        CheckConstraint('response_minutes > 0'),
        CheckConstraint('resolution_minutes >= response_minutes'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    policy_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    severity: Mapped[str] = mapped_column(SlaSeverityEnum, nullable=False)
    response_minutes: Mapped[int] = mapped_column(Integer(), nullable=False)
    resolution_minutes: Mapped[int] = mapped_column(Integer(), nullable=False)


class PlatformComplianceFrameworks(CreatedAtMixin, Base):
    __tablename__ = "compliance_frameworks"
    __table_args__ = (
        UniqueConstraint('framework', name='uq_compliance_frameworks_framework'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    framework: Mapped[str] = mapped_column(ComplianceFrameworkEnum, nullable=False)
    display_name: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())


class PlatformComplianceFrameworkRegions(Base):
    __tablename__ = "compliance_framework_regions"
    __table_args__ = (
        ForeignKeyConstraint(['framework_id'], ['platform.compliance_frameworks.id'], name='fk_compliance_framework_regions_framework'),
        {"schema": "platform"},
    )

    framework_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    region: Mapped[str] = mapped_column(RegionEnum, primary_key=True)

    rel_fk_compliance_framework_regions_framework: Mapped["PlatformComplianceFrameworks"] = relationship("PlatformComplianceFrameworks", viewonly=True, foreign_keys="[PlatformComplianceFrameworkRegions.framework_id]")


class PlatformTenantComplianceFrameworks(CreatedAtMixin, Base):
    __tablename__ = "tenant_compliance_frameworks"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'framework_id', 'disabled_at', name='uq_tenant_compliance_frameworks_active'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_tenant_compliance_frameworks_tenant'),
        ForeignKeyConstraint(['framework_id'], ['platform.compliance_frameworks.id'], name='fk_tenant_compliance_frameworks_framework'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    framework_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    enabled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_tenant_compliance_frameworks_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[PlatformTenantComplianceFrameworks.tenant_id]")
    rel_fk_tenant_compliance_frameworks_framework: Mapped["PlatformComplianceFrameworks"] = relationship("PlatformComplianceFrameworks", viewonly=True, foreign_keys="[PlatformTenantComplianceFrameworks.framework_id]")


class PlatformAiModelDefinitions(TimestampMixin, Base):
    __tablename__ = "ai_model_definitions"
    __table_args__ = (
        UniqueConstraint('provider', 'model_key', name='uq_ai_model_definitions_provider_model'),
        CheckConstraint('max_context_tokens IS NULL OR max_context_tokens > 0'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    provider: Mapped[str] = mapped_column(AiProviderEnum, nullable=False)
    model_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    display_name: Mapped[str] = mapped_column(Text(), nullable=False)
    max_context_tokens: Mapped[int | None] = mapped_column(Integer())
    supports_embeddings: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    supports_audio: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    supports_video: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class PlatformAiModelRegionRestrictions(Base):
    __tablename__ = "ai_model_region_restrictions"
    __table_args__ = (
        ForeignKeyConstraint(['model_definition_id'], ['platform.ai_model_definitions.id'], name='fk_ai_model_region_restrictions_model'),
        {"schema": "platform"},
    )

    model_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    region: Mapped[str] = mapped_column(RegionEnum, primary_key=True)
    restriction_reason: Mapped[str | None] = mapped_column(Text())

    rel_fk_ai_model_region_restrictions_model: Mapped["PlatformAiModelDefinitions"] = relationship("PlatformAiModelDefinitions", viewonly=True, foreign_keys="[PlatformAiModelRegionRestrictions.model_definition_id]")


class PlatformFeatureFlagRegistry(TimestampMixin, Base):
    __tablename__ = "feature_flag_registry"
    __table_args__ = (
        UniqueConstraint('flag_key', name='uq_feature_flag_registry_key'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    flag_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    default_enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    rollout_percentage: Mapped[Decimal] = mapped_column(Percent0100Domain, nullable=False, server_default=text('0'))
    kill_switch: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))


class PlatformFeatureFlagTenantOverrides(CreatedAtMixin, Base):
    __tablename__ = "feature_flag_tenant_overrides"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'feature_flag_id', 'expires_at', name='uq_feature_flag_tenant_overrides_active'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_feature_flag_tenant_overrides_tenant'),
        ForeignKeyConstraint(['feature_flag_id'], ['platform.feature_flag_registry.id'], name='fk_feature_flag_tenant_overrides_flag'),
        ForeignKeyConstraint(['created_by_platform_user_id'], ['platform.platform_users.id'], name='fk_feature_flag_tenant_overrides_created_by'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    feature_flag_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text())
    created_by_platform_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_feature_flag_tenant_overrides_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[PlatformFeatureFlagTenantOverrides.tenant_id]")
    rel_fk_feature_flag_tenant_overrides_flag: Mapped["PlatformFeatureFlagRegistry"] = relationship("PlatformFeatureFlagRegistry", viewonly=True, foreign_keys="[PlatformFeatureFlagTenantOverrides.feature_flag_id]")
    rel_fk_feature_flag_tenant_overrides_created_by: Mapped["PlatformPlatformUsers"] = relationship("PlatformPlatformUsers", viewonly=True, foreign_keys="[PlatformFeatureFlagTenantOverrides.created_by_platform_user_id]")


class PlatformApiVersions(CreatedAtMixin, Base):
    __tablename__ = "api_versions"
    __table_args__ = (
        UniqueConstraint('version_label', name='uq_api_versions_label'),
        CheckConstraint('sunset_at IS NULL OR deprecated_at IS NOT NULL AND sunset_at > deprecated_at', name='chk_api_versions_sunset_after_deprecation'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    version_label: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    released_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sunset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    migration_guide_url: Mapped[str | None] = mapped_column(Text())


class PlatformDeployments(Base):
    __tablename__ = "deployments"
    __table_args__ = (
        ForeignKeyConstraint(['rollback_of_deployment_id'], ['platform.deployments.id'], name='fk_deployments_rollback'),
        CheckConstraint("environment IN ('dev','qa','staging','production')"),
        CheckConstraint("status IN ('running','succeeded','failed','rolled_back')"),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    environment: Mapped[str] = mapped_column(Text(), nullable=False)
    version_label: Mapped[str] = mapped_column(Text(), nullable=False)
    rollout_strategy: Mapped[str] = mapped_column(RolloutStrategyEnum, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rollback_of_deployment_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'running'"))

    rel_fk_deployments_rollback: Mapped["PlatformDeployments"] = relationship("PlatformDeployments", viewonly=True, foreign_keys="[PlatformDeployments.rollback_of_deployment_id]")


class PlatformSloDefinitions(TimestampMixin, Base):
    __tablename__ = "slo_definitions"
    __table_args__ = (
        UniqueConstraint('slo_key', name='uq_slo_definitions_key'),
        CheckConstraint('window_days > 0'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    slo_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    service_name: Mapped[str] = mapped_column(Text(), nullable=False)
    objective_percent: Mapped[Decimal] = mapped_column(Percent0100Domain, nullable=False)
    window_days: Mapped[int] = mapped_column(Integer(), nullable=False)


class PlatformErrorBudgetStatus(CreatedAtMixin, Base):
    __tablename__ = "error_budget_status"
    __table_args__ = (
        UniqueConstraint('slo_definition_id', 'period_start', 'period_end', name='uq_error_budget_status_slo_period'),
        ForeignKeyConstraint(['slo_definition_id'], ['platform.slo_definitions.id'], name='fk_error_budget_status_slo'),
        CheckConstraint('burn_rate >= 0'),
        CheckConstraint('period_end >= period_start', name='chk_error_budget_status_period'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    slo_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    consumed_percent: Mapped[Decimal] = mapped_column(Percent0100Domain, nullable=False, server_default=text('0'))
    burn_rate: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, server_default=text('0'))

    rel_fk_error_budget_status_slo: Mapped["PlatformSloDefinitions"] = relationship("PlatformSloDefinitions", viewonly=True, foreign_keys="[PlatformErrorBudgetStatus.slo_definition_id]")


class PlatformAiQualityMetrics(CreatedAtMixin, Base):
    __tablename__ = "ai_quality_metrics"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_ai_quality_metrics_tenant'),
        ForeignKeyConstraint(['model_definition_id'], ['platform.ai_model_definitions.id'], name='fk_ai_quality_metrics_model'),
        CheckConstraint('sample_count >= 0'),
        CheckConstraint('sample_period_end >= sample_period_start', name='chk_ai_quality_metrics_period'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    action_type: Mapped[str] = mapped_column(AiActionTypeEnum, nullable=False)
    model_definition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    sample_period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    sample_period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer(), nullable=False)
    human_override_rate: Mapped[Decimal | None] = mapped_column(Percent0100Domain)
    bias_flag_rate: Mapped[Decimal | None] = mapped_column(Percent0100Domain)
    avg_confidence: Mapped[Decimal | None] = mapped_column(ConfidenceScoreDomain)

    rel_fk_ai_quality_metrics_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[PlatformAiQualityMetrics.tenant_id]")
    rel_fk_ai_quality_metrics_model: Mapped["PlatformAiModelDefinitions"] = relationship("PlatformAiModelDefinitions", viewonly=True, foreign_keys="[PlatformAiQualityMetrics.model_definition_id]")


class PlatformAiGovernanceAlerts(CreatedAtMixin, Base):
    __tablename__ = "ai_governance_alerts"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_ai_governance_alerts_tenant'),
        CheckConstraint("status IN ('open','acknowledged','resolved','dismissed')"),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    action_type: Mapped[str] = mapped_column(AiActionTypeEnum, nullable=False)
    severity: Mapped[str] = mapped_column(SlaSeverityEnum, nullable=False)
    alert_key: Mapped[str] = mapped_column(Text(), nullable=False)
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'open'"))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_ai_governance_alerts_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[PlatformAiGovernanceAlerts.tenant_id]")


class PlatformAiGovernanceAlertEvidence(CreatedAtMixin, Base):
    __tablename__ = "ai_governance_alert_evidence"
    __table_args__ = (
        ForeignKeyConstraint(['alert_id'], ['platform.ai_governance_alerts.id'], name='fk_ai_governance_alert_evidence_alert'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    alert_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    evidence_schema: Mapped[str] = mapped_column(Text(), nullable=False)
    evidence_table: Mapped[str] = mapped_column(Text(), nullable=False)
    evidence_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())

    rel_fk_ai_governance_alert_evidence_alert: Mapped["PlatformAiGovernanceAlerts"] = relationship("PlatformAiGovernanceAlerts", viewonly=True, foreign_keys="[PlatformAiGovernanceAlertEvidence.alert_id]")


class PlatformBenchmarkCohorts(CreatedAtMixin, Base):
    __tablename__ = "benchmark_cohorts"
    __table_args__ = (
        UniqueConstraint('cohort_key', name='uq_benchmark_cohorts_key'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    cohort_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    region: Mapped[str | None] = mapped_column(RegionEnum)
    tenant_type: Mapped[str | None] = mapped_column(TenantTypeEnum)


class PlatformBenchmarkMetrics(CreatedAtMixin, Base):
    __tablename__ = "benchmark_metrics"
    __table_args__ = (
        UniqueConstraint('cohort_id', 'metric_key', 'period_start', 'period_end', name='uq_benchmark_metrics_cohort_metric_period'),
        ForeignKeyConstraint(['cohort_id'], ['platform.benchmark_cohorts.id'], name='fk_benchmark_metrics_cohort'),
        CheckConstraint('sample_size >= 0'),
        CheckConstraint('period_end >= period_start', name='chk_benchmark_metrics_period'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    cohort_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    metric_key: Mapped[str] = mapped_column(Text(), nullable=False)
    period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer(), nullable=False)

    rel_fk_benchmark_metrics_cohort: Mapped["PlatformBenchmarkCohorts"] = relationship("PlatformBenchmarkCohorts", viewonly=True, foreign_keys="[PlatformBenchmarkMetrics.cohort_id]")

