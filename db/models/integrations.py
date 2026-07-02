# db/models/integrations.py
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



class PlatformConnectorDefinitions(TimestampMixin, Base):
    __tablename__ = "connector_definitions"
    __table_args__ = (
        UniqueConstraint('provider_key', name='uq_connector_definitions_provider'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    provider_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    display_name: Mapped[str] = mapped_column(Text(), nullable=False)
    category: Mapped[str] = mapped_column(ConnectorCategoryEnum, nullable=False)
    auth_type: Mapped[str] = mapped_column(ConnectorAuthTypeEnum, nullable=False)
    status: Mapped[str] = mapped_column(PlanStatusEnum, nullable=False, server_default=text("'active'"))


class PlatformConnectorOperations(Base):
    __tablename__ = "connector_operations"
    __table_args__ = (
        ForeignKeyConstraint(['connector_definition_id'], ['platform.connector_definitions.id'], name='fk_connector_operations_definition'),
        {"schema": "platform"},
    )

    connector_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    operation_key: Mapped[str] = mapped_column(postgresql.CITEXT(), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text())

    rel_fk_connector_operations_definition: Mapped["PlatformConnectorDefinitions"] = relationship("PlatformConnectorDefinitions", viewonly=True, foreign_keys="[PlatformConnectorOperations.connector_definition_id]")


class PlatformConnectorVersions(Base):
    __tablename__ = "connector_versions"
    __table_args__ = (
        UniqueConstraint('connector_definition_id', 'version_label', name='uq_connector_versions_definition_version'),
        ForeignKeyConstraint(['connector_definition_id'], ['platform.connector_definitions.id'], name='fk_connector_versions_definition'),
        {"schema": "platform"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    connector_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    version_label: Mapped[str] = mapped_column(Text(), nullable=False)
    released_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sunset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_connector_versions_definition: Mapped["PlatformConnectorDefinitions"] = relationship("PlatformConnectorDefinitions", viewonly=True, foreign_keys="[PlatformConnectorVersions.connector_definition_id]")


class TenantConnectorInstances(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "connector_instances"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_connector_instances_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_connector_instances_tenant'),
        ForeignKeyConstraint(['connector_definition_id'], ['platform.connector_definitions.id'], name='fk_connector_instances_definition'),
        ForeignKeyConstraint(['connector_version_id'], ['platform.connector_versions.id'], name='fk_connector_instances_version'),
        ForeignKeyConstraint(['tenant_id', 'created_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_connector_instances_created_by'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    connector_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    connector_version_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(ConnectorStatusEnum, nullable=False, server_default=text("'pending_setup'"))
    credentials_ref: Mapped[str | None] = mapped_column(Text())
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_connector_instances_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantConnectorInstances.tenant_id]")
    rel_fk_connector_instances_definition: Mapped["PlatformConnectorDefinitions"] = relationship("PlatformConnectorDefinitions", viewonly=True, foreign_keys="[TenantConnectorInstances.connector_definition_id]")
    rel_fk_connector_instances_version: Mapped["PlatformConnectorVersions"] = relationship("PlatformConnectorVersions", viewonly=True, foreign_keys="[TenantConnectorInstances.connector_version_id]")
    rel_fk_connector_instances_created_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantConnectorInstances.tenant_id, TenantConnectorInstances.created_by_user_id]")


class TenantConnectorInstanceSettings(TimestampMixin, Base):
    __tablename__ = "connector_instance_settings"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_connector_instance_settings_tenant_id'),
        UniqueConstraint('tenant_id', 'connector_instance_id', 'setting_key', name='uq_connector_instance_settings_key'),
        ForeignKeyConstraint(['tenant_id', 'connector_instance_id'], ['tenant.connector_instances.tenant_id', 'tenant.connector_instances.id'], name='fk_connector_instance_settings_instance'),
        CheckConstraint('(value_text IS NOT NULL)::int+(value_number IS NOT NULL)::int+(value_bool IS NOT NULL)::int+(secret_ref IS NOT NULL)::int=1', name='chk_connector_instance_settings_one_value'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    connector_instance_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    setting_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text())
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    value_bool: Mapped[bool | None] = mapped_column(Boolean())
    secret_ref: Mapped[str | None] = mapped_column(Text())

    rel_fk_connector_instance_settings_instance: Mapped["TenantConnectorInstances"] = relationship("TenantConnectorInstances", viewonly=True, foreign_keys="[TenantConnectorInstanceSettings.tenant_id, TenantConnectorInstanceSettings.connector_instance_id]")


class TenantSyncJobs(TimestampMixin, Base):
    __tablename__ = "sync_jobs"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_sync_jobs_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'connector_instance_id'], ['tenant.connector_instances.tenant_id', 'tenant.connector_instances.id'], name='fk_sync_jobs_instance'),
        CheckConstraint('records_processed>=0'),
        CheckConstraint('records_failed>=0'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    connector_instance_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    sync_type: Mapped[str] = mapped_column(SyncTypeEnum, nullable=False)
    status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False, server_default=text("'pending'"))
    external_cursor: Mapped[str | None] = mapped_column(Text())
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_processed: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    records_failed: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text())

    rel_fk_sync_jobs_instance: Mapped["TenantConnectorInstances"] = relationship("TenantConnectorInstances", viewonly=True, foreign_keys="[TenantSyncJobs.tenant_id, TenantSyncJobs.connector_instance_id]")


class TenantSyncJobRecords(CreatedAtMixin, Base):
    __tablename__ = "sync_job_records"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_sync_job_records_tenant_id'),
        UniqueConstraint('tenant_id', 'sync_job_id', 'external_record_id', name='uq_sync_job_records_external'),
        ForeignKeyConstraint(['tenant_id', 'sync_job_id'], ['tenant.sync_jobs.tenant_id', 'tenant.sync_jobs.id'], name='fk_sync_job_records_job'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    sync_job_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    external_record_id: Mapped[str] = mapped_column(Text(), nullable=False)
    record_status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False)
    platform_table: Mapped[str | None] = mapped_column(Text())
    platform_record_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    error_message: Mapped[str | None] = mapped_column(Text())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_sync_job_records_job: Mapped["TenantSyncJobs"] = relationship("TenantSyncJobs", viewonly=True, foreign_keys="[TenantSyncJobRecords.tenant_id, TenantSyncJobRecords.sync_job_id]")


class TenantWebhookEvents(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_webhook_events_tenant_id'),
        UniqueConstraint('tenant_id', 'provider_event_id', name='uq_webhook_events_provider'),
        ForeignKeyConstraint(['tenant_id', 'connector_instance_id'], ['tenant.connector_instances.tenant_id', 'tenant.connector_instances.id'], name='fk_webhook_events_instance'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    connector_instance_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    provider_event_id: Mapped[str] = mapped_column(Text(), nullable=False)
    event_type: Mapped[str] = mapped_column(Text(), nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    payload: Mapped[dict[str, Any]] = mapped_column(postgresql.JSONB(), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False, server_default=text("'pending'"))

    rel_fk_webhook_events_instance: Mapped["TenantConnectorInstances"] = relationship("TenantConnectorInstances", viewonly=True, foreign_keys="[TenantWebhookEvents.tenant_id, TenantWebhookEvents.connector_instance_id]")


class TenantWebhookSubscriptions(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "webhook_subscriptions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_webhook_subscriptions_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_webhook_subscriptions_tenant'),
        ForeignKeyConstraint(['tenant_id', 'created_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_webhook_subscriptions_user'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    target_url: Mapped[str] = mapped_column(Text(), nullable=False)
    signing_secret_ref: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(ConnectorStatusEnum, nullable=False, server_default=text("'connected'"))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_webhook_subscriptions_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantWebhookSubscriptions.tenant_id]")
    rel_fk_webhook_subscriptions_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantWebhookSubscriptions.tenant_id, TenantWebhookSubscriptions.created_by_user_id]")


class TenantWebhookSubscriptionEventTypes(Base):
    __tablename__ = "webhook_subscription_event_types"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'webhook_subscription_id'], ['tenant.webhook_subscriptions.tenant_id', 'tenant.webhook_subscriptions.id'], name='fk_webhook_subscription_event_types_subscription'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    webhook_subscription_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(Text(), primary_key=True)

    rel_fk_webhook_subscription_event_types_subscription: Mapped["TenantWebhookSubscriptions"] = relationship("TenantWebhookSubscriptions", viewonly=True, foreign_keys="[TenantWebhookSubscriptionEventTypes.tenant_id, TenantWebhookSubscriptionEventTypes.webhook_subscription_id]")


class TenantCalendarEvents(TimestampMixin, Base):
    __tablename__ = "calendar_events"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_calendar_events_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'connector_instance_id'], ['tenant.connector_instances.tenant_id', 'tenant.connector_instances.id'], name='fk_calendar_events_connector'),
        CheckConstraint("status IN('tentative','confirmed','cancelled')"),
        CheckConstraint('end_at>start_at', name='chk_calendar_events_time'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    connector_instance_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    external_event_id: Mapped[str | None] = mapped_column(Text())
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(Text(), nullable=False)
    location: Mapped[str | None] = mapped_column(Text())
    meeting_url: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'confirmed'"))

    rel_fk_calendar_events_connector: Mapped["TenantConnectorInstances"] = relationship("TenantConnectorInstances", viewonly=True, foreign_keys="[TenantCalendarEvents.tenant_id, TenantCalendarEvents.connector_instance_id]")


class TenantCalendarEventAttendees(Base):
    __tablename__ = "calendar_event_attendees"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_calendar_event_attendees_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'calendar_event_id'], ['tenant.calendar_events.tenant_id', 'tenant.calendar_events.id'], name='fk_calendar_event_attendees_event'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_calendar_event_attendees_user'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_calendar_event_attendees_candidate'),
        ForeignKeyConstraint(['tenant_id', 'client_contact_id'], ['agency.client_contacts.tenant_id', 'agency.client_contacts.id'], name='fk_calendar_event_attendees_contact'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    calendar_event_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    email: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    client_contact_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    response_status: Mapped[str] = mapped_column(ApprovalStatusEnum, nullable=False, server_default=text("'pending'"))
    is_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_calendar_event_attendees_event: Mapped["TenantCalendarEvents"] = relationship("TenantCalendarEvents", viewonly=True, foreign_keys="[TenantCalendarEventAttendees.tenant_id, TenantCalendarEventAttendees.calendar_event_id]")
    rel_fk_calendar_event_attendees_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantCalendarEventAttendees.tenant_id, TenantCalendarEventAttendees.user_id]")
    rel_fk_calendar_event_attendees_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantCalendarEventAttendees.tenant_id, TenantCalendarEventAttendees.candidate_id]")
    rel_fk_calendar_event_attendees_contact: Mapped["AgencyClientContacts"] = relationship("AgencyClientContacts", viewonly=True, foreign_keys="[TenantCalendarEventAttendees.tenant_id, TenantCalendarEventAttendees.client_contact_id]")


class TenantHrmsFieldMappings(TimestampMixin, Base):
    __tablename__ = "hrms_field_mappings"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_hrms_field_mappings_tenant_id'),
        UniqueConstraint('tenant_id', 'connector_instance_id', 'platform_field', name='uq_hrms_field_mappings_field'),
        ForeignKeyConstraint(['tenant_id', 'connector_instance_id'], ['tenant.connector_instances.tenant_id', 'tenant.connector_instances.id'], name='fk_hrms_field_mappings_instance'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    connector_instance_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    platform_field: Mapped[str] = mapped_column(Text(), nullable=False)
    external_field: Mapped[str] = mapped_column(Text(), nullable=False)
    transformation_rule_key: Mapped[str | None] = mapped_column(Text())

    rel_fk_hrms_field_mappings_instance: Mapped["TenantConnectorInstances"] = relationship("TenantConnectorInstances", viewonly=True, foreign_keys="[TenantHrmsFieldMappings.tenant_id, TenantHrmsFieldMappings.connector_instance_id]")


class TenantHrmsSyncRecords(TimestampMixin, Base):
    __tablename__ = "hrms_sync_records"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_hrms_sync_records_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'connector_instance_id'], ['tenant.connector_instances.tenant_id', 'tenant.connector_instances.id'], name='fk_hrms_sync_records_instance'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_hrms_sync_records_candidate'),
        ForeignKeyConstraint(['tenant_id', 'offer_id'], ['tenant.offers.tenant_id', 'tenant.offers.id'], name='fk_hrms_sync_records_offer'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    connector_instance_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    offer_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    employee_external_id: Mapped[str | None] = mapped_column(Text())
    sync_status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False, server_default=text("'pending'"))
    error_detail: Mapped[str | None] = mapped_column(Text())

    rel_fk_hrms_sync_records_instance: Mapped["TenantConnectorInstances"] = relationship("TenantConnectorInstances", viewonly=True, foreign_keys="[TenantHrmsSyncRecords.tenant_id, TenantHrmsSyncRecords.connector_instance_id]")
    rel_fk_hrms_sync_records_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantHrmsSyncRecords.tenant_id, TenantHrmsSyncRecords.candidate_id]")
    rel_fk_hrms_sync_records_offer: Mapped["TenantOffers"] = relationship("TenantOffers", viewonly=True, foreign_keys="[TenantHrmsSyncRecords.tenant_id, TenantHrmsSyncRecords.offer_id]")


class EventsEventOutbox(Base):
    __tablename__ = "event_outbox"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_event_outbox_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_event_outbox_tenant'),
        CheckConstraint('retry_count>=0'),
        {"schema": "events"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    aggregate_reference_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(Text(), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(postgresql.JSONB(), nullable=False)
    status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False, server_default=text("'pending'"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retry_count: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_event_outbox_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[EventsEventOutbox.tenant_id]")


class EventsDomainEvents(Base):
    __tablename__ = "domain_events"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', 'occurred_at', name='uq_domain_events_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_domain_events_tenant'),
        ForeignKeyConstraint(['tenant_id', 'entity_reference_id'], ['tenant.entity_references.tenant_id', 'tenant.entity_references.id'], name='fk_domain_events_entity'),
        Index('idx_domain_events_tenant_type_time', 'tenant_id', 'event_type', text('occurred_at DESC')),
        {"schema": "events", "postgresql_partition_by": "RANGE(occurred_at)"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    event_type: Mapped[str] = mapped_column(Text(), nullable=False)
    entity_reference_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    source_service: Mapped[str] = mapped_column(Text(), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(postgresql.JSONB(), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, server_default=text('now()'))

    rel_fk_domain_events_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[EventsDomainEvents.tenant_id]")
    rel_fk_domain_events_entity: Mapped["TenantEntityReferences"] = relationship("TenantEntityReferences", viewonly=True, foreign_keys="[EventsDomainEvents.tenant_id, EventsDomainEvents.entity_reference_id]")


class EventsEventSubscriptions(TimestampMixin, Base):
    __tablename__ = "event_subscriptions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_event_subscriptions_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_event_subscriptions_tenant'),
        {"schema": "events"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    target_url: Mapped[str] = mapped_column(Text(), nullable=False)
    signing_secret_ref: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(ConnectorStatusEnum, nullable=False, server_default=text("'connected'"))

    rel_fk_event_subscriptions_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[EventsEventSubscriptions.tenant_id]")


class EventsEventSubscriptionEventTypes(Base):
    __tablename__ = "event_subscription_event_types"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'event_subscription_id'], ['events.event_subscriptions.tenant_id', 'events.event_subscriptions.id'], name='fk_event_subscription_event_types_subscription'),
        {"schema": "events"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    event_subscription_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(Text(), primary_key=True)

    rel_fk_event_subscription_event_types_subscription: Mapped["EventsEventSubscriptions"] = relationship("EventsEventSubscriptions", viewonly=True, foreign_keys="[EventsEventSubscriptionEventTypes.tenant_id, EventsEventSubscriptionEventTypes.event_subscription_id]")


class EventsEventDeliveryAttempts(Base):
    __tablename__ = "event_delivery_attempts"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_event_delivery_attempts_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'event_subscription_id'], ['events.event_subscriptions.tenant_id', 'events.event_subscriptions.id'], name='fk_event_delivery_attempts_subscription'),
        CheckConstraint('attempt_number>0'),
        {"schema": "events"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    event_subscription_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    domain_event_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    attempt_number: Mapped[int] = mapped_column(Integer(), nullable=False)
    status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False)
    response_status: Mapped[int | None] = mapped_column(Integer())
    response_body: Mapped[str | None] = mapped_column(Text())
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    rel_fk_event_delivery_attempts_subscription: Mapped["EventsEventSubscriptions"] = relationship("EventsEventSubscriptions", viewonly=True, foreign_keys="[EventsEventDeliveryAttempts.tenant_id, EventsEventDeliveryAttempts.event_subscription_id]")


class EventsIdempotencyRecords(CreatedAtMixin, Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_idempotency_records_tenant_id'),
        UniqueConstraint('tenant_id', 'idempotency_key', name='uq_idempotency_records_key'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_idempotency_records_tenant'),
        CheckConstraint("status IN('in_progress','completed','failed')"),
        CheckConstraint('expires_at>created_at', name='chk_idempotency_records_expires'),
        {"schema": "events"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    idempotency_key: Mapped[str] = mapped_column(Text(), nullable=False)
    request_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False)
    result_payload: Mapped[dict[str, Any] | None] = mapped_column(postgresql.JSONB())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    rel_fk_idempotency_records_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[EventsIdempotencyRecords.tenant_id]")


class TenantReviewItems(TimestampMixin, LockVersionMixin, Base):
    __tablename__ = "review_items"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_review_items_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'entity_reference_id'], ['tenant.entity_references.tenant_id', 'tenant.entity_references.id'], name='fk_review_items_entity'),
        ForeignKeyConstraint(['tenant_id', 'assigned_to_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_review_items_user'),
        ForeignKeyConstraint(['tenant_id', 'assigned_to_role_id'], ['tenant.roles.tenant_id', 'tenant.roles.id'], name='fk_review_items_role'),
        CheckConstraint('assigned_to_user_id IS NOT NULL OR assigned_to_role_id IS NOT NULL', name='chk_review_items_assignee'),
        Index('idx_review_items_queue', 'tenant_id', 'status', 'assigned_to_user_id', 'sla_due_at'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    source_module: Mapped[str] = mapped_column(Text(), nullable=False)
    source_action_type: Mapped[str] = mapped_column(AiActionTypeEnum, nullable=False)
    entity_reference_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    ai_output_text: Mapped[str] = mapped_column(Text(), nullable=False)
    ai_output_raw_snapshot: Mapped[dict[str, Any] | None] = mapped_column(postgresql.JSONB())
    ai_confidence: Mapped[Decimal] = mapped_column(ConfidenceScoreDomain, nullable=False)
    ai_reasoning_summary: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(ReviewItemStatusEnum, nullable=False, server_default=text("'pending'"))
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    assigned_to_role_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_review_items_entity: Mapped["TenantEntityReferences"] = relationship("TenantEntityReferences", viewonly=True, foreign_keys="[TenantReviewItems.tenant_id, TenantReviewItems.entity_reference_id]")
    rel_fk_review_items_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantReviewItems.tenant_id, TenantReviewItems.assigned_to_user_id]")
    rel_fk_review_items_role: Mapped["TenantRoles"] = relationship("TenantRoles", viewonly=True, foreign_keys="[TenantReviewItems.tenant_id, TenantReviewItems.assigned_to_role_id]")


class TenantReviewItemRelations(Base):
    __tablename__ = "review_item_relations"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'review_item_id'], ['tenant.review_items.tenant_id', 'tenant.review_items.id'], name='fk_review_item_relations_item'),
        ForeignKeyConstraint(['tenant_id', 'related_review_item_id'], ['tenant.review_items.tenant_id', 'tenant.review_items.id'], name='fk_review_item_relations_related'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    review_item_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    related_review_item_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    relation_key: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_review_item_relations_item: Mapped["TenantReviewItems"] = relationship("TenantReviewItems", viewonly=True, foreign_keys="[TenantReviewItemRelations.tenant_id, TenantReviewItemRelations.review_item_id]")
    rel_fk_review_item_relations_related: Mapped["TenantReviewItems"] = relationship("TenantReviewItems", viewonly=True, foreign_keys="[TenantReviewItemRelations.tenant_id, TenantReviewItemRelations.related_review_item_id]")


class TenantHumanDecisions(CreatedAtMixin, Base):
    __tablename__ = "human_decisions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_human_decisions_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'review_item_id'], ['tenant.review_items.tenant_id', 'tenant.review_items.id'], name='fk_human_decisions_item'),
        ForeignKeyConstraint(['tenant_id', 'decided_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_human_decisions_user'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    review_item_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    decision: Mapped[str] = mapped_column(ReviewItemStatusEnum, nullable=False)
    original_ai_output_text: Mapped[str] = mapped_column(Text(), nullable=False)
    modified_output_text: Mapped[str | None] = mapped_column(Text())
    reason_code: Mapped[str | None] = mapped_column(Text())
    free_text_comment: Mapped[str | None] = mapped_column(Text())
    decided_by_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    rel_fk_human_decisions_item: Mapped["TenantReviewItems"] = relationship("TenantReviewItems", viewonly=True, foreign_keys="[TenantHumanDecisions.tenant_id, TenantHumanDecisions.review_item_id]")
    rel_fk_human_decisions_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantHumanDecisions.tenant_id, TenantHumanDecisions.decided_by_user_id]")


class NotifNotificationTemplates(TimestampMixin, Base):
    __tablename__ = "notification_templates"
    __table_args__ = (
        UniqueConstraint('template_key', name='uq_notification_templates_key'),
        {"schema": "notif"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    template_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    category: Mapped[str] = mapped_column(NotifCategoryEnum, nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class NotifNotificationTemplateChannels(Base):
    __tablename__ = "notification_template_channels"
    __table_args__ = (
        ForeignKeyConstraint(['template_id'], ['notif.notification_templates.id'], name='fk_notification_template_channels_template'),
        {"schema": "notif"},
    )

    template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    channel: Mapped[str] = mapped_column(NotifChannelEnum, primary_key=True)

    rel_fk_notification_template_channels_template: Mapped["NotifNotificationTemplates"] = relationship("NotifNotificationTemplates", viewonly=True, foreign_keys="[NotifNotificationTemplateChannels.template_id]")


class NotifNotificationTemplateVariables(Base):
    __tablename__ = "notification_template_variables"
    __table_args__ = (
        ForeignKeyConstraint(['template_id'], ['notif.notification_templates.id'], name='fk_notification_template_variables_template'),
        {"schema": "notif"},
    )

    template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    variable_key: Mapped[str] = mapped_column(postgresql.CITEXT(), primary_key=True)
    is_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_notification_template_variables_template: Mapped["NotifNotificationTemplates"] = relationship("NotifNotificationTemplates", viewonly=True, foreign_keys="[NotifNotificationTemplateVariables.template_id]")


class NotifNotificationTemplateContents(CreatedAtMixin, Base):
    __tablename__ = "notification_template_contents"
    __table_args__ = (
        UniqueConstraint('template_id', 'channel', 'locale', name='uq_notification_template_contents_template_channel_locale'),
        ForeignKeyConstraint(['template_id'], ['notif.notification_templates.id'], name='fk_notification_template_contents_template'),
        {"schema": "notif"},
    )

    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(NotifChannelEnum, nullable=False)
    locale: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'en'"))
    subject: Mapped[str | None] = mapped_column(Text())
    body_text: Mapped[str] = mapped_column(Text(), nullable=False)
    body_html: Mapped[str | None] = mapped_column(Text())

    rel_fk_notification_template_contents_template: Mapped["NotifNotificationTemplates"] = relationship("NotifNotificationTemplates", viewonly=True, foreign_keys="[NotifNotificationTemplateContents.template_id]")


class TenantNotificationTemplateOverrides(TimestampMixin, Base):
    __tablename__ = "notification_template_overrides"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_notification_template_overrides_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_notification_template_overrides_tenant'),
        ForeignKeyConstraint(['template_id'], ['notif.notification_templates.id'], name='fk_notification_template_overrides_template'),
        ForeignKeyConstraint(['tenant_id', 'created_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_notification_template_overrides_user'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_notification_template_overrides_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantNotificationTemplateOverrides.tenant_id]")
    rel_fk_notification_template_overrides_template: Mapped["NotifNotificationTemplates"] = relationship("NotifNotificationTemplates", viewonly=True, foreign_keys="[TenantNotificationTemplateOverrides.template_id]")
    rel_fk_notification_template_overrides_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantNotificationTemplateOverrides.tenant_id, TenantNotificationTemplateOverrides.created_by_user_id]")


class TenantNotificationTemplateOverrideContents(CreatedAtMixin, Base):
    __tablename__ = "notification_template_override_contents"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_notification_template_override_contents_tenant_id'),
        UniqueConstraint('tenant_id', 'override_id', 'channel', 'locale', name='uq_notification_template_override_contents_locale'),
        ForeignKeyConstraint(['tenant_id', 'override_id'], ['tenant.notification_template_overrides.tenant_id', 'tenant.notification_template_overrides.id'], name='fk_notification_template_override_contents_override'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    override_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(NotifChannelEnum, nullable=False)
    locale: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'en'"))
    subject: Mapped[str | None] = mapped_column(Text())
    body_text: Mapped[str] = mapped_column(Text(), nullable=False)
    body_html: Mapped[str | None] = mapped_column(Text())

    rel_fk_notification_template_override_contents_override: Mapped["TenantNotificationTemplateOverrides"] = relationship("TenantNotificationTemplateOverrides", viewonly=True, foreign_keys="[TenantNotificationTemplateOverrideContents.tenant_id, TenantNotificationTemplateOverrideContents.override_id]")


class NotifNotificationEvents(CreatedAtMixin, Base):
    __tablename__ = "notification_events"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_notification_events_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_notification_events_tenant'),
        ForeignKeyConstraint(['template_id'], ['notif.notification_templates.id'], name='fk_notification_events_template'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_notification_events_user'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_notification_events_candidate'),
        ForeignKeyConstraint(['tenant_id', 'client_contact_id'], ['agency.client_contacts.tenant_id', 'agency.client_contacts.id'], name='fk_notification_events_contact'),
        {"schema": "notif"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    template_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    category: Mapped[str] = mapped_column(NotifCategoryEnum, nullable=False)
    recipient_type: Mapped[str] = mapped_column(NotifRecipientTypeEnum, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    client_contact_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_notification_events_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[NotifNotificationEvents.tenant_id]")
    rel_fk_notification_events_template: Mapped["NotifNotificationTemplates"] = relationship("NotifNotificationTemplates", viewonly=True, foreign_keys="[NotifNotificationEvents.template_id]")
    rel_fk_notification_events_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[NotifNotificationEvents.tenant_id, NotifNotificationEvents.user_id]")
    rel_fk_notification_events_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[NotifNotificationEvents.tenant_id, NotifNotificationEvents.candidate_id]")
    rel_fk_notification_events_contact: Mapped["AgencyClientContacts"] = relationship("AgencyClientContacts", viewonly=True, foreign_keys="[NotifNotificationEvents.tenant_id, NotifNotificationEvents.client_contact_id]")


class NotifNotificationEventVariables(Base):
    __tablename__ = "notification_event_variables"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'notification_event_id'], ['notif.notification_events.tenant_id', 'notif.notification_events.id'], name='fk_notification_event_variables_event'),
        {"schema": "notif"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    notification_event_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    variable_key: Mapped[str] = mapped_column(postgresql.CITEXT(), primary_key=True)
    variable_value: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_notification_event_variables_event: Mapped["NotifNotificationEvents"] = relationship("NotifNotificationEvents", viewonly=True, foreign_keys="[NotifNotificationEventVariables.tenant_id, NotifNotificationEventVariables.notification_event_id]")


class NotifNotificationDeliveries(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_notification_deliveries_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'notification_event_id'], ['notif.notification_events.tenant_id', 'notif.notification_events.id'], name='fk_notification_deliveries_event'),
        Index('idx_notification_deliveries_status', 'tenant_id', 'status', 'queued_at'),
        {"schema": "notif"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    notification_event_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(NotifChannelEnum, nullable=False)
    status: Mapped[str] = mapped_column(NotifDeliveryStatusEnum, nullable=False, server_default=text("'queued'"))
    provider_message_id: Mapped[str | None] = mapped_column(Text())
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text())

    rel_fk_notification_deliveries_event: Mapped["NotifNotificationEvents"] = relationship("NotifNotificationEvents", viewonly=True, foreign_keys="[NotifNotificationDeliveries.tenant_id, NotifNotificationDeliveries.notification_event_id]")


class NotifNotificationDeliveryAttempts(Base):
    __tablename__ = "notification_delivery_attempts"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_notification_delivery_attempts_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'notification_delivery_id'], ['notif.notification_deliveries.tenant_id', 'notif.notification_deliveries.id'], name='fk_notification_delivery_attempts_delivery'),
        CheckConstraint('attempt_number>0'),
        {"schema": "notif"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    notification_delivery_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer(), nullable=False)
    status: Mapped[str] = mapped_column(NotifDeliveryStatusEnum, nullable=False)
    response_status: Mapped[int | None] = mapped_column(Integer())
    response_body: Mapped[str | None] = mapped_column(Text())
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    rel_fk_notification_delivery_attempts_delivery: Mapped["NotifNotificationDeliveries"] = relationship("NotifNotificationDeliveries", viewonly=True, foreign_keys="[NotifNotificationDeliveryAttempts.tenant_id, NotifNotificationDeliveryAttempts.notification_delivery_id]")


class TenantNotificationPreferences(TimestampMixin, Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_notification_preferences_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_notification_preferences_tenant'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_notification_preferences_user'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_notification_preferences_candidate'),
        ForeignKeyConstraint(['tenant_id', 'client_contact_id'], ['agency.client_contacts.tenant_id', 'agency.client_contacts.id'], name='fk_notification_preferences_contact'),
        CheckConstraint('(user_id IS NOT NULL)::int+(candidate_id IS NOT NULL)::int+(client_contact_id IS NOT NULL)::int=1', name='chk_notification_preferences_one_subject'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    client_contact_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    category: Mapped[str] = mapped_column(NotifCategoryEnum, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_notification_preferences_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantNotificationPreferences.tenant_id]")
    rel_fk_notification_preferences_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantNotificationPreferences.tenant_id, TenantNotificationPreferences.user_id]")
    rel_fk_notification_preferences_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantNotificationPreferences.tenant_id, TenantNotificationPreferences.candidate_id]")
    rel_fk_notification_preferences_contact: Mapped["AgencyClientContacts"] = relationship("AgencyClientContacts", viewonly=True, foreign_keys="[TenantNotificationPreferences.tenant_id, TenantNotificationPreferences.client_contact_id]")


class TenantNotificationPreferenceChannels(Base):
    __tablename__ = "notification_preference_channels"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'notification_preference_id'], ['tenant.notification_preferences.tenant_id', 'tenant.notification_preferences.id'], name='fk_notification_preference_channels_pref'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    notification_preference_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    channel: Mapped[str] = mapped_column(NotifChannelEnum, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_notification_preference_channels_pref: Mapped["TenantNotificationPreferences"] = relationship("TenantNotificationPreferences", viewonly=True, foreign_keys="[TenantNotificationPreferenceChannels.tenant_id, TenantNotificationPreferenceChannels.notification_preference_id]")


class NotifSuppressionList(CreatedAtMixin, Base):
    __tablename__ = "suppression_list"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_suppression_list_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_suppression_list_tenant'),
        CheckConstraint('recipient_email IS NOT NULL OR recipient_phone_e164 IS NOT NULL', name='chk_suppression_list_recipient'),
        {"schema": "notif"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    recipient_email: Mapped[str | None] = mapped_column(postgresql.CITEXT())
    recipient_phone_e164: Mapped[str | None] = mapped_column(Text())
    channel: Mapped[str] = mapped_column(NotifChannelEnum, nullable=False)
    reason: Mapped[str] = mapped_column(SuppressionReasonEnum, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_suppression_list_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[NotifSuppressionList.tenant_id]")

