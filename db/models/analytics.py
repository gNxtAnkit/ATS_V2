# db/models/analytics.py
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



class TenantDashboards(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "dashboards"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_dashboards_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_dashboards_tenant'),
        ForeignKeyConstraint(['tenant_id', 'owner_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_dashboards_owner'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    is_default: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_dashboards_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantDashboards.tenant_id]")
    rel_fk_dashboards_owner: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantDashboards.tenant_id, TenantDashboards.owner_user_id]")


class TenantDashboardWidgets(TimestampMixin, Base):
    __tablename__ = "dashboard_widgets"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_dashboard_widgets_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'dashboard_id'], ['tenant.dashboards.tenant_id', 'tenant.dashboards.id'], name='fk_dashboard_widgets_dashboard'),
        CheckConstraint('width>0'),
        CheckConstraint('height>0'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    dashboard_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    widget_key: Mapped[str] = mapped_column(Text(), nullable=False)
    widget_type: Mapped[str] = mapped_column(Text(), nullable=False)
    report_definition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    position_x: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    position_y: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    width: Mapped[int] = mapped_column(Integer(), nullable=False)
    height: Mapped[int] = mapped_column(Integer(), nullable=False)

    rel_fk_dashboard_widgets_dashboard: Mapped["TenantDashboards"] = relationship("TenantDashboards", viewonly=True, foreign_keys="[TenantDashboardWidgets.tenant_id, TenantDashboardWidgets.dashboard_id]")


class TenantDashboardShares(CreatedAtMixin, Base):
    __tablename__ = "dashboard_shares"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'dashboard_id'], ['tenant.dashboards.tenant_id', 'tenant.dashboards.id'], name='fk_dashboard_shares_dashboard'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_dashboard_shares_user'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    dashboard_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    can_edit: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_dashboard_shares_dashboard: Mapped["TenantDashboards"] = relationship("TenantDashboards", viewonly=True, foreign_keys="[TenantDashboardShares.tenant_id, TenantDashboardShares.dashboard_id]")
    rel_fk_dashboard_shares_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantDashboardShares.tenant_id, TenantDashboardShares.user_id]")


class TenantReportDefinitions(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "report_definitions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_report_definitions_tenant_id'),
        UniqueConstraint('tenant_id', 'report_key', name='uq_report_definitions_key'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_report_definitions_tenant'),
        ForeignKeyConstraint(['tenant_id', 'owner_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_report_definitions_owner'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    report_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    base_view: Mapped[str] = mapped_column(Text(), nullable=False)
    default_format: Mapped[str] = mapped_column(ReportFormatEnum, nullable=False, server_default=text("'csv'"))
    schedule_cron: Mapped[str | None] = mapped_column(Text())

    rel_fk_report_definitions_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantReportDefinitions.tenant_id]")
    rel_fk_report_definitions_owner: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantReportDefinitions.tenant_id, TenantReportDefinitions.owner_user_id]")


class TenantReportFilters(Base):
    __tablename__ = "report_filters"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_report_filters_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'report_definition_id'], ['tenant.report_definitions.tenant_id', 'tenant.report_definitions.id'], name='fk_report_filters_report'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    report_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    field_key: Mapped[str] = mapped_column(Text(), nullable=False)
    operator: Mapped[str] = mapped_column(ConditionOperatorEnum, nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text())
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    value_bool: Mapped[bool | None] = mapped_column(Boolean())
    value_date: Mapped[date | None] = mapped_column(Date())

    rel_fk_report_filters_report: Mapped["TenantReportDefinitions"] = relationship("TenantReportDefinitions", viewonly=True, foreign_keys="[TenantReportFilters.tenant_id, TenantReportFilters.report_definition_id]")


class TenantReportColumns(Base):
    __tablename__ = "report_columns"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_report_columns_tenant_id'),
        UniqueConstraint('tenant_id', 'report_definition_id', 'column_key', name='uq_report_columns_key'),
        ForeignKeyConstraint(['tenant_id', 'report_definition_id'], ['tenant.report_definitions.tenant_id', 'tenant.report_definitions.id'], name='fk_report_columns_report'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    report_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    column_key: Mapped[str] = mapped_column(Text(), nullable=False)
    label: Mapped[str] = mapped_column(Text(), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    is_group_by: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_report_columns_report: Mapped["TenantReportDefinitions"] = relationship("TenantReportDefinitions", viewonly=True, foreign_keys="[TenantReportColumns.tenant_id, TenantReportColumns.report_definition_id]")


class TenantReportScheduleRecipients(CreatedAtMixin, Base):
    __tablename__ = "report_schedule_recipients"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'report_definition_id'], ['tenant.report_definitions.tenant_id', 'tenant.report_definitions.id'], name='fk_report_schedule_recipients_report'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_report_schedule_recipients_user'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    report_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    rel_fk_report_schedule_recipients_report: Mapped["TenantReportDefinitions"] = relationship("TenantReportDefinitions", viewonly=True, foreign_keys="[TenantReportScheduleRecipients.tenant_id, TenantReportScheduleRecipients.report_definition_id]")
    rel_fk_report_schedule_recipients_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantReportScheduleRecipients.tenant_id, TenantReportScheduleRecipients.user_id]")


class TenantExportJobs(CreatedAtMixin, Base):
    __tablename__ = "export_jobs"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_export_jobs_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'report_definition_id'], ['tenant.report_definitions.tenant_id', 'tenant.report_definitions.id'], name='fk_export_jobs_report'),
        ForeignKeyConstraint(['tenant_id', 'requested_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_export_jobs_user'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    report_definition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    format: Mapped[str] = mapped_column(ReportFormatEnum, nullable=False)
    status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False, server_default=text("'pending'"))
    result_uri: Mapped[str | None] = mapped_column(Text())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_export_jobs_report: Mapped["TenantReportDefinitions"] = relationship("TenantReportDefinitions", viewonly=True, foreign_keys="[TenantExportJobs.tenant_id, TenantExportJobs.report_definition_id]")
    rel_fk_export_jobs_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantExportJobs.tenant_id, TenantExportJobs.requested_by_user_id]")


class AnalyticsMetricDefinitions(CreatedAtMixin, Base):
    __tablename__ = "metric_definitions"
    __table_args__ = (
        UniqueConstraint('metric_key', name='uq_metric_definitions_key'),
        {"schema": "analytics"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    metric_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    display_name: Mapped[str] = mapped_column(Text(), nullable=False)
    unit: Mapped[str] = mapped_column(Text(), nullable=False)


class AnalyticsDimensionDefinitions(CreatedAtMixin, Base):
    __tablename__ = "dimension_definitions"
    __table_args__ = (
        UniqueConstraint('dimension_key', name='uq_dimension_definitions_key'),
        {"schema": "analytics"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    dimension_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    display_name: Mapped[str] = mapped_column(Text(), nullable=False)


class AnalyticsAnalyticsEvents(Base):
    __tablename__ = "analytics_events"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', 'occurred_at', name='uq_analytics_events_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_analytics_events_tenant'),
        ForeignKeyConstraint(['tenant_id', 'entity_reference_id'], ['tenant.entity_references.tenant_id', 'tenant.entity_references.id'], name='fk_analytics_events_entity'),
        Index('idx_analytics_events_tenant_time', 'tenant_id', text('occurred_at DESC')),
        {"schema": "analytics", "postgresql_partition_by": "RANGE(occurred_at)"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    event_key: Mapped[str] = mapped_column(Text(), nullable=False)
    entity_reference_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, server_default=text('now()'))

    rel_fk_analytics_events_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[AnalyticsAnalyticsEvents.tenant_id]")
    rel_fk_analytics_events_entity: Mapped["TenantEntityReferences"] = relationship("TenantEntityReferences", viewonly=True, foreign_keys="[AnalyticsAnalyticsEvents.tenant_id, AnalyticsAnalyticsEvents.entity_reference_id]")


class AnalyticsAnalyticsEventMetricValues(Base):
    __tablename__ = "analytics_event_metric_values"
    __table_args__ = (
        ForeignKeyConstraint(['metric_definition_id'], ['analytics.metric_definitions.id'], name='fk_analytics_event_metric_values_metric'),
        {"schema": "analytics"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    analytics_event_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    metric_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    rel_fk_analytics_event_metric_values_metric: Mapped["AnalyticsMetricDefinitions"] = relationship("AnalyticsMetricDefinitions", viewonly=True, foreign_keys="[AnalyticsAnalyticsEventMetricValues.metric_definition_id]")


class AnalyticsAnalyticsEventDimensionValues(Base):
    __tablename__ = "analytics_event_dimension_values"
    __table_args__ = (
        ForeignKeyConstraint(['dimension_definition_id'], ['analytics.dimension_definitions.id'], name='fk_analytics_event_dimension_values_dimension'),
        {"schema": "analytics"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    analytics_event_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    dimension_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    dimension_value: Mapped[str] = mapped_column(Text(), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    rel_fk_analytics_event_dimension_values_dimension: Mapped["AnalyticsDimensionDefinitions"] = relationship("AnalyticsDimensionDefinitions", viewonly=True, foreign_keys="[AnalyticsAnalyticsEventDimensionValues.dimension_definition_id]")


class AnalyticsDailyMetricFacts(CreatedAtMixin, Base):
    __tablename__ = "daily_metric_facts"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_daily_metric_facts_tenant'),
        ForeignKeyConstraint(['metric_definition_id'], ['analytics.metric_definitions.id'], name='fk_daily_metric_facts_metric'),
        {"schema": "analytics"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    metric_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    fact_date: Mapped[date] = mapped_column(Date(), primary_key=True)
    dimension_hash: Mapped[str] = mapped_column(Text(), primary_key=True, server_default=text("'all'"))
    metric_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)

    rel_fk_daily_metric_facts_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[AnalyticsDailyMetricFacts.tenant_id]")
    rel_fk_daily_metric_facts_metric: Mapped["AnalyticsMetricDefinitions"] = relationship("AnalyticsMetricDefinitions", viewonly=True, foreign_keys="[AnalyticsDailyMetricFacts.metric_definition_id]")


class ComplianceRetentionPolicies(TimestampMixin, Base):
    __tablename__ = "retention_policies"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_retention_policies_tenant_id'),
        UniqueConstraint('tenant_id', 'resource_key', name='uq_retention_policies_resource'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_retention_policies_tenant'),
        CheckConstraint('retention_days>0'),
        CheckConstraint('archive_after_days IS NULL OR archive_after_days>0'),
        {"schema": "compliance"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    resource_key: Mapped[str] = mapped_column(Text(), nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer(), nullable=False)
    archive_after_days: Mapped[int | None] = mapped_column(Integer())
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_retention_policies_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[ComplianceRetentionPolicies.tenant_id]")


class ComplianceLegalHolds(Base):
    __tablename__ = "legal_holds"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_legal_holds_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_legal_holds_candidate'),
        ForeignKeyConstraint(['tenant_id', 'entity_reference_id'], ['tenant.entity_references.tenant_id', 'tenant.entity_references.id'], name='fk_legal_holds_entity'),
        ForeignKeyConstraint(['tenant_id', 'placed_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_legal_holds_user'),
        CheckConstraint("status IN('active','released')"),
        {"schema": "compliance"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    entity_reference_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    reason: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'active'"))
    placed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_legal_holds_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[ComplianceLegalHolds.tenant_id, ComplianceLegalHolds.candidate_id]")
    rel_fk_legal_holds_entity: Mapped["TenantEntityReferences"] = relationship("TenantEntityReferences", viewonly=True, foreign_keys="[ComplianceLegalHolds.tenant_id, ComplianceLegalHolds.entity_reference_id]")
    rel_fk_legal_holds_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[ComplianceLegalHolds.tenant_id, ComplianceLegalHolds.placed_by_user_id]")


class ComplianceEvidencePackages(TimestampMixin, Base):
    __tablename__ = "evidence_packages"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_evidence_packages_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_evidence_packages_tenant'),
        ForeignKeyConstraint(['tenant_id', 'created_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_evidence_packages_user'),
        CheckConstraint("status IN('draft','collecting','ready','submitted','accepted')"),
        CheckConstraint('period_end>=period_start', name='chk_evidence_packages_period'),
        {"schema": "compliance"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    framework: Mapped[str] = mapped_column(ComplianceFrameworkEnum, nullable=False)
    period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'draft'"))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    storage_uri: Mapped[str | None] = mapped_column(Text())

    rel_fk_evidence_packages_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[ComplianceEvidencePackages.tenant_id]")
    rel_fk_evidence_packages_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[ComplianceEvidencePackages.tenant_id, ComplianceEvidencePackages.created_by_user_id]")


class ComplianceEvidenceItems(CreatedAtMixin, Base):
    __tablename__ = "evidence_items"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_evidence_items_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'evidence_package_id'], ['compliance.evidence_packages.tenant_id', 'compliance.evidence_packages.id'], name='fk_evidence_items_package'),
        {"schema": "compliance"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    evidence_package_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    evidence_key: Mapped[str] = mapped_column(Text(), nullable=False)
    source_table: Mapped[str | None] = mapped_column(Text())
    source_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    storage_uri: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False, server_default=text("'pending'"))

    rel_fk_evidence_items_package: Mapped["ComplianceEvidencePackages"] = relationship("ComplianceEvidencePackages", viewonly=True, foreign_keys="[ComplianceEvidenceItems.tenant_id, ComplianceEvidenceItems.evidence_package_id]")

