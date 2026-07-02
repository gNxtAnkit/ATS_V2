# db/models/billing.py
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



class BillingSubscriptions(TimestampMixin, LockVersionMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_subscriptions_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_subscriptions_tenant'),
        ForeignKeyConstraint(['plan_id'], ['platform.plans.id'], name='fk_subscriptions_plan'),
        CheckConstraint("status IN('trialing','active','past_due','suspended','cancelled','churned')"),
        CheckConstraint('current_period_end>=current_period_start', name='chk_subscriptions_period'),
        Index('uq_subscriptions_active_tenant', 'tenant_id', unique=True, postgresql_where=text("status IN('trialing','active','past_due','suspended')")),
        {"schema": "billing"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    plan_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'active'"))
    billing_interval: Mapped[str] = mapped_column(BillingIntervalEnum, nullable=False)
    current_period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    current_period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_subscriptions_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[BillingSubscriptions.tenant_id]")
    rel_fk_subscriptions_plan: Mapped["PlatformPlans"] = relationship("PlatformPlans", viewonly=True, foreign_keys="[BillingSubscriptions.plan_id]")


class BillingSubscriptionItems(TimestampMixin, Base):
    __tablename__ = "subscription_items"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_subscription_items_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'subscription_id'], ['billing.subscriptions.tenant_id', 'billing.subscriptions.id'], name='fk_subscription_items_subscription'),
        ForeignKeyConstraint(['addon_id'], ['platform.plan_addons.id'], name='fk_subscription_items_addon'),
        CheckConstraint('quantity>0'),
        {"schema": "billing"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    subscription_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    addon_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    quantity: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('1'))
    unit_price: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False, server_default=text('0'))
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False, server_default=text("'USD'"))

    rel_fk_subscription_items_subscription: Mapped["BillingSubscriptions"] = relationship("BillingSubscriptions", viewonly=True, foreign_keys="[BillingSubscriptionItems.tenant_id, BillingSubscriptionItems.subscription_id]")
    rel_fk_subscription_items_addon: Mapped["PlatformPlanAddons"] = relationship("PlatformPlanAddons", viewonly=True, foreign_keys="[BillingSubscriptionItems.addon_id]")


class BillingTenantAddonSubscriptions(TimestampMixin, Base):
    __tablename__ = "tenant_addon_subscriptions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_tenant_addon_subscriptions_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'subscription_id'], ['billing.subscriptions.tenant_id', 'billing.subscriptions.id'], name='fk_tenant_addon_subscriptions_subscription'),
        ForeignKeyConstraint(['addon_id'], ['platform.plan_addons.id'], name='fk_tenant_addon_subscriptions_addon'),
        CheckConstraint("status IN('active','cancelled','expired')"),
        {"schema": "billing"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    subscription_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    addon_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'active'"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_tenant_addon_subscriptions_subscription: Mapped["BillingSubscriptions"] = relationship("BillingSubscriptions", viewonly=True, foreign_keys="[BillingTenantAddonSubscriptions.tenant_id, BillingTenantAddonSubscriptions.subscription_id]")
    rel_fk_tenant_addon_subscriptions_addon: Mapped["PlatformPlanAddons"] = relationship("PlatformPlanAddons", viewonly=True, foreign_keys="[BillingTenantAddonSubscriptions.addon_id]")


class BillingTenantQuotaOverrides(CreatedAtMixin, Base):
    __tablename__ = "tenant_quota_overrides"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_tenant_quota_overrides_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_tenant_quota_overrides_tenant'),
        ForeignKeyConstraint(['quota_definition_id'], ['platform.quota_definitions.id'], name='fk_tenant_quota_overrides_quota'),
        ForeignKeyConstraint(['created_by_platform_user_id'], ['platform.platform_users.id'], name='fk_tenant_quota_overrides_user'),
        CheckConstraint('override_limit>=0'),
        {"schema": "billing"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    quota_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    override_limit: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    reason: Mapped[str] = mapped_column(Text(), nullable=False)
    created_by_platform_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_tenant_quota_overrides_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[BillingTenantQuotaOverrides.tenant_id]")
    rel_fk_tenant_quota_overrides_quota: Mapped["PlatformQuotaDefinitions"] = relationship("PlatformQuotaDefinitions", viewonly=True, foreign_keys="[BillingTenantQuotaOverrides.quota_definition_id]")
    rel_fk_tenant_quota_overrides_user: Mapped["PlatformPlatformUsers"] = relationship("PlatformPlatformUsers", viewonly=True, foreign_keys="[BillingTenantQuotaOverrides.created_by_platform_user_id]")


class BillingUsageEvents(Base):
    __tablename__ = "usage_events"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', 'occurred_at', name='uq_usage_events_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_usage_events_tenant'),
        ForeignKeyConstraint(['quota_definition_id'], ['platform.quota_definitions.id'], name='fk_usage_events_quota'),
        ForeignKeyConstraint(['tenant_id', 'entity_reference_id'], ['tenant.entity_references.tenant_id', 'tenant.entity_references.id'], name='fk_usage_events_entity'),
        CheckConstraint('quantity>=0'),
        {"schema": "billing", "postgresql_partition_by": "RANGE(occurred_at)"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    quota_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    source: Mapped[str] = mapped_column(UsageSourceEnum, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit: Mapped[str] = mapped_column(Text(), nullable=False)
    entity_reference_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, server_default=text('now()'))

    rel_fk_usage_events_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[BillingUsageEvents.tenant_id]")
    rel_fk_usage_events_quota: Mapped["PlatformQuotaDefinitions"] = relationship("PlatformQuotaDefinitions", viewonly=True, foreign_keys="[BillingUsageEvents.quota_definition_id]")
    rel_fk_usage_events_entity: Mapped["TenantEntityReferences"] = relationship("TenantEntityReferences", viewonly=True, foreign_keys="[BillingUsageEvents.tenant_id, BillingUsageEvents.entity_reference_id]")


class BillingUsageAggregations(CreatedAtMixin, Base):
    __tablename__ = "usage_aggregations"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_usage_aggregations_tenant_id'),
        UniqueConstraint('tenant_id', 'quota_definition_id', 'period_start', 'period_end', name='uq_usage_aggregations_key'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_usage_aggregations_tenant'),
        ForeignKeyConstraint(['quota_definition_id'], ['platform.quota_definitions.id'], name='fk_usage_aggregations_quota'),
        CheckConstraint('quantity>=0'),
        CheckConstraint('period_end>=period_start', name='chk_usage_aggregations_period'),
        Index('idx_usage_aggregations_period', 'tenant_id', 'period_start', 'period_end'),
        {"schema": "billing"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    quota_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    rel_fk_usage_aggregations_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[BillingUsageAggregations.tenant_id]")
    rel_fk_usage_aggregations_quota: Mapped["PlatformQuotaDefinitions"] = relationship("PlatformQuotaDefinitions", viewonly=True, foreign_keys="[BillingUsageAggregations.quota_definition_id]")


class BillingBillingAddresses(TimestampMixin, Base):
    __tablename__ = "billing_addresses"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_billing_addresses_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_billing_addresses_tenant'),
        {"schema": "billing"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    line1: Mapped[str] = mapped_column(Text(), nullable=False)
    line2: Mapped[str | None] = mapped_column(Text())
    city: Mapped[str] = mapped_column(Text(), nullable=False)
    state_region: Mapped[str | None] = mapped_column(Text())
    postal_code: Mapped[str | None] = mapped_column(Text())
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(Text())

    rel_fk_billing_addresses_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[BillingBillingAddresses.tenant_id]")


class BillingPaymentMethods(TimestampMixin, Base):
    __tablename__ = "payment_methods"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_payment_methods_tenant_id'),
        UniqueConstraint('provider', 'provider_payment_method_id', name='uq_payment_methods_provider'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_payment_methods_tenant'),
        ForeignKeyConstraint(['tenant_id', 'billing_address_id'], ['billing.billing_addresses.tenant_id', 'billing.billing_addresses.id'], name='fk_payment_methods_address'),
        CheckConstraint("method_type IN('card','bank_transfer','upi','wire','manual')"),
        CheckConstraint('expiry_month BETWEEN 1 AND 12'),
        Index('uq_payment_methods_default', 'tenant_id', unique=True, postgresql_where=text('is_default AND revoked_at IS NULL')),
        {"schema": "billing"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    billing_address_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    provider: Mapped[str] = mapped_column(Text(), nullable=False)
    provider_payment_method_id: Mapped[str] = mapped_column(Text(), nullable=False)
    method_type: Mapped[str] = mapped_column(Text(), nullable=False)
    brand: Mapped[str | None] = mapped_column(Text())
    last4: Mapped[str | None] = mapped_column(Text())
    expiry_month: Mapped[int | None] = mapped_column(SmallInteger())
    expiry_year: Mapped[int | None] = mapped_column(SmallInteger())
    is_default: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_payment_methods_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[BillingPaymentMethods.tenant_id]")
    rel_fk_payment_methods_address: Mapped["BillingBillingAddresses"] = relationship("BillingBillingAddresses", viewonly=True, foreign_keys="[BillingPaymentMethods.tenant_id, BillingPaymentMethods.billing_address_id]")


class BillingInvoices(TimestampMixin, Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_invoices_tenant_id'),
        UniqueConstraint('tenant_id', 'invoice_number', name='uq_invoices_number'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_invoices_tenant'),
        ForeignKeyConstraint(['tenant_id', 'subscription_id'], ['billing.subscriptions.tenant_id', 'billing.subscriptions.id'], name='fk_invoices_subscription'),
        CheckConstraint('total_amount = subtotal_amount + tax_amount - discount_amount', name='chk_invoices_total'),
        {"schema": "billing"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    invoice_number: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(InvoiceStatusEnum, nullable=False, server_default=text("'draft'"))
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False, server_default=text('0'))
    subtotal_amount: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False, server_default=text('0'))
    tax_amount: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False, server_default=text('0'))
    discount_amount: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False, server_default=text('0'))
    due_date: Mapped[date | None] = mapped_column(Date())
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_invoices_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[BillingInvoices.tenant_id]")
    rel_fk_invoices_subscription: Mapped["BillingSubscriptions"] = relationship("BillingSubscriptions", viewonly=True, foreign_keys="[BillingInvoices.tenant_id, BillingInvoices.subscription_id]")


class BillingInvoiceLineItems(CreatedAtMixin, Base):
    __tablename__ = "invoice_line_items"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_invoice_line_items_tenant_id'),
        UniqueConstraint('tenant_id', 'invoice_id', 'line_number', name='uq_invoice_line_items_line'),
        ForeignKeyConstraint(['tenant_id', 'invoice_id'], ['billing.invoices.tenant_id', 'billing.invoices.id'], name='fk_invoice_line_items_invoice'),
        ForeignKeyConstraint(['quota_definition_id'], ['platform.quota_definitions.id'], name='fk_invoice_line_items_quota'),
        ForeignKeyConstraint(['addon_id'], ['platform.plan_addons.id'], name='fk_invoice_line_items_addon'),
        CheckConstraint('line_number>0'),
        CheckConstraint('quantity>0'),
        {"schema": "billing"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    invoice_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer(), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False)
    quota_definition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    addon_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_invoice_line_items_invoice: Mapped["BillingInvoices"] = relationship("BillingInvoices", viewonly=True, foreign_keys="[BillingInvoiceLineItems.tenant_id, BillingInvoiceLineItems.invoice_id]")
    rel_fk_invoice_line_items_quota: Mapped["PlatformQuotaDefinitions"] = relationship("PlatformQuotaDefinitions", viewonly=True, foreign_keys="[BillingInvoiceLineItems.quota_definition_id]")
    rel_fk_invoice_line_items_addon: Mapped["PlatformPlanAddons"] = relationship("PlatformPlanAddons", viewonly=True, foreign_keys="[BillingInvoiceLineItems.addon_id]")


class BillingInvoiceTaxes(CreatedAtMixin, Base):
    __tablename__ = "invoice_taxes"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_invoice_taxes_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'invoice_id'], ['billing.invoices.tenant_id', 'billing.invoices.id'], name='fk_invoice_taxes_invoice'),
        {"schema": "billing"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    invoice_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    tax_type: Mapped[str] = mapped_column(Text(), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(Text(), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Percent0100Domain, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False)

    rel_fk_invoice_taxes_invoice: Mapped["BillingInvoices"] = relationship("BillingInvoices", viewonly=True, foreign_keys="[BillingInvoiceTaxes.tenant_id, BillingInvoiceTaxes.invoice_id]")


class BillingPaymentAttempts(Base):
    __tablename__ = "payment_attempts"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_payment_attempts_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'invoice_id'], ['billing.invoices.tenant_id', 'billing.invoices.id'], name='fk_payment_attempts_invoice'),
        ForeignKeyConstraint(['tenant_id', 'payment_method_id'], ['billing.payment_methods.tenant_id', 'billing.payment_methods.id'], name='fk_payment_attempts_method'),
        {"schema": "billing"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    invoice_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    payment_method_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    provider: Mapped[str] = mapped_column(Text(), nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(PaymentStatusEnum, nullable=False, server_default=text("'pending'"))
    amount: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text())

    rel_fk_payment_attempts_invoice: Mapped["BillingInvoices"] = relationship("BillingInvoices", viewonly=True, foreign_keys="[BillingPaymentAttempts.tenant_id, BillingPaymentAttempts.invoice_id]")
    rel_fk_payment_attempts_method: Mapped["BillingPaymentMethods"] = relationship("BillingPaymentMethods", viewonly=True, foreign_keys="[BillingPaymentAttempts.tenant_id, BillingPaymentAttempts.payment_method_id]")


class BillingCredits(CreatedAtMixin, Base):
    __tablename__ = "credits"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_credits_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_credits_tenant'),
        ForeignKeyConstraint(['tenant_id', 'invoice_id'], ['billing.invoices.tenant_id', 'billing.invoices.id'], name='fk_credits_invoice'),
        ForeignKeyConstraint(['issued_by_platform_user_id'], ['platform.platform_users.id'], name='fk_credits_user'),
        {"schema": "billing"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    amount: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False)
    reason: Mapped[str] = mapped_column(Text(), nullable=False)
    issued_by_platform_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_credits_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[BillingCredits.tenant_id]")
    rel_fk_credits_invoice: Mapped["BillingInvoices"] = relationship("BillingInvoices", viewonly=True, foreign_keys="[BillingCredits.tenant_id, BillingCredits.invoice_id]")
    rel_fk_credits_user: Mapped["PlatformPlatformUsers"] = relationship("PlatformPlatformUsers", viewonly=True, foreign_keys="[BillingCredits.issued_by_platform_user_id]")

