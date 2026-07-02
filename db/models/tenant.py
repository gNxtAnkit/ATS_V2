# db/models/tenant.py
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



class TenantBusinessUnits(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "business_units"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_business_units_tenant_id'),
        UniqueConstraint('tenant_id', 'code', name='uq_business_units_tenant_code'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_business_units_tenant'),
        ForeignKeyConstraint(['tenant_id', 'parent_business_unit_id'], ['tenant.business_units.tenant_id', 'tenant.business_units.id'], name='fk_business_units_parent'),
        CheckConstraint("status IN ('active','inactive','archived')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    parent_business_unit_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    code: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    cost_center: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'active'"))

    rel_fk_business_units_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantBusinessUnits.tenant_id]")
    rel_fk_business_units_parent: Mapped["TenantBusinessUnits"] = relationship("TenantBusinessUnits", viewonly=True, foreign_keys="[TenantBusinessUnits.tenant_id, TenantBusinessUnits.parent_business_unit_id]")


class TenantUsers(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_users_tenant_id'),
        UniqueConstraint('tenant_id', 'email', name='uq_users_tenant_email'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_users_tenant'),
        ForeignKeyConstraint(['tenant_id', 'business_unit_id'], ['tenant.business_units.tenant_id', 'tenant.business_units.id'], name='fk_users_business_unit'),
        CheckConstraint("provisioning_source IN ('manual','sso_jit','scim','api')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    business_unit_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    email: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    display_name: Mapped[str] = mapped_column(Text(), nullable=False)
    given_name: Mapped[str | None] = mapped_column(Text())
    family_name: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(TenantUserStatusEnum, nullable=False, server_default=text("'invited'"))
    provisioning_source: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'manual'"))
    is_tenant_admin: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    password_hash: Mapped[str | None] = mapped_column(Text())
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_users_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantUsers.tenant_id]")
    rel_fk_users_business_unit: Mapped["TenantBusinessUnits"] = relationship("TenantBusinessUnits", viewonly=True, foreign_keys="[TenantUsers.tenant_id, TenantUsers.business_unit_id]")


class TenantUserMfaFactors(CreatedAtMixin, Base):
    __tablename__ = "user_mfa_factors"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_user_mfa_factors_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_user_mfa_factors_user'),
        Index('uq_user_mfa_factors_primary', 'tenant_id', 'user_id', unique=True, postgresql_where=text('is_primary AND disabled_at IS NULL')),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    method: Mapped[str] = mapped_column(MfaMethodEnum, nullable=False)
    secret_ref: Mapped[str | None] = mapped_column(Text())
    phone_e164: Mapped[str | None] = mapped_column(Text())
    is_primary: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    enabled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_user_mfa_factors_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantUserMfaFactors.tenant_id, TenantUserMfaFactors.user_id]")


class TenantUserSessions(CreatedAtMixin, Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_user_sessions_tenant_id'),
        UniqueConstraint('session_token_hash', name='uq_user_sessions_token_hash'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_user_sessions_user'),
        CheckConstraint('expires_at > created_at', name='chk_user_sessions_expires_after_created'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    session_token_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(postgresql.INET())
    user_agent: Mapped[str | None] = mapped_column(Text())
    mfa_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_user_sessions_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantUserSessions.tenant_id, TenantUserSessions.user_id]")


class TenantPasswordResetTokens(CreatedAtMixin, Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_password_reset_tokens_tenant_id'),
        UniqueConstraint('tenant_id', 'token_hmac', name='uq_password_reset_tokens_hmac'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_password_reset_tokens_user'),
        CheckConstraint("status IN ('pending','used','expired','revoked')"),
        CheckConstraint('expires_at > requested_at', name='chk_password_reset_tokens_expires_after_requested'),
        Index('uq_password_reset_tokens_one_active', 'tenant_id', 'user_id', unique=True, postgresql_where=text("status = 'pending'")),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    token_hmac: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'pending'"))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_password_reset_tokens_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantPasswordResetTokens.tenant_id, TenantPasswordResetTokens.user_id]")


class TenantEmailVerificationTokens(CreatedAtMixin, Base):
    __tablename__ = "email_verification_tokens"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_email_verification_tokens_tenant_id'),
        UniqueConstraint('tenant_id', 'token_hmac', name='uq_email_verification_tokens_hmac'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_email_verification_tokens_user'),
        CheckConstraint("status IN ('pending','used','expired','revoked')"),
        CheckConstraint('expires_at > requested_at', name='chk_email_verification_tokens_expires_after_requested'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    token_hmac: Mapped[str] = mapped_column(Text(), nullable=False)
    email: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'pending'"))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_email_verification_tokens_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantEmailVerificationTokens.tenant_id, TenantEmailVerificationTokens.user_id]")


class TenantRoles(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_roles_tenant_id'),
        UniqueConstraint('tenant_id', 'role_key', name='uq_roles_tenant_key'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_roles_tenant'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    role_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    is_system_role: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_roles_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantRoles.tenant_id]")


class TenantPermissions(CreatedAtMixin, Base):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_permissions_tenant_id'),
        UniqueConstraint('tenant_id', 'permission_key', name='uq_permissions_tenant_key'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_permissions_tenant'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    permission_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    resource_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    action_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())

    rel_fk_permissions_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantPermissions.tenant_id]")


class TenantPermissionConditionGroups(CreatedAtMixin, Base):
    __tablename__ = "permission_condition_groups"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_permission_condition_groups_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'permission_id'], ['tenant.permissions.tenant_id', 'tenant.permissions.id'], name='fk_permission_condition_groups_permission'),
        CheckConstraint("group_operator IN ('AND','OR')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    permission_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    group_operator: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'AND'"))
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_permission_condition_groups_permission: Mapped["TenantPermissions"] = relationship("TenantPermissions", viewonly=True, foreign_keys="[TenantPermissionConditionGroups.tenant_id, TenantPermissionConditionGroups.permission_id]")


class TenantPermissionConditions(CreatedAtMixin, Base):
    __tablename__ = "permission_conditions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_permission_conditions_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'condition_group_id'], ['tenant.permission_condition_groups.tenant_id', 'tenant.permission_condition_groups.id'], name='fk_permission_conditions_group'),
        CheckConstraint('(CASE WHEN value_text IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN value_number IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN value_bool IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN value_date IS NULL THEN 0 ELSE 1 END) <= 1', name='chk_permission_conditions_one_value'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    condition_group_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    attribute_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    operator: Mapped[str] = mapped_column(ConditionOperatorEnum, nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text())
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    value_bool: Mapped[bool | None] = mapped_column(Boolean())
    value_date: Mapped[date | None] = mapped_column(Date())
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_permission_conditions_group: Mapped["TenantPermissionConditionGroups"] = relationship("TenantPermissionConditionGroups", viewonly=True, foreign_keys="[TenantPermissionConditions.tenant_id, TenantPermissionConditions.condition_group_id]")


class TenantRolePermissions(CreatedAtMixin, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'role_id'], ['tenant.roles.tenant_id', 'tenant.roles.id'], name='fk_role_permissions_role'),
        ForeignKeyConstraint(['tenant_id', 'permission_id'], ['tenant.permissions.tenant_id', 'tenant.permissions.id'], name='fk_role_permissions_permission'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    rel_fk_role_permissions_role: Mapped["TenantRoles"] = relationship("TenantRoles", viewonly=True, foreign_keys="[TenantRolePermissions.tenant_id, TenantRolePermissions.role_id]")
    rel_fk_role_permissions_permission: Mapped["TenantPermissions"] = relationship("TenantPermissions", viewonly=True, foreign_keys="[TenantRolePermissions.tenant_id, TenantRolePermissions.permission_id]")


class TenantUserRoleAssignments(CreatedAtMixin, Base):
    __tablename__ = "user_role_assignments"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_user_role_assignments_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_user_role_assignments_user'),
        ForeignKeyConstraint(['tenant_id', 'role_id'], ['tenant.roles.tenant_id', 'tenant.roles.id'], name='fk_user_role_assignments_role'),
        ForeignKeyConstraint(['tenant_id', 'business_unit_id'], ['tenant.business_units.tenant_id', 'tenant.business_units.id'], name='fk_user_role_assignments_business_unit'),
        ForeignKeyConstraint(['tenant_id', 'assigned_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_user_role_assignments_assigned_by'),
        CheckConstraint('ends_at IS NULL OR ends_at > starts_at', name='chk_user_role_assignments_dates'),
        Index('uq_user_role_assignments_active', 'tenant_id', 'user_id', 'role_id', text("COALESCE(business_unit_id, '00000000-0000-0000-0000-000000000000'::uuid)"), unique=True, postgresql_where=text('ends_at IS NULL')),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    business_unit_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_user_role_assignments_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantUserRoleAssignments.tenant_id, TenantUserRoleAssignments.user_id]")
    rel_fk_user_role_assignments_role: Mapped["TenantRoles"] = relationship("TenantRoles", viewonly=True, foreign_keys="[TenantUserRoleAssignments.tenant_id, TenantUserRoleAssignments.role_id]")
    rel_fk_user_role_assignments_business_unit: Mapped["TenantBusinessUnits"] = relationship("TenantBusinessUnits", viewonly=True, foreign_keys="[TenantUserRoleAssignments.tenant_id, TenantUserRoleAssignments.business_unit_id]")
    rel_fk_user_role_assignments_assigned_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantUserRoleAssignments.tenant_id, TenantUserRoleAssignments.assigned_by_user_id]")


class TenantAbacPolicies(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "abac_policies"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_abac_policies_tenant_id'),
        UniqueConstraint('tenant_id', 'policy_key', name='uq_abac_policies_tenant_key'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_abac_policies_tenant'),
        CheckConstraint('priority >= 0'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    policy_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    effect: Mapped[str] = mapped_column(AbacEffectEnum, nullable=False)
    resource_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    action_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    priority: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('100'))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_abac_policies_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantAbacPolicies.tenant_id]")


class TenantAbacPolicyConditionGroups(CreatedAtMixin, Base):
    __tablename__ = "abac_policy_condition_groups"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_abac_policy_condition_groups_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'policy_id'], ['tenant.abac_policies.tenant_id', 'tenant.abac_policies.id'], name='fk_abac_policy_condition_groups_policy'),
        ForeignKeyConstraint(['tenant_id', 'parent_group_id'], ['tenant.abac_policy_condition_groups.tenant_id', 'tenant.abac_policy_condition_groups.id'], name='fk_abac_policy_condition_groups_parent'),
        CheckConstraint("group_operator IN ('AND','OR')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    policy_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    parent_group_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    group_operator: Mapped[str] = mapped_column(Text(), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_abac_policy_condition_groups_policy: Mapped["TenantAbacPolicies"] = relationship("TenantAbacPolicies", viewonly=True, foreign_keys="[TenantAbacPolicyConditionGroups.tenant_id, TenantAbacPolicyConditionGroups.policy_id]")
    rel_fk_abac_policy_condition_groups_parent: Mapped["TenantAbacPolicyConditionGroups"] = relationship("TenantAbacPolicyConditionGroups", viewonly=True, foreign_keys="[TenantAbacPolicyConditionGroups.tenant_id, TenantAbacPolicyConditionGroups.parent_group_id]")


class TenantAbacPolicyConditions(CreatedAtMixin, Base):
    __tablename__ = "abac_policy_conditions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_abac_policy_conditions_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'condition_group_id'], ['tenant.abac_policy_condition_groups.tenant_id', 'tenant.abac_policy_condition_groups.id'], name='fk_abac_policy_conditions_group'),
        CheckConstraint('(CASE WHEN value_text IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN value_number IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN value_bool IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN value_date IS NULL THEN 0 ELSE 1 END) <= 1', name='chk_abac_policy_conditions_one_value'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    condition_group_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    attribute_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    operator: Mapped[str] = mapped_column(ConditionOperatorEnum, nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text())
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    value_bool: Mapped[bool | None] = mapped_column(Boolean())
    value_date: Mapped[date | None] = mapped_column(Date())

    rel_fk_abac_policy_conditions_group: Mapped["TenantAbacPolicyConditionGroups"] = relationship("TenantAbacPolicyConditionGroups", viewonly=True, foreign_keys="[TenantAbacPolicyConditions.tenant_id, TenantAbacPolicyConditions.condition_group_id]")


class TenantFieldPermissions(TimestampMixin, Base):
    __tablename__ = "field_permissions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_field_permissions_tenant_id'),
        UniqueConstraint('tenant_id', 'resource_key', 'field_key', name='uq_field_permissions_resource_field'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_field_permissions_tenant'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    resource_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    field_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    redaction: Mapped[str] = mapped_column(FieldRedactionEnum, nullable=False)

    rel_fk_field_permissions_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantFieldPermissions.tenant_id]")


class TenantFieldPermissionRoles(CreatedAtMixin, Base):
    __tablename__ = "field_permission_roles"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'field_permission_id'], ['tenant.field_permissions.tenant_id', 'tenant.field_permissions.id'], name='fk_field_permission_roles_field_permission'),
        ForeignKeyConstraint(['tenant_id', 'role_id'], ['tenant.roles.tenant_id', 'tenant.roles.id'], name='fk_field_permission_roles_role'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    field_permission_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    rel_fk_field_permission_roles_field_permission: Mapped["TenantFieldPermissions"] = relationship("TenantFieldPermissions", viewonly=True, foreign_keys="[TenantFieldPermissionRoles.tenant_id, TenantFieldPermissionRoles.field_permission_id]")
    rel_fk_field_permission_roles_role: Mapped["TenantRoles"] = relationship("TenantRoles", viewonly=True, foreign_keys="[TenantFieldPermissionRoles.tenant_id, TenantFieldPermissionRoles.role_id]")


class TenantDelegations(TimestampMixin, Base):
    __tablename__ = "delegations"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_delegations_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'delegator_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_delegations_delegator'),
        ForeignKeyConstraint(['tenant_id', 'delegate_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_delegations_delegate'),
        ForeignKeyConstraint(['tenant_id', 'role_id'], ['tenant.roles.tenant_id', 'tenant.roles.id'], name='fk_delegations_role'),
        CheckConstraint('ends_at > starts_at', name='chk_delegations_dates'),
        CheckConstraint('delegator_user_id <> delegate_user_id', name='chk_delegations_not_self'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    delegator_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    delegate_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    role_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(DelegationStatusEnum, nullable=False, server_default=text("'active'"))
    reason: Mapped[str] = mapped_column(Text(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_delegations_delegator: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantDelegations.tenant_id, TenantDelegations.delegator_user_id]")
    rel_fk_delegations_delegate: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantDelegations.tenant_id, TenantDelegations.delegate_user_id]")
    rel_fk_delegations_role: Mapped["TenantRoles"] = relationship("TenantRoles", viewonly=True, foreign_keys="[TenantDelegations.tenant_id, TenantDelegations.role_id]")


class TenantSsoConfigs(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "sso_configs"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_sso_configs_tenant_id'),
        UniqueConstraint('tenant_id', 'provider', name='uq_sso_configs_tenant_provider'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_sso_configs_tenant'),
        CheckConstraint("enforcement_mode IN ('optional','required_for_admins','required_for_all')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    provider: Mapped[str] = mapped_column(SsoProviderEnum, nullable=False)
    status: Mapped[str] = mapped_column(SsoStatusEnum, nullable=False, server_default=text("'disabled'"))
    issuer_url: Mapped[str | None] = mapped_column(Text())
    client_id: Mapped[str | None] = mapped_column(Text())
    metadata_url: Mapped[str | None] = mapped_column(Text())
    enforcement_mode: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'optional'"))
    jit_provisioning_enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_sso_configs_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantSsoConfigs.tenant_id]")


class TenantSsoAttributeMappings(CreatedAtMixin, Base):
    __tablename__ = "sso_attribute_mappings"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_sso_attribute_mappings_tenant_id'),
        UniqueConstraint('tenant_id', 'sso_config_id', 'platform_attribute', name='uq_sso_attribute_mappings_config_attr'),
        ForeignKeyConstraint(['tenant_id', 'sso_config_id'], ['tenant.sso_configs.tenant_id', 'tenant.sso_configs.id'], name='fk_sso_attribute_mappings_config'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    sso_config_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    platform_attribute: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    provider_claim: Mapped[str] = mapped_column(Text(), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_sso_attribute_mappings_config: Mapped["TenantSsoConfigs"] = relationship("TenantSsoConfigs", viewonly=True, foreign_keys="[TenantSsoAttributeMappings.tenant_id, TenantSsoAttributeMappings.sso_config_id]")


class TenantSsoGroupRoleMappings(CreatedAtMixin, Base):
    __tablename__ = "sso_group_role_mappings"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_sso_group_role_mappings_tenant_id'),
        UniqueConstraint('tenant_id', 'sso_config_id', 'provider_group', name='uq_sso_group_role_mappings_config_group'),
        ForeignKeyConstraint(['tenant_id', 'sso_config_id'], ['tenant.sso_configs.tenant_id', 'tenant.sso_configs.id'], name='fk_sso_group_role_mappings_config'),
        ForeignKeyConstraint(['tenant_id', 'role_id'], ['tenant.roles.tenant_id', 'tenant.roles.id'], name='fk_sso_group_role_mappings_role'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    sso_config_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    provider_group: Mapped[str] = mapped_column(Text(), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)

    rel_fk_sso_group_role_mappings_config: Mapped["TenantSsoConfigs"] = relationship("TenantSsoConfigs", viewonly=True, foreign_keys="[TenantSsoGroupRoleMappings.tenant_id, TenantSsoGroupRoleMappings.sso_config_id]")
    rel_fk_sso_group_role_mappings_role: Mapped["TenantRoles"] = relationship("TenantRoles", viewonly=True, foreign_keys="[TenantSsoGroupRoleMappings.tenant_id, TenantSsoGroupRoleMappings.role_id]")


class TenantSecurityEvents(Base):
    __tablename__ = "security_events"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', 'occurred_at', name='uq_security_events_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_security_events_tenant'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_security_events_user'),
        {"schema": "tenant", "postgresql_partition_by": "RANGE (occurred_at)"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(SecurityEventTypeEnum, nullable=False)
    outcome: Mapped[str] = mapped_column(SecurityEventOutcomeEnum, nullable=False)
    severity: Mapped[str] = mapped_column(SecurityEventSeverityEnum, nullable=False, server_default=text("'info'"))
    ip_address: Mapped[str | None] = mapped_column(postgresql.INET())
    user_agent: Mapped[str | None] = mapped_column(Text())
    request_id: Mapped[str | None] = mapped_column(Text())
    provider_event_id: Mapped[str | None] = mapped_column(Text())
    raw_event_snapshot: Mapped[dict[str, Any] | None] = mapped_column(postgresql.JSONB())
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, server_default=text('now()'))

    rel_fk_security_events_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantSecurityEvents.tenant_id]")
    rel_fk_security_events_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantSecurityEvents.tenant_id, TenantSecurityEvents.user_id]")


class TenantTenantBranding(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "tenant_branding"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_tenant_branding_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_tenant_branding_tenant'),
        CheckConstraint("primary_color IS NULL OR primary_color ~ '^#[0-9A-Fa-f]{6}$'"),
        CheckConstraint("secondary_color IS NULL OR secondary_color ~ '^#[0-9A-Fa-f]{6}$'"),
        Index('uq_tenant_branding_default', 'tenant_id', unique=True, postgresql_where=text('is_default AND deleted_at IS NULL')),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    brand_name: Mapped[str] = mapped_column(Text(), nullable=False)
    primary_color: Mapped[str | None] = mapped_column(Text())
    secondary_color: Mapped[str | None] = mapped_column(Text())
    logo_asset_ref: Mapped[str | None] = mapped_column(Text())
    favicon_asset_ref: Mapped[str | None] = mapped_column(Text())
    default_locale: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'en'"))
    is_default: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_tenant_branding_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantTenantBranding.tenant_id]")


class TenantWhiteLabelDomains(TimestampMixin, Base):
    __tablename__ = "white_label_domains"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_white_label_domains_tenant_id'),
        UniqueConstraint('domain', name='uq_white_label_domains_domain'),
        ForeignKeyConstraint(['tenant_id', 'branding_id'], ['tenant.tenant_branding.tenant_id', 'tenant.tenant_branding.id'], name='fk_white_label_domains_branding'),
        CheckConstraint("status IN ('pending','verified','active','failed','disabled')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    branding_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    domain: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'pending'"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_white_label_domains_branding: Mapped["TenantTenantBranding"] = relationship("TenantTenantBranding", viewonly=True, foreign_keys="[TenantWhiteLabelDomains.tenant_id, TenantWhiteLabelDomains.branding_id]")


class PlatformConfigDefinitions(TimestampMixin, Base):
    __tablename__ = "config_definitions"
    __table_args__ = (
        UniqueConstraint('config_key', name='uq_config_definitions_key'),
        CheckConstraint('(CASE WHEN default_bool IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN default_text IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN default_number IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN default_integer IS NULL THEN 0 ELSE 1 END) <= 1', name='chk_config_definitions_one_default'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    config_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    value_type: Mapped[str] = mapped_column(ConfigValueTypeEnum, nullable=False)
    default_bool: Mapped[bool | None] = mapped_column(Boolean())
    default_text: Mapped[str | None] = mapped_column(Text())
    default_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    default_integer: Mapped[int | None] = mapped_column(BigInteger())
    validation_regex: Mapped[str | None] = mapped_column(Text())
    min_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    max_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    is_secret: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    is_versioned: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class PlatformConfigScopeLevels(Base):
    __tablename__ = "config_scope_levels"
    __table_args__ = (
        ForeignKeyConstraint(['config_definition_id'], ['platform.config_definitions.id'], name='fk_config_scope_levels_definition'),
        {"schema": "platform"},
    )

    config_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    scope_level: Mapped[str] = mapped_column(ConfigScopeEnum, primary_key=True)

    rel_fk_config_scope_levels_definition: Mapped["PlatformConfigDefinitions"] = relationship("PlatformConfigDefinitions", viewonly=True, foreign_keys="[PlatformConfigScopeLevels.config_definition_id]")


class PlatformConfigAllowedValues(Base):
    __tablename__ = "config_allowed_values"
    __table_args__ = (
        UniqueConstraint('config_definition_id', 'allowed_value', name='uq_config_allowed_values_definition_value'),
        ForeignKeyConstraint(['config_definition_id'], ['platform.config_definitions.id'], name='fk_config_allowed_values_definition'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    config_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    allowed_value: Mapped[str] = mapped_column(Text(), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_config_allowed_values_definition: Mapped["PlatformConfigDefinitions"] = relationship("PlatformConfigDefinitions", viewonly=True, foreign_keys="[PlatformConfigAllowedValues.config_definition_id]")


class TenantConfigValues(TimestampMixin, Base):
    __tablename__ = "config_values"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_config_values_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_config_values_tenant'),
        ForeignKeyConstraint(['config_definition_id'], ['platform.config_definitions.id'], name='fk_config_values_definition'),
        ForeignKeyConstraint(['tenant_id', 'business_unit_id'], ['tenant.business_units.tenant_id', 'tenant.business_units.id'], name='fk_config_values_business_unit'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_config_values_user'),
        ForeignKeyConstraint(['tenant_id', 'created_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_config_values_created_by'),
        CheckConstraint('version > 0'),
        CheckConstraint('(CASE WHEN value_bool IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN value_text IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN value_number IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN value_integer IS NULL THEN 0 ELSE 1 END) +     (CASE WHEN secret_ref IS NULL THEN 0 ELSE 1 END) = 1', name='chk_config_values_one_value'),
        CheckConstraint("(scope_level = 'tenant' AND business_unit_id IS NULL AND team_id IS NULL AND user_id IS NULL) OR     (scope_level = 'business_unit' AND business_unit_id IS NOT NULL AND team_id IS NULL AND user_id IS NULL) OR     (scope_level = 'team' AND team_id IS NOT NULL AND user_id IS NULL) OR     (scope_level = 'user' AND user_id IS NOT NULL)", name='chk_config_values_scope'),
        Index('uq_config_values_active_scope', 'tenant_id', 'config_definition_id', 'scope_level', text("COALESCE(business_unit_id, '00000000-0000-0000-0000-000000000000'::uuid)"), text("COALESCE(team_id, '00000000-0000-0000-0000-000000000000'::uuid)"), text("COALESCE(user_id, '00000000-0000-0000-0000-000000000000'::uuid)"), unique=True, postgresql_where=text('is_active')),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    config_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    scope_level: Mapped[str] = mapped_column(ConfigScopeEnum, nullable=False)
    business_unit_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    team_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    value_bool: Mapped[bool | None] = mapped_column(Boolean())
    value_text: Mapped[str | None] = mapped_column(Text())
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    value_integer: Mapped[int | None] = mapped_column(BigInteger())
    secret_ref: Mapped[str | None] = mapped_column(Text())
    version: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('1'))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_config_values_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantConfigValues.tenant_id]")
    rel_fk_config_values_definition: Mapped["PlatformConfigDefinitions"] = relationship("PlatformConfigDefinitions", viewonly=True, foreign_keys="[TenantConfigValues.config_definition_id]")
    rel_fk_config_values_business_unit: Mapped["TenantBusinessUnits"] = relationship("TenantBusinessUnits", viewonly=True, foreign_keys="[TenantConfigValues.tenant_id, TenantConfigValues.business_unit_id]")
    rel_fk_config_values_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantConfigValues.tenant_id, TenantConfigValues.user_id]")
    rel_fk_config_values_created_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantConfigValues.tenant_id, TenantConfigValues.created_by_user_id]")


class TenantConfigChangeLog(Base):
    __tablename__ = "config_change_log"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_config_change_log_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'config_value_id'], ['tenant.config_values.tenant_id', 'tenant.config_values.id'], name='fk_config_change_log_config_value'),
        ForeignKeyConstraint(['tenant_id', 'changed_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_config_change_log_changed_by'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    config_value_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    old_value_text: Mapped[str | None] = mapped_column(Text())
    new_value_text: Mapped[str] = mapped_column(Text(), nullable=False)
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    change_reason: Mapped[str] = mapped_column(Text(), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    rel_fk_config_change_log_config_value: Mapped["TenantConfigValues"] = relationship("TenantConfigValues", viewonly=True, foreign_keys="[TenantConfigChangeLog.tenant_id, TenantConfigChangeLog.config_value_id]")
    rel_fk_config_change_log_changed_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantConfigChangeLog.tenant_id, TenantConfigChangeLog.changed_by_user_id]")


class TenantWorkingCalendars(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "working_calendars"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_working_calendars_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_working_calendars_tenant'),
        Index('uq_working_calendars_default', 'tenant_id', unique=True, postgresql_where=text('is_default AND deleted_at IS NULL')),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    timezone: Mapped[str] = mapped_column(Text(), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_working_calendars_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantWorkingCalendars.tenant_id]")


class TenantWorkingCalendarDays(CreatedAtMixin, Base):
    __tablename__ = "working_calendar_days"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_working_calendar_days_tenant_id'),
        UniqueConstraint('tenant_id', 'working_calendar_id', 'day_of_week', name='uq_working_calendar_days_calendar_day'),
        ForeignKeyConstraint(['tenant_id', 'working_calendar_id'], ['tenant.working_calendars.tenant_id', 'tenant.working_calendars.id'], name='fk_working_calendar_days_calendar'),
        CheckConstraint('day_of_week BETWEEN 1 AND 7'),
        CheckConstraint('end_time > start_time', name='chk_working_calendar_days_time'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    working_calendar_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger(), nullable=False)
    start_time: Mapped[time] = mapped_column(Time(), nullable=False)
    end_time: Mapped[time] = mapped_column(Time(), nullable=False)

    rel_fk_working_calendar_days_calendar: Mapped["TenantWorkingCalendars"] = relationship("TenantWorkingCalendars", viewonly=True, foreign_keys="[TenantWorkingCalendarDays.tenant_id, TenantWorkingCalendarDays.working_calendar_id]")


class TenantCalendarHolidays(CreatedAtMixin, Base):
    __tablename__ = "calendar_holidays"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_calendar_holidays_tenant_id'),
        UniqueConstraint('tenant_id', 'working_calendar_id', 'holiday_date', name='uq_calendar_holidays_calendar_date'),
        ForeignKeyConstraint(['tenant_id', 'working_calendar_id'], ['tenant.working_calendars.tenant_id', 'tenant.working_calendars.id'], name='fk_calendar_holidays_calendar'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    working_calendar_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    holiday_date: Mapped[date] = mapped_column(Date(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    is_working_day_override: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_calendar_holidays_calendar: Mapped["TenantWorkingCalendars"] = relationship("TenantWorkingCalendars", viewonly=True, foreign_keys="[TenantCalendarHolidays.tenant_id, TenantCalendarHolidays.working_calendar_id]")


class TenantLocalizationResources(TimestampMixin, Base):
    __tablename__ = "localization_resources"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_localization_resources_tenant_id'),
        UniqueConstraint('tenant_id', 'locale', 'resource_key', name='uq_localization_resources_locale_key'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_localization_resources_tenant'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    locale: Mapped[str] = mapped_column(Text(), nullable=False)
    resource_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    resource_value: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_localization_resources_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantLocalizationResources.tenant_id]")


class TenantTeams(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_teams_tenant_id'),
        UniqueConstraint('tenant_id', 'name', name='uq_teams_tenant_name'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_teams_tenant'),
        ForeignKeyConstraint(['tenant_id', 'business_unit_id'], ['tenant.business_units.tenant_id', 'tenant.business_units.id'], name='fk_teams_business_unit'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    business_unit_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())

    rel_fk_teams_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantTeams.tenant_id]")
    rel_fk_teams_business_unit: Mapped["TenantBusinessUnits"] = relationship("TenantBusinessUnits", viewonly=True, foreign_keys="[TenantTeams.tenant_id, TenantTeams.business_unit_id]")


class TenantTeamMembers(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'team_id'], ['tenant.teams.tenant_id', 'tenant.teams.id'], name='fk_team_members_team'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_team_members_user'),
        CheckConstraint('left_at IS NULL OR left_at > joined_at', name='chk_team_members_left_after_joined'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    team_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    role_label: Mapped[str | None] = mapped_column(Text())
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_team_members_team: Mapped["TenantTeams"] = relationship("TenantTeams", viewonly=True, foreign_keys="[TenantTeamMembers.tenant_id, TenantTeamMembers.team_id]")
    rel_fk_team_members_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantTeamMembers.tenant_id, TenantTeamMembers.user_id]")


class TenantApiKeys(TimestampMixin, Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_api_keys_tenant_id'),
        UniqueConstraint('key_hash', name='uq_api_keys_hash'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_api_keys_tenant'),
        ForeignKeyConstraint(['tenant_id', 'created_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_api_keys_created_by'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    key_prefix: Mapped[str] = mapped_column(Text(), nullable=False)
    key_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    rate_limit_tier: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'standard'"))
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_api_keys_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantApiKeys.tenant_id]")
    rel_fk_api_keys_created_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantApiKeys.tenant_id, TenantApiKeys.created_by_user_id]")


class TenantApiKeyScopes(CreatedAtMixin, Base):
    __tablename__ = "api_key_scopes"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'api_key_id'], ['tenant.api_keys.tenant_id', 'tenant.api_keys.id'], name='fk_api_key_scopes_api_key'),
        ForeignKeyConstraint(['tenant_id', 'permission_id'], ['tenant.permissions.tenant_id', 'tenant.permissions.id'], name='fk_api_key_scopes_permission'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    api_key_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    rel_fk_api_key_scopes_api_key: Mapped["TenantApiKeys"] = relationship("TenantApiKeys", viewonly=True, foreign_keys="[TenantApiKeyScopes.tenant_id, TenantApiKeyScopes.api_key_id]")
    rel_fk_api_key_scopes_permission: Mapped["TenantPermissions"] = relationship("TenantPermissions", viewonly=True, foreign_keys="[TenantApiKeyScopes.tenant_id, TenantApiKeyScopes.permission_id]")


class TenantMobileDeviceRegistrations(TimestampMixin, Base):
    __tablename__ = "mobile_device_registrations"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_mobile_device_registrations_tenant_id'),
        UniqueConstraint('tenant_id', 'user_id', 'device_fingerprint_hash', name='uq_mobile_device_registrations_device'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_mobile_device_registrations_user'),
        CheckConstraint("platform IN ('ios','android','web')"),
        CheckConstraint("status IN ('active','revoked','lost')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    device_fingerprint_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    push_token_hash: Mapped[str | None] = mapped_column(Text())
    platform: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'active'"))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_mobile_device_registrations_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantMobileDeviceRegistrations.tenant_id, TenantMobileDeviceRegistrations.user_id]")


class TenantDomainVerifications(TimestampMixin, Base):
    __tablename__ = "domain_verifications"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_domain_verifications_tenant_id'),
        UniqueConstraint('tenant_id', 'domain', name='uq_domain_verifications_tenant_domain'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_domain_verifications_tenant'),
        CheckConstraint("status IN ('pending','verified','failed','revoked')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    domain: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    verification_token_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'pending'"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_domain_verifications_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantDomainVerifications.tenant_id]")

