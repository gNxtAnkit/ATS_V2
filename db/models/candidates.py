# db/models/candidates.py
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



class TenantCandidates(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "candidates"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_candidates_tenant_id'),
        UniqueConstraint('tenant_id', 'candidate_number', name='uq_candidates_tenant_number'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_candidates_tenant'),
        ForeignKeyConstraint(['tenant_id', 'merged_into_candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_candidates_merged_into'),
        CheckConstraint("status IN ('active','archived','merged','erasure_pending','erased')"),
        Index('uq_candidates_tenant_primary_email_active', 'tenant_id', 'primary_email', unique=True, postgresql_where=text('primary_email IS NOT NULL AND deleted_at IS NULL')),
        Index('idx_candidates_tenant_name_trgm', 'tenant_id', text('full_name gin_trgm_ops'), postgresql_using='gin'),
        Index('idx_candidates_tenant_email', 'tenant_id', 'primary_email', postgresql_where=text('deleted_at IS NULL')),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    candidate_number: Mapped[str] = mapped_column(Text(), nullable=False)
    full_name: Mapped[str] = mapped_column(Text(), nullable=False)
    primary_email: Mapped[str | None] = mapped_column(postgresql.CITEXT())
    primary_phone_e164: Mapped[str | None] = mapped_column(Text())
    current_title: Mapped[str | None] = mapped_column(Text())
    current_company: Mapped[str | None] = mapped_column(Text())
    current_location: Mapped[str | None] = mapped_column(Text())
    source: Mapped[str | None] = mapped_column(Text())
    profile_summary: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'active'"))
    merged_into_candidate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_candidates_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantCandidates.tenant_id]")
    rel_fk_candidates_merged_into: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantCandidates.tenant_id, TenantCandidates.merged_into_candidate_id]")


class TenantCandidateContacts(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "candidate_contacts"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_candidate_contacts_tenant_id'),
        UniqueConstraint('tenant_id', 'contact_type', 'normalized_value', name='uq_candidate_contacts_unique_value'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_candidate_contacts_candidate'),
        CheckConstraint("contact_type IN ('email','phone','linkedin','github','website','other')"),
        Index('uq_candidate_contacts_primary', 'tenant_id', 'candidate_id', 'contact_type', unique=True, postgresql_where=text('is_primary AND deleted_at IS NULL')),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    contact_type: Mapped[str] = mapped_column(Text(), nullable=False)
    contact_value: Mapped[str] = mapped_column(Text(), nullable=False)
    normalized_value: Mapped[str | None] = mapped_column(postgresql.CITEXT())
    is_primary: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    is_verified: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_candidate_contacts_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantCandidateContacts.tenant_id, TenantCandidateContacts.candidate_id]")


class TenantCandidateDocuments(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "candidate_documents"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_candidate_documents_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_candidate_documents_candidate'),
        ForeignKeyConstraint(['tenant_id', 'uploaded_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_candidate_documents_uploaded_by'),
        CheckConstraint("document_type IN ('resume','cover_letter','portfolio','assessment','offer','background_check','other')"),
        CheckConstraint('size_bytes >= 0'),
        Index('uq_candidate_documents_current_type', 'tenant_id', 'candidate_id', 'document_type', unique=True, postgresql_where=text('is_current AND deleted_at IS NULL')),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    document_type: Mapped[str] = mapped_column(Text(), nullable=False)
    file_name: Mapped[str] = mapped_column(Text(), nullable=False)
    storage_uri: Mapped[str] = mapped_column(Text(), nullable=False)
    mime_type: Mapped[str] = mapped_column(Text(), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_candidate_documents_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantCandidateDocuments.tenant_id, TenantCandidateDocuments.candidate_id]")
    rel_fk_candidate_documents_uploaded_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantCandidateDocuments.tenant_id, TenantCandidateDocuments.uploaded_by_user_id]")


class TenantConsentRecords(CreatedAtMixin, Base):
    __tablename__ = "consent_records"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_consent_records_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_consent_records_candidate'),
        CheckConstraint("status IN ('granted','withdrawn','expired','not_required')"),
        CheckConstraint("(status <> 'granted' OR granted_at IS NOT NULL) AND (status <> 'withdrawn' OR withdrawn_at IS NOT NULL)", name='chk_consent_records_status_dates'),
        Index('uq_consent_records_active', 'tenant_id', 'candidate_id', 'consent_type', unique=True, postgresql_where=text("status = 'granted'")),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    consent_type: Mapped[str] = mapped_column(ConsentTypeEnum, nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False)
    source: Mapped[str] = mapped_column(Text(), nullable=False)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locale: Mapped[str | None] = mapped_column(Text())
    policy_version: Mapped[str | None] = mapped_column(Text())
    evidence_uri: Mapped[str | None] = mapped_column(Text())

    rel_fk_consent_records_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantConsentRecords.tenant_id, TenantConsentRecords.candidate_id]")


class TenantDataSubjectRequests(TimestampMixin, Base):
    __tablename__ = "data_subject_requests"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_data_subject_requests_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_data_subject_requests_tenant'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_data_subject_requests_candidate'),
        CheckConstraint('due_at > submitted_at', name='chk_data_subject_requests_due'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    request_type: Mapped[str] = mapped_column(DsrTypeEnum, nullable=False)
    status: Mapped[str] = mapped_column(DsrStatusEnum, nullable=False, server_default=text("'submitted'"))
    requester_email: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(Text(), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text())
    completion_certificate_uri: Mapped[str | None] = mapped_column(Text())

    rel_fk_data_subject_requests_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantDataSubjectRequests.tenant_id]")
    rel_fk_data_subject_requests_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantDataSubjectRequests.tenant_id, TenantDataSubjectRequests.candidate_id]")


class TenantDataSubjectRequestTasks(TimestampMixin, Base):
    __tablename__ = "data_subject_request_tasks"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_data_subject_request_tasks_tenant_id'),
        UniqueConstraint('tenant_id', 'dsr_id', 'subsystem_key', name='uq_data_subject_request_tasks_subsystem'),
        ForeignKeyConstraint(['tenant_id', 'dsr_id'], ['tenant.data_subject_requests.tenant_id', 'tenant.data_subject_requests.id'], name='fk_data_subject_request_tasks_dsr'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    dsr_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    subsystem_key: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False, server_default=text("'pending'"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text())

    rel_fk_data_subject_request_tasks_dsr: Mapped["TenantDataSubjectRequests"] = relationship("TenantDataSubjectRequests", viewonly=True, foreign_keys="[TenantDataSubjectRequestTasks.tenant_id, TenantDataSubjectRequestTasks.dsr_id]")


class TenantTalentPools(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "talent_pools"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_talent_pools_tenant_id'),
        UniqueConstraint('tenant_id', 'name', name='uq_talent_pools_tenant_name'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_talent_pools_tenant'),
        ForeignKeyConstraint(['tenant_id', 'owner_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_talent_pools_owner'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    is_shared: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_talent_pools_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantTalentPools.tenant_id]")
    rel_fk_talent_pools_owner: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantTalentPools.tenant_id, TenantTalentPools.owner_user_id]")


class TenantTalentPoolEntries(CreatedAtMixin, Base):
    __tablename__ = "talent_pool_entries"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_talent_pool_entries_tenant_id'),
        UniqueConstraint('tenant_id', 'talent_pool_id', 'candidate_id', 'removed_at', name='uq_talent_pool_entries_active'),
        ForeignKeyConstraint(['tenant_id', 'talent_pool_id'], ['tenant.talent_pools.tenant_id', 'tenant.talent_pools.id'], name='fk_talent_pool_entries_pool'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_talent_pool_entries_candidate'),
        ForeignKeyConstraint(['tenant_id', 'added_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_talent_pool_entries_added_by'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    talent_pool_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    added_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text())

    rel_fk_talent_pool_entries_pool: Mapped["TenantTalentPools"] = relationship("TenantTalentPools", viewonly=True, foreign_keys="[TenantTalentPoolEntries.tenant_id, TenantTalentPoolEntries.talent_pool_id]")
    rel_fk_talent_pool_entries_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantTalentPoolEntries.tenant_id, TenantTalentPoolEntries.candidate_id]")
    rel_fk_talent_pool_entries_added_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantTalentPoolEntries.tenant_id, TenantTalentPoolEntries.added_by_user_id]")


class TenantTalentPoolEntryMandates(Base):
    __tablename__ = "talent_pool_entry_mandates"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'talent_pool_entry_id'], ['tenant.talent_pool_entries.tenant_id', 'tenant.talent_pool_entries.id'], name='fk_talent_pool_entry_mandates_entry'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    talent_pool_entry_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    mandate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    associated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    rel_fk_talent_pool_entry_mandates_entry: Mapped["TenantTalentPoolEntries"] = relationship("TenantTalentPoolEntries", viewonly=True, foreign_keys="[TenantTalentPoolEntryMandates.tenant_id, TenantTalentPoolEntryMandates.talent_pool_entry_id]")


class TenantCandidateSuppressions(CreatedAtMixin, Base):
    __tablename__ = "candidate_suppressions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_candidate_suppressions_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_candidate_suppressions_candidate'),
        ForeignKeyConstraint(['tenant_id', 'created_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_candidate_suppressions_created_by'),
        CheckConstraint('ends_at IS NULL OR ends_at > starts_at', name='chk_candidate_suppressions_period'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    suppression_reason: Mapped[str] = mapped_column(SuppressionReasonEnum, nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(Text(), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text())
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_candidate_suppressions_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantCandidateSuppressions.tenant_id, TenantCandidateSuppressions.candidate_id]")
    rel_fk_candidate_suppressions_created_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantCandidateSuppressions.tenant_id, TenantCandidateSuppressions.created_by_user_id]")


class TenantCandidateWorkHistory(TimestampMixin, Base):
    __tablename__ = "candidate_work_history"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_candidate_work_history_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_candidate_work_history_candidate'),
        CheckConstraint('end_date IS NULL OR start_date IS NULL OR end_date >= start_date', name='chk_candidate_work_history_dates'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    company_name: Mapped[str] = mapped_column(Text(), nullable=False)
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date())
    end_date: Mapped[date | None] = mapped_column(Date())
    is_current: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    description: Mapped[str | None] = mapped_column(Text())

    rel_fk_candidate_work_history_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantCandidateWorkHistory.tenant_id, TenantCandidateWorkHistory.candidate_id]")


class TenantSkillTaxonomy(TimestampMixin, Base):
    __tablename__ = "skill_taxonomy"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_skill_taxonomy_tenant_id'),
        UniqueConstraint('tenant_id', 'skill_key', name='uq_skill_taxonomy_tenant_key'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_skill_taxonomy_tenant'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    skill_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    display_name: Mapped[str] = mapped_column(Text(), nullable=False)
    category: Mapped[str | None] = mapped_column(Text())
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_skill_taxonomy_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantSkillTaxonomy.tenant_id]")


class TenantCandidateWorkHistorySkills(Base):
    __tablename__ = "candidate_work_history_skills"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'work_history_id'], ['tenant.candidate_work_history.tenant_id', 'tenant.candidate_work_history.id'], name='fk_candidate_work_history_skills_work'),
        ForeignKeyConstraint(['tenant_id', 'skill_id'], ['tenant.skill_taxonomy.tenant_id', 'tenant.skill_taxonomy.id'], name='fk_candidate_work_history_skills_skill'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    work_history_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    rel_fk_candidate_work_history_skills_work: Mapped["TenantCandidateWorkHistory"] = relationship("TenantCandidateWorkHistory", viewonly=True, foreign_keys="[TenantCandidateWorkHistorySkills.tenant_id, TenantCandidateWorkHistorySkills.work_history_id]")
    rel_fk_candidate_work_history_skills_skill: Mapped["TenantSkillTaxonomy"] = relationship("TenantSkillTaxonomy", viewonly=True, foreign_keys="[TenantCandidateWorkHistorySkills.tenant_id, TenantCandidateWorkHistorySkills.skill_id]")


class TenantCandidateEducation(TimestampMixin, Base):
    __tablename__ = "candidate_education"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_candidate_education_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_candidate_education_candidate'),
        CheckConstraint('end_date IS NULL OR start_date IS NULL OR end_date >= start_date', name='chk_candidate_education_dates'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    institution: Mapped[str] = mapped_column(Text(), nullable=False)
    degree: Mapped[str | None] = mapped_column(Text())
    field_of_study: Mapped[str | None] = mapped_column(Text())
    start_date: Mapped[date | None] = mapped_column(Date())
    end_date: Mapped[date | None] = mapped_column(Date())

    rel_fk_candidate_education_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantCandidateEducation.tenant_id, TenantCandidateEducation.candidate_id]")


class TenantCandidateSkills(CreatedAtMixin, Base):
    __tablename__ = "candidate_skills"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_candidate_skills_candidate'),
        ForeignKeyConstraint(['tenant_id', 'skill_id'], ['tenant.skill_taxonomy.tenant_id', 'tenant.skill_taxonomy.id'], name='fk_candidate_skills_skill'),
        CheckConstraint("proficiency IN ('beginner','intermediate','advanced','expert')"),
        CheckConstraint('years_experience IS NULL OR years_experience >= 0'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    proficiency: Mapped[str | None] = mapped_column(Text())
    years_experience: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    source: Mapped[str | None] = mapped_column(Text())

    rel_fk_candidate_skills_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantCandidateSkills.tenant_id, TenantCandidateSkills.candidate_id]")
    rel_fk_candidate_skills_skill: Mapped["TenantSkillTaxonomy"] = relationship("TenantSkillTaxonomy", viewonly=True, foreign_keys="[TenantCandidateSkills.tenant_id, TenantCandidateSkills.skill_id]")


class TenantCandidateEeoData(CreatedAtMixin, Base):
    __tablename__ = "candidate_eeo_data"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_candidate_eeo_data_candidate'),
        ForeignKeyConstraint(['tenant_id', 'consent_record_id'], ['tenant.consent_records.tenant_id', 'tenant.consent_records.id'], name='fk_candidate_eeo_data_consent'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    gender: Mapped[str | None] = mapped_column(Text())
    ethnicity: Mapped[str | None] = mapped_column(Text())
    disability_status: Mapped[str | None] = mapped_column(Text())
    veteran_status: Mapped[str | None] = mapped_column(Text())
    consent_record_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_candidate_eeo_data_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantCandidateEeoData.tenant_id, TenantCandidateEeoData.candidate_id]")
    rel_fk_candidate_eeo_data_consent: Mapped["TenantConsentRecords"] = relationship("TenantConsentRecords", viewonly=True, foreign_keys="[TenantCandidateEeoData.tenant_id, TenantCandidateEeoData.consent_record_id]")


class TenantCandidateDuplicateFlags(CreatedAtMixin, Base):
    __tablename__ = "candidate_duplicate_flags"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_candidate_duplicate_flags_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_candidate_duplicate_flags_candidate'),
        ForeignKeyConstraint(['tenant_id', 'possible_duplicate_candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_candidate_duplicate_flags_duplicate'),
        ForeignKeyConstraint(['tenant_id', 'resolved_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_candidate_duplicate_flags_resolved_by'),
        CheckConstraint("status IN ('open','confirmed_duplicate','dismissed','merged')"),
        CheckConstraint('candidate_id <> possible_duplicate_candidate_id', name='chk_candidate_duplicate_flags_not_self'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    possible_duplicate_candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    score: Mapped[Decimal] = mapped_column(ConfidenceScoreDomain, nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'open'"))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    resolved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_candidate_duplicate_flags_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantCandidateDuplicateFlags.tenant_id, TenantCandidateDuplicateFlags.candidate_id]")
    rel_fk_candidate_duplicate_flags_duplicate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantCandidateDuplicateFlags.tenant_id, TenantCandidateDuplicateFlags.possible_duplicate_candidate_id]")
    rel_fk_candidate_duplicate_flags_resolved_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantCandidateDuplicateFlags.tenant_id, TenantCandidateDuplicateFlags.resolved_by_user_id]")


class TenantCandidateDuplicateFlagReasons(Base):
    __tablename__ = "candidate_duplicate_flag_reasons"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'duplicate_flag_id'], ['tenant.candidate_duplicate_flags.tenant_id', 'tenant.candidate_duplicate_flags.id'], name='fk_candidate_duplicate_flag_reasons_flag'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    duplicate_flag_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    reason_key: Mapped[str] = mapped_column(Text(), primary_key=True)
    reason_detail: Mapped[str | None] = mapped_column(Text())

    rel_fk_candidate_duplicate_flag_reasons_flag: Mapped["TenantCandidateDuplicateFlags"] = relationship("TenantCandidateDuplicateFlags", viewonly=True, foreign_keys="[TenantCandidateDuplicateFlagReasons.tenant_id, TenantCandidateDuplicateFlagReasons.duplicate_flag_id]")

