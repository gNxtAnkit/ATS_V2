# db/models/agency.py
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



class AgencyClients(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_clients_tenant_id'),
        UniqueConstraint('tenant_id', 'name', name='uq_clients_tenant_name'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_clients_tenant'),
        ForeignKeyConstraint(['tenant_id', 'default_branding_id'], ['tenant.tenant_branding.tenant_id', 'tenant.tenant_branding.id'], name='fk_clients_branding'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    industry: Mapped[str | None] = mapped_column(Text())
    contract_type: Mapped[str] = mapped_column(ContractTypeEnum, nullable=False)
    status: Mapped[str] = mapped_column(ClientStatusEnum, nullable=False, server_default=text("'active'"))
    billing_terms: Mapped[str | None] = mapped_column(Text())
    default_branding_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_clients_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[AgencyClients.tenant_id]")
    rel_fk_clients_branding: Mapped["TenantTenantBranding"] = relationship("TenantTenantBranding", viewonly=True, foreign_keys="[AgencyClients.tenant_id, AgencyClients.default_branding_id]")


class AgencyClientDomains(CreatedAtMixin, Base):
    __tablename__ = "client_domains"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'client_id'], ['agency.clients.tenant_id', 'agency.clients.id'], name='fk_client_domains_client'),
        Index('uq_client_domains_one_primary', 'tenant_id', 'client_id', unique=True, postgresql_where=text('is_primary')),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    domain: Mapped[str] = mapped_column(postgresql.CITEXT(), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_client_domains_client: Mapped["AgencyClients"] = relationship("AgencyClients", viewonly=True, foreign_keys="[AgencyClientDomains.tenant_id, AgencyClientDomains.client_id]")


class AgencyClientContacts(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "client_contacts"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_client_contacts_tenant_id'),
        UniqueConstraint('tenant_id', 'client_id', 'email', name='uq_client_contacts_email'),
        ForeignKeyConstraint(['tenant_id', 'client_id'], ['agency.clients.tenant_id', 'agency.clients.id'], name='fk_client_contacts_client'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    client_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    email: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    phone_e164: Mapped[str | None] = mapped_column(Text())
    role_title: Mapped[str | None] = mapped_column(Text())
    portal_access_enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_client_contacts_client: Mapped["AgencyClients"] = relationship("AgencyClients", viewonly=True, foreign_keys="[AgencyClientContacts.tenant_id, AgencyClientContacts.client_id]")


class AgencyClientPortalUsers(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "client_portal_users"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_client_portal_users_tenant_id'),
        UniqueConstraint('tenant_id', 'contact_id', name='uq_client_portal_users_contact'),
        ForeignKeyConstraint(['tenant_id', 'client_id'], ['agency.clients.tenant_id', 'agency.clients.id'], name='fk_client_portal_users_client'),
        ForeignKeyConstraint(['tenant_id', 'contact_id'], ['agency.client_contacts.tenant_id', 'agency.client_contacts.id'], name='fk_client_portal_users_contact'),
        CheckConstraint("access_scope IN ('specific_mandates','all_active_mandates')"),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    client_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    email: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    access_scope: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(TenantUserStatusEnum, nullable=False, server_default=text("'invited'"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_client_portal_users_client: Mapped["AgencyClients"] = relationship("AgencyClients", viewonly=True, foreign_keys="[AgencyClientPortalUsers.tenant_id, AgencyClientPortalUsers.client_id]")
    rel_fk_client_portal_users_contact: Mapped["AgencyClientContacts"] = relationship("AgencyClientContacts", viewonly=True, foreign_keys="[AgencyClientPortalUsers.tenant_id, AgencyClientPortalUsers.contact_id]")


class AgencyExternalCompetingAgencies(CreatedAtMixin, Base):
    __tablename__ = "external_competing_agencies"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_external_competing_agencies_tenant_id'),
        UniqueConstraint('tenant_id', 'name', name='uq_external_competing_agencies_name'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_external_competing_agencies_tenant'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    domain: Mapped[str | None] = mapped_column(postgresql.CITEXT())

    rel_fk_external_competing_agencies_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[AgencyExternalCompetingAgencies.tenant_id]")


class AgencyCompetitorConflicts(CreatedAtMixin, Base):
    __tablename__ = "competitor_conflicts"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'client_a_id'], ['agency.clients.tenant_id', 'agency.clients.id'], name='fk_competitor_conflicts_a'),
        ForeignKeyConstraint(['tenant_id', 'client_b_id'], ['agency.clients.tenant_id', 'agency.clients.id'], name='fk_competitor_conflicts_b'),
        CheckConstraint('client_a_id < client_b_id', name='chk_competitor_conflicts_order'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    client_a_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    client_b_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    reason: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_competitor_conflicts_a: Mapped["AgencyClients"] = relationship("AgencyClients", viewonly=True, foreign_keys="[AgencyCompetitorConflicts.tenant_id, AgencyCompetitorConflicts.client_a_id]")
    rel_fk_competitor_conflicts_b: Mapped["AgencyClients"] = relationship("AgencyClients", viewonly=True, foreign_keys="[AgencyCompetitorConflicts.tenant_id, AgencyCompetitorConflicts.client_b_id]")


class AgencyMandates(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "mandates"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_mandates_tenant_id'),
        UniqueConstraint('tenant_id', 'mandate_number', name='uq_mandates_number'),
        ForeignKeyConstraint(['tenant_id', 'client_id'], ['agency.clients.tenant_id', 'agency.clients.id'], name='fk_mandates_client'),
        ForeignKeyConstraint(['tenant_id', 'owner_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_mandates_owner'),
        CheckConstraint('headcount > 0'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    client_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    mandate_number: Mapped[str] = mapped_column(Text(), nullable=False)
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    headcount: Mapped[int] = mapped_column(Integer(), nullable=False)
    fee_structure: Mapped[str] = mapped_column(FeeStructureEnum, nullable=False)
    exclusivity: Mapped[str] = mapped_column(ExclusivityEnum, nullable=False)
    target_fill_date: Mapped[date | None] = mapped_column(Date())
    status: Mapped[str] = mapped_column(MandateStatusEnum, nullable=False, server_default=text("'draft'"))
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancellation_reason: Mapped[str | None] = mapped_column(Text())

    rel_fk_mandates_client: Mapped["AgencyClients"] = relationship("AgencyClients", viewonly=True, foreign_keys="[AgencyMandates.tenant_id, AgencyMandates.client_id]")
    rel_fk_mandates_owner: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[AgencyMandates.tenant_id, AgencyMandates.owner_user_id]")


class AgencyMandateCompetingAgencies(CreatedAtMixin, Base):
    __tablename__ = "mandate_competing_agencies"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'mandate_id'], ['agency.mandates.tenant_id', 'agency.mandates.id'], name='fk_mandate_competing_agencies_mandate'),
        ForeignKeyConstraint(['tenant_id', 'external_competing_agency_id'], ['agency.external_competing_agencies.tenant_id', 'agency.external_competing_agencies.id'], name='fk_mandate_competing_agencies_agency'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    mandate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    external_competing_agency_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    risk_note: Mapped[str | None] = mapped_column(Text())

    rel_fk_mandate_competing_agencies_mandate: Mapped["AgencyMandates"] = relationship("AgencyMandates", viewonly=True, foreign_keys="[AgencyMandateCompetingAgencies.tenant_id, AgencyMandateCompetingAgencies.mandate_id]")
    rel_fk_mandate_competing_agencies_agency: Mapped["AgencyExternalCompetingAgencies"] = relationship("AgencyExternalCompetingAgencies", viewonly=True, foreign_keys="[AgencyMandateCompetingAgencies.tenant_id, AgencyMandateCompetingAgencies.external_competing_agency_id]")


class AgencyMandateFeeTerms(CreatedAtMixin, Base):
    __tablename__ = "mandate_fee_terms"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_mandate_fee_terms_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'mandate_id'], ['agency.mandates.tenant_id', 'agency.mandates.id'], name='fk_mandate_fee_terms_mandate'),
        CheckConstraint("due_event IS NULL OR due_event IN ('signing','shortlist','interview','placement','start_date','guarantee_clear')"),
        CheckConstraint("(term_type='percentage_of_salary' AND percentage IS NOT NULL AND flat_amount IS NULL) OR (term_type IN ('flat_fee','retainer','time_and_materials') AND flat_amount IS NOT NULL)", name='chk_mandate_fee_terms_amount'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    mandate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    term_type: Mapped[str] = mapped_column(FeeStructureEnum, nullable=False)
    percentage: Mapped[Decimal | None] = mapped_column(Percent0100Domain)
    flat_amount: Mapped[Decimal | None] = mapped_column(PositiveMoneyDomain)
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False, server_default=text("'USD'"))
    milestone_name: Mapped[str | None] = mapped_column(Text())
    milestone_order: Mapped[int | None] = mapped_column(Integer())
    due_event: Mapped[str | None] = mapped_column(Text())

    rel_fk_mandate_fee_terms_mandate: Mapped["AgencyMandates"] = relationship("AgencyMandates", viewonly=True, foreign_keys="[AgencyMandateFeeTerms.tenant_id, AgencyMandateFeeTerms.mandate_id]")


class AgencyRetainerMilestones(TimestampMixin, Base):
    __tablename__ = "retainer_milestones"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_retainer_milestones_tenant_id'),
        UniqueConstraint('tenant_id', 'mandate_id', 'milestone_order', name='uq_retainer_milestones_order'),
        ForeignKeyConstraint(['tenant_id', 'mandate_id'], ['agency.mandates.tenant_id', 'agency.mandates.id'], name='fk_retainer_milestones_mandate'),
        ForeignKeyConstraint(['tenant_id', 'fee_term_id'], ['agency.mandate_fee_terms.tenant_id', 'agency.mandate_fee_terms.id'], name='fk_retainer_milestones_fee_term'),
        CheckConstraint('milestone_order>0'),
        CheckConstraint("status IN ('pending','invoiced','paid','waived')"),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    mandate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    fee_term_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    milestone_order: Mapped[int] = mapped_column(Integer(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    trigger_event: Mapped[str] = mapped_column(Text(), nullable=False)
    amount: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False, server_default=text("'USD'"))
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'pending'"))
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_retainer_milestones_mandate: Mapped["AgencyMandates"] = relationship("AgencyMandates", viewonly=True, foreign_keys="[AgencyRetainerMilestones.tenant_id, AgencyRetainerMilestones.mandate_id]")
    rel_fk_retainer_milestones_fee_term: Mapped["AgencyMandateFeeTerms"] = relationship("AgencyMandateFeeTerms", viewonly=True, foreign_keys="[AgencyRetainerMilestones.tenant_id, AgencyRetainerMilestones.fee_term_id]")


class AgencyClientPortalUserMandates(CreatedAtMixin, Base):
    __tablename__ = "client_portal_user_mandates"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'portal_user_id'], ['agency.client_portal_users.tenant_id', 'agency.client_portal_users.id'], name='fk_client_portal_user_mandates_user'),
        ForeignKeyConstraint(['tenant_id', 'mandate_id'], ['agency.mandates.tenant_id', 'agency.mandates.id'], name='fk_client_portal_user_mandates_mandate'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    portal_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    mandate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    rel_fk_client_portal_user_mandates_user: Mapped["AgencyClientPortalUsers"] = relationship("AgencyClientPortalUsers", viewonly=True, foreign_keys="[AgencyClientPortalUserMandates.tenant_id, AgencyClientPortalUserMandates.portal_user_id]")
    rel_fk_client_portal_user_mandates_mandate: Mapped["AgencyMandates"] = relationship("AgencyMandates", viewonly=True, foreign_keys="[AgencyClientPortalUserMandates.tenant_id, AgencyClientPortalUserMandates.mandate_id]")


class AgencySubmittals(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "submittals"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_submittals_tenant_id'),
        UniqueConstraint('tenant_id', 'candidate_id', 'mandate_id', name='uq_submittals_candidate_mandate'),
        ForeignKeyConstraint(['tenant_id', 'mandate_id'], ['agency.mandates.tenant_id', 'agency.mandates.id'], name='fk_submittals_mandate'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_submittals_candidate'),
        ForeignKeyConstraint(['tenant_id', 'submitted_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_submittals_submitted_by'),
        CheckConstraint('competitor_conflict_overridden = false OR competitor_conflict_override_reason IS NOT NULL', name='chk_submittals_conflict_override'),
        Index('idx_submittals_tenant_mandate_status', 'tenant_id', 'mandate_id', 'status', postgresql_where=text('deleted_at IS NULL')),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    mandate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    submitted_by_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(SubmittalStatusEnum, nullable=False, server_default=text("'draft'"))
    direct_apply_attestation: Mapped[str | None] = mapped_column(Text())
    competitor_conflict_overridden: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    competitor_conflict_override_reason: Mapped[str | None] = mapped_column(Text())

    rel_fk_submittals_mandate: Mapped["AgencyMandates"] = relationship("AgencyMandates", viewonly=True, foreign_keys="[AgencySubmittals.tenant_id, AgencySubmittals.mandate_id]")
    rel_fk_submittals_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[AgencySubmittals.tenant_id, AgencySubmittals.candidate_id]")
    rel_fk_submittals_submitted_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[AgencySubmittals.tenant_id, AgencySubmittals.submitted_by_user_id]")


class AgencySubmittalProfileSnapshots(CreatedAtMixin, Base):
    __tablename__ = "submittal_profile_snapshots"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_submittal_profile_snapshots_tenant_id'),
        UniqueConstraint('tenant_id', 'submittal_id', 'snapshot_version', name='uq_submittal_profile_snapshots_version'),
        ForeignKeyConstraint(['tenant_id', 'submittal_id'], ['agency.submittals.tenant_id', 'agency.submittals.id'], name='fk_submittal_profile_snapshots_submittal'),
        ForeignKeyConstraint(['tenant_id', 'resume_document_id'], ['tenant.candidate_documents.tenant_id', 'tenant.candidate_documents.id'], name='fk_submittal_profile_snapshots_resume'),
        ForeignKeyConstraint(['tenant_id', 'created_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_submittal_profile_snapshots_created_by'),
        CheckConstraint('snapshot_version>0'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    submittal_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    snapshot_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    resume_document_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    rendered_profile_uri: Mapped[str | None] = mapped_column(Text())
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_submittal_profile_snapshots_submittal: Mapped["AgencySubmittals"] = relationship("AgencySubmittals", viewonly=True, foreign_keys="[AgencySubmittalProfileSnapshots.tenant_id, AgencySubmittalProfileSnapshots.submittal_id]")
    rel_fk_submittal_profile_snapshots_resume: Mapped["TenantCandidateDocuments"] = relationship("TenantCandidateDocuments", viewonly=True, foreign_keys="[AgencySubmittalProfileSnapshots.tenant_id, AgencySubmittalProfileSnapshots.resume_document_id]")
    rel_fk_submittal_profile_snapshots_created_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[AgencySubmittalProfileSnapshots.tenant_id, AgencySubmittalProfileSnapshots.created_by_user_id]")


class AgencySubmittalProfileFields(CreatedAtMixin, Base):
    __tablename__ = "submittal_profile_fields"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_submittal_profile_fields_tenant_id'),
        UniqueConstraint('tenant_id', 'snapshot_id', 'field_key', name='uq_submittal_profile_fields_key'),
        ForeignKeyConstraint(['tenant_id', 'snapshot_id'], ['agency.submittal_profile_snapshots.tenant_id', 'agency.submittal_profile_snapshots.id'], name='fk_submittal_profile_fields_snapshot'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    snapshot_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    field_key: Mapped[str] = mapped_column(Text(), nullable=False)
    field_value: Mapped[str | None] = mapped_column(Text())
    is_redacted: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    redaction_reason: Mapped[str | None] = mapped_column(Text())
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_submittal_profile_fields_snapshot: Mapped["AgencySubmittalProfileSnapshots"] = relationship("AgencySubmittalProfileSnapshots", viewonly=True, foreign_keys="[AgencySubmittalProfileFields.tenant_id, AgencySubmittalProfileFields.snapshot_id]")


class AgencySubmittalFeedback(CreatedAtMixin, Base):
    __tablename__ = "submittal_feedback"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_submittal_feedback_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'submittal_id'], ['agency.submittals.tenant_id', 'agency.submittals.id'], name='fk_submittal_feedback_submittal'),
        ForeignKeyConstraint(['tenant_id', 'client_contact_id'], ['agency.client_contacts.tenant_id', 'agency.client_contacts.id'], name='fk_submittal_feedback_contact'),
        CheckConstraint('rating BETWEEN 1 AND 5'),
        CheckConstraint("decision IN ('advance','reject','hold','needs_more_info')"),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    submittal_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    client_contact_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    decision: Mapped[str] = mapped_column(Text(), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text())

    rel_fk_submittal_feedback_submittal: Mapped["AgencySubmittals"] = relationship("AgencySubmittals", viewonly=True, foreign_keys="[AgencySubmittalFeedback.tenant_id, AgencySubmittalFeedback.submittal_id]")
    rel_fk_submittal_feedback_contact: Mapped["AgencyClientContacts"] = relationship("AgencyClientContacts", viewonly=True, foreign_keys="[AgencySubmittalFeedback.tenant_id, AgencySubmittalFeedback.client_contact_id]")


class AgencyPlacements(TimestampMixin, Base):
    __tablename__ = "placements"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_placements_tenant_id'),
        UniqueConstraint('tenant_id', 'submittal_id', name='uq_placements_submittal'),
        ForeignKeyConstraint(['tenant_id', 'submittal_id'], ['agency.submittals.tenant_id', 'agency.submittals.id'], name='fk_placements_submittal'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_placements_candidate'),
        ForeignKeyConstraint(['tenant_id', 'mandate_id'], ['agency.mandates.tenant_id', 'agency.mandates.id'], name='fk_placements_mandate'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    submittal_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    mandate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    start_date: Mapped[date | None] = mapped_column(Date())
    final_salary: Mapped[Decimal | None] = mapped_column(PositiveMoneyDomain)
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False, server_default=text("'USD'"))
    fee_amount: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False)
    guarantee_status: Mapped[str] = mapped_column(GuaranteeStatusEnum, nullable=False, server_default=text("'active'"))

    rel_fk_placements_submittal: Mapped["AgencySubmittals"] = relationship("AgencySubmittals", viewonly=True, foreign_keys="[AgencyPlacements.tenant_id, AgencyPlacements.submittal_id]")
    rel_fk_placements_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[AgencyPlacements.tenant_id, AgencyPlacements.candidate_id]")
    rel_fk_placements_mandate: Mapped["AgencyMandates"] = relationship("AgencyMandates", viewonly=True, foreign_keys="[AgencyPlacements.tenant_id, AgencyPlacements.mandate_id]")


class AgencyPlacementFeeTermSnapshots(Base):
    __tablename__ = "placement_fee_term_snapshots"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_placement_fee_term_snapshots_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'placement_id'], ['agency.placements.tenant_id', 'agency.placements.id'], name='fk_placement_fee_term_snapshots_placement'),
        ForeignKeyConstraint(['tenant_id', 'source_fee_term_id'], ['agency.mandate_fee_terms.tenant_id', 'agency.mandate_fee_terms.id'], name='fk_placement_fee_term_snapshots_source'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    placement_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    source_fee_term_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    term_type: Mapped[str] = mapped_column(FeeStructureEnum, nullable=False)
    percentage: Mapped[Decimal | None] = mapped_column(Percent0100Domain)
    flat_amount: Mapped[Decimal | None] = mapped_column(PositiveMoneyDomain)
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    rel_fk_placement_fee_term_snapshots_placement: Mapped["AgencyPlacements"] = relationship("AgencyPlacements", viewonly=True, foreign_keys="[AgencyPlacementFeeTermSnapshots.tenant_id, AgencyPlacementFeeTermSnapshots.placement_id]")
    rel_fk_placement_fee_term_snapshots_source: Mapped["AgencyMandateFeeTerms"] = relationship("AgencyMandateFeeTerms", viewonly=True, foreign_keys="[AgencyPlacementFeeTermSnapshots.tenant_id, AgencyPlacementFeeTermSnapshots.source_fee_term_id]")


class AgencyPlacementGuarantees(TimestampMixin, Base):
    __tablename__ = "placement_guarantees"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_placement_guarantees_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'placement_id'], ['agency.placements.tenant_id', 'agency.placements.id'], name='fk_placement_guarantees_placement'),
        CheckConstraint('guarantee_days>=0'),
        CheckConstraint('ends_at >= starts_at', name='chk_placement_guarantees_period'),
        {"schema": "agency"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    placement_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    guarantee_days: Mapped[int] = mapped_column(Integer(), nullable=False)
    starts_at: Mapped[date] = mapped_column(Date(), nullable=False)
    ends_at: Mapped[date] = mapped_column(Date(), nullable=False)
    status: Mapped[str] = mapped_column(GuaranteeStatusEnum, nullable=False, server_default=text("'active'"))

    rel_fk_placement_guarantees_placement: Mapped["AgencyPlacements"] = relationship("AgencyPlacements", viewonly=True, foreign_keys="[AgencyPlacementGuarantees.tenant_id, AgencyPlacementGuarantees.placement_id]")

