# db/models/corporate.py
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



class TenantHeadcountPlans(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "headcount_plans"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_headcount_plans_tenant_id'),
        UniqueConstraint('tenant_id', 'business_unit_id', 'role_family', 'fiscal_period', name='uq_headcount_plans_natural'),
        ForeignKeyConstraint(['tenant_id', 'business_unit_id'], ['tenant.business_units.tenant_id', 'tenant.business_units.id'], name='fk_headcount_plans_bu'),
        CheckConstraint('approved_count >= 0'),
        CheckConstraint('filled_count >= 0'),
        CheckConstraint("status IN ('draft','pending_approval','approved','closed','cancelled')"),
        CheckConstraint('filled_count <= approved_count', name='chk_headcount_plans_filled_lte_approved'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    business_unit_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    role_family: Mapped[str] = mapped_column(Text(), nullable=False)
    fiscal_period: Mapped[str] = mapped_column(Text(), nullable=False)
    approved_count: Mapped[int] = mapped_column(Integer(), nullable=False)
    filled_count: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    budget_amount: Mapped[Decimal | None] = mapped_column(PositiveMoneyDomain)
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False, server_default=text("'USD'"))
    cost_center: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'approved'"))

    rel_fk_headcount_plans_bu: Mapped["TenantBusinessUnits"] = relationship("TenantBusinessUnits", viewonly=True, foreign_keys="[TenantHeadcountPlans.tenant_id, TenantHeadcountPlans.business_unit_id]")


class TenantSalaryBenchmarks(CreatedAtMixin, Base):
    __tablename__ = "salary_benchmarks"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_salary_benchmarks_tenant_id'),
        UniqueConstraint('tenant_id', 'role_title', 'level_code', 'location', 'currency', 'as_of_date', name='uq_salary_benchmarks_natural'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_salary_benchmarks_tenant'),
        CheckConstraint('p25 <= p50 AND p50 <= p75 AND p75 <= p90', name='chk_salary_benchmarks_order'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    role_title: Mapped[str] = mapped_column(Text(), nullable=False)
    level_code: Mapped[str] = mapped_column(Text(), nullable=False)
    location: Mapped[str] = mapped_column(Text(), nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False)
    p25: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False)
    p50: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False)
    p75: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False)
    p90: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False)
    data_source: Mapped[str] = mapped_column(Text(), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date(), nullable=False)

    rel_fk_salary_benchmarks_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantSalaryBenchmarks.tenant_id]")


class TenantRequisitions(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "requisitions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_requisitions_tenant_id'),
        UniqueConstraint('tenant_id', 'requisition_number', name='uq_requisitions_number'),
        ForeignKeyConstraint(['tenant_id', 'business_unit_id'], ['tenant.business_units.tenant_id', 'tenant.business_units.id'], name='fk_requisitions_bu'),
        ForeignKeyConstraint(['tenant_id', 'headcount_plan_id'], ['tenant.headcount_plans.tenant_id', 'tenant.headcount_plans.id'], name='fk_requisitions_headcount'),
        ForeignKeyConstraint(['tenant_id', 'hiring_manager_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_requisitions_hiring_manager'),
        ForeignKeyConstraint(['tenant_id', 'recruiter_owner_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_requisitions_recruiter'),
        CheckConstraint('headcount_requested > 0'),
        CheckConstraint("priority IN ('low','normal','high','critical')"),
        CheckConstraint('(salary_min IS NULL AND salary_max IS NULL AND salary_currency IS NULL) OR (salary_min IS NOT NULL AND salary_max IS NOT NULL AND salary_currency IS NOT NULL AND salary_min <= salary_max)', name='chk_requisitions_salary'),
        CheckConstraint("status <> 'approved' OR approved_at IS NOT NULL", name='chk_requisitions_approved_at'),
        Index('idx_requisitions_tenant_status', 'tenant_id', 'status', postgresql_where=text('deleted_at IS NULL')),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    requisition_number: Mapped[str] = mapped_column(Text(), nullable=False)
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    business_unit_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    headcount_plan_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    hiring_manager_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    recruiter_owner_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    employment_type: Mapped[str] = mapped_column(EmploymentTypeEnum, nullable=False)
    headcount_type: Mapped[str] = mapped_column(HeadcountTypeEnum, nullable=False, server_default=text("'new'"))
    headcount_requested: Mapped[int] = mapped_column(Integer(), nullable=False)
    status: Mapped[str] = mapped_column(RequisitionStatusEnum, nullable=False, server_default=text("'draft'"))
    priority: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'normal'"))
    target_start_date: Mapped[date | None] = mapped_column(Date())
    salary_min: Mapped[Decimal | None] = mapped_column(PositiveMoneyDomain)
    salary_max: Mapped[Decimal | None] = mapped_column(PositiveMoneyDomain)
    salary_currency: Mapped[str | None] = mapped_column(CurrencyCodeDomain)
    level_code: Mapped[str | None] = mapped_column(Text())
    grade_code: Mapped[str | None] = mapped_column(Text())
    justification: Mapped[str | None] = mapped_column(Text())
    is_off_plan_exception: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_requisitions_bu: Mapped["TenantBusinessUnits"] = relationship("TenantBusinessUnits", viewonly=True, foreign_keys="[TenantRequisitions.tenant_id, TenantRequisitions.business_unit_id]")
    rel_fk_requisitions_headcount: Mapped["TenantHeadcountPlans"] = relationship("TenantHeadcountPlans", viewonly=True, foreign_keys="[TenantRequisitions.tenant_id, TenantRequisitions.headcount_plan_id]")
    rel_fk_requisitions_hiring_manager: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantRequisitions.tenant_id, TenantRequisitions.hiring_manager_id]")
    rel_fk_requisitions_recruiter: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantRequisitions.tenant_id, TenantRequisitions.recruiter_owner_id]")


class TenantRequisitionLocations(CreatedAtMixin, Base):
    __tablename__ = "requisition_locations"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_requisition_locations_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_requisition_locations_req'),
        CheckConstraint("work_mode IN ('onsite','hybrid','remote')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    requisition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    location_name: Mapped[str] = mapped_column(Text(), nullable=False)
    country_code: Mapped[str | None] = mapped_column(CHAR(2))
    region: Mapped[str | None] = mapped_column(Text())
    city: Mapped[str | None] = mapped_column(Text())
    work_mode: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'onsite'"))

    rel_fk_requisition_locations_req: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[TenantRequisitionLocations.tenant_id, TenantRequisitionLocations.requisition_id]")


class TenantRequisitionOpenings(TimestampMixin, Base):
    __tablename__ = "requisition_openings"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_requisition_openings_tenant_id'),
        UniqueConstraint('tenant_id', 'requisition_id', 'opening_number', name='uq_requisition_openings_number'),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_requisition_openings_req'),
        ForeignKeyConstraint(['tenant_id', 'hired_candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_requisition_openings_candidate'),
        CheckConstraint('opening_number > 0'),
        CheckConstraint("status IN ('open','filled','cancelled')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    requisition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    opening_number: Mapped[int] = mapped_column(Integer(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'open'"))
    hired_candidate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_requisition_openings_req: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[TenantRequisitionOpenings.tenant_id, TenantRequisitionOpenings.requisition_id]")
    rel_fk_requisition_openings_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantRequisitionOpenings.tenant_id, TenantRequisitionOpenings.hired_candidate_id]")


class TenantCompetencyTaxonomy(TimestampMixin, Base):
    __tablename__ = "competency_taxonomy"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_competency_taxonomy_tenant_id'),
        UniqueConstraint('tenant_id', 'competency_key', name='uq_competency_taxonomy_key'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_competency_taxonomy_tenant'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    competency_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    display_name: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_competency_taxonomy_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantCompetencyTaxonomy.tenant_id]")


class TenantJobDescriptions(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "job_descriptions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_job_descriptions_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_job_descriptions_req'),
        ForeignKeyConstraint(['tenant_id', 'approved_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_job_descriptions_approved_by'),
        CheckConstraint("generated_by IN ('ai','human','hybrid')"),
        CheckConstraint("status <> 'approved' OR (final_text IS NOT NULL AND approved_by_user_id IS NOT NULL AND approved_at IS NOT NULL)", name='chk_job_descriptions_approval'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    requisition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(JobDescriptionStatusEnum, nullable=False, server_default=text("'draft'"))
    draft_text: Mapped[str] = mapped_column(Text(), nullable=False)
    final_text: Mapped[str | None] = mapped_column(Text())
    generated_by: Mapped[str] = mapped_column(Text(), nullable=False)
    inclusive_language_score: Mapped[Decimal | None] = mapped_column(Percent0100Domain)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_job_descriptions_req: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[TenantJobDescriptions.tenant_id, TenantJobDescriptions.requisition_id]")
    rel_fk_job_descriptions_approved_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantJobDescriptions.tenant_id, TenantJobDescriptions.approved_by_user_id]")


class TenantJobDescriptionCompetencies(Base):
    __tablename__ = "job_description_competencies"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'job_description_id'], ['tenant.job_descriptions.tenant_id', 'tenant.job_descriptions.id'], name='fk_job_description_competencies_jd'),
        ForeignKeyConstraint(['tenant_id', 'competency_id'], ['tenant.competency_taxonomy.tenant_id', 'tenant.competency_taxonomy.id'], name='fk_job_description_competencies_comp'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    job_description_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    competency_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    competency_level: Mapped[str] = mapped_column(CompetencyLevelEnum, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_job_description_competencies_jd: Mapped["TenantJobDescriptions"] = relationship("TenantJobDescriptions", viewonly=True, foreign_keys="[TenantJobDescriptionCompetencies.tenant_id, TenantJobDescriptionCompetencies.job_description_id]")
    rel_fk_job_description_competencies_comp: Mapped["TenantCompetencyTaxonomy"] = relationship("TenantCompetencyTaxonomy", viewonly=True, foreign_keys="[TenantJobDescriptionCompetencies.tenant_id, TenantJobDescriptionCompetencies.competency_id]")


class TenantInclusiveLanguageFindings(CreatedAtMixin, Base):
    __tablename__ = "inclusive_language_findings"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_inclusive_language_findings_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'job_description_id'], ['tenant.job_descriptions.tenant_id', 'tenant.job_descriptions.id'], name='fk_inclusive_language_findings_jd'),
        CheckConstraint("severity IN ('low','medium','high')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    job_description_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    field_name: Mapped[str] = mapped_column(Text(), nullable=False)
    issue_text: Mapped[str] = mapped_column(Text(), nullable=False)
    severity: Mapped[str] = mapped_column(Text(), nullable=False)
    suggestion: Mapped[str | None] = mapped_column(Text())

    rel_fk_inclusive_language_findings_jd: Mapped["TenantJobDescriptions"] = relationship("TenantJobDescriptions", viewonly=True, foreign_keys="[TenantInclusiveLanguageFindings.tenant_id, TenantInclusiveLanguageFindings.job_description_id]")


class TenantRequisitionValidationResults(CreatedAtMixin, Base):
    __tablename__ = "requisition_validation_results"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_requisition_validation_results_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_requisition_validation_results_req'),
        CheckConstraint("overall_status IN ('pass','warning','fail')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    requisition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    model_name: Mapped[str | None] = mapped_column(Text())
    overall_status: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_requisition_validation_results_req: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[TenantRequisitionValidationResults.tenant_id, TenantRequisitionValidationResults.requisition_id]")


class TenantRequisitionValidationIssues(CreatedAtMixin, Base):
    __tablename__ = "requisition_validation_issues"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_requisition_validation_issues_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'validation_result_id'], ['tenant.requisition_validation_results.tenant_id', 'tenant.requisition_validation_results.id'], name='fk_requisition_validation_issues_result'),
        CheckConstraint("severity IN ('info','warning','error')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    validation_result_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    field_name: Mapped[str] = mapped_column(Text(), nullable=False)
    severity: Mapped[str] = mapped_column(Text(), nullable=False)
    suggestion: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_requisition_validation_issues_result: Mapped["TenantRequisitionValidationResults"] = relationship("TenantRequisitionValidationResults", viewonly=True, foreign_keys="[TenantRequisitionValidationIssues.tenant_id, TenantRequisitionValidationIssues.validation_result_id]")


class TenantPipelineStageDefinitions(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "pipeline_stage_definitions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_pipeline_stage_definitions_tenant_id'),
        Index('uq_pipeline_stage_definitions_key', 'tenant_id', text("COALESCE(requisition_id,'00000000-0000-0000-0000-000000000000'::uuid)"), 'stage_key', unique=True),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_pipeline_stage_definitions_req'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    requisition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    stage_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False)
    is_terminal: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_pipeline_stage_definitions_req: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[TenantPipelineStageDefinitions.tenant_id, TenantPipelineStageDefinitions.requisition_id]")


class TenantPipelineStageAutoActions(CreatedAtMixin, Base):
    __tablename__ = "pipeline_stage_auto_actions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_pipeline_stage_auto_actions_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'stage_definition_id'], ['tenant.pipeline_stage_definitions.tenant_id', 'tenant.pipeline_stage_definitions.id'], name='fk_pipeline_stage_auto_actions_stage'),
        CheckConstraint("action_type IN ('notify','ai_screen','schedule','webhook','create_task')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    stage_definition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    action_type: Mapped[str] = mapped_column(Text(), nullable=False)
    action_key: Mapped[str] = mapped_column(Text(), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_pipeline_stage_auto_actions_stage: Mapped["TenantPipelineStageDefinitions"] = relationship("TenantPipelineStageDefinitions", viewonly=True, foreign_keys="[TenantPipelineStageAutoActions.tenant_id, TenantPipelineStageAutoActions.stage_definition_id]")


class TenantApplications(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_applications_tenant_id'),
        UniqueConstraint('tenant_id', 'candidate_id', 'requisition_id', name='uq_applications_candidate_req'),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_applications_req'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_applications_candidate'),
        ForeignKeyConstraint(['tenant_id', 'current_stage_id'], ['tenant.pipeline_stage_definitions.tenant_id', 'tenant.pipeline_stage_definitions.id'], name='fk_applications_stage'),
        Index('idx_applications_tenant_req_status', 'tenant_id', 'requisition_id', 'status', postgresql_where=text('deleted_at IS NULL')),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    requisition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    current_stage_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    source: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(ApplicationStatusEnum, nullable=False, server_default=text("'applied'"))
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    rejected_reason: Mapped[str | None] = mapped_column(Text())
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_applications_req: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[TenantApplications.tenant_id, TenantApplications.requisition_id]")
    rel_fk_applications_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantApplications.tenant_id, TenantApplications.candidate_id]")
    rel_fk_applications_stage: Mapped["TenantPipelineStageDefinitions"] = relationship("TenantPipelineStageDefinitions", viewonly=True, foreign_keys="[TenantApplications.tenant_id, TenantApplications.current_stage_id]")


class TenantApplicationQuestions(CreatedAtMixin, Base):
    __tablename__ = "application_questions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_application_questions_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_application_questions_req'),
        CheckConstraint("answer_type IN ('text','number','boolean','date','single_select','multi_select')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    requisition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    question_text: Mapped[str] = mapped_column(Text(), nullable=False)
    answer_type: Mapped[str] = mapped_column(Text(), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_application_questions_req: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[TenantApplicationQuestions.tenant_id, TenantApplicationQuestions.requisition_id]")


class TenantApplicationAnswers(TimestampMixin, Base):
    __tablename__ = "application_answers"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_application_answers_tenant_id'),
        UniqueConstraint('tenant_id', 'application_id', 'question_id', name='uq_application_answers_question'),
        ForeignKeyConstraint(['tenant_id', 'application_id'], ['tenant.applications.tenant_id', 'tenant.applications.id'], name='fk_application_answers_application'),
        ForeignKeyConstraint(['tenant_id', 'question_id'], ['tenant.application_questions.tenant_id', 'tenant.application_questions.id'], name='fk_application_answers_question'),
        CheckConstraint('(CASE WHEN answer_text IS NULL THEN 0 ELSE 1 END)+(CASE WHEN answer_number IS NULL THEN 0 ELSE 1 END)+(CASE WHEN answer_bool IS NULL THEN 0 ELSE 1 END)+(CASE WHEN answer_date IS NULL THEN 0 ELSE 1 END)=1', name='chk_application_answers_one_value'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    application_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    answer_text: Mapped[str | None] = mapped_column(Text())
    answer_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    answer_bool: Mapped[bool | None] = mapped_column(Boolean())
    answer_date: Mapped[date | None] = mapped_column(Date())

    rel_fk_application_answers_application: Mapped["TenantApplications"] = relationship("TenantApplications", viewonly=True, foreign_keys="[TenantApplicationAnswers.tenant_id, TenantApplicationAnswers.application_id]")
    rel_fk_application_answers_question: Mapped["TenantApplicationQuestions"] = relationship("TenantApplicationQuestions", viewonly=True, foreign_keys="[TenantApplicationAnswers.tenant_id, TenantApplicationAnswers.question_id]")


class TenantApplicationStageHistory(CreatedAtMixin, Base):
    __tablename__ = "application_stage_history"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_application_stage_history_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'application_id'], ['tenant.applications.tenant_id', 'tenant.applications.id'], name='fk_application_stage_history_application'),
        ForeignKeyConstraint(['tenant_id', 'from_stage_id'], ['tenant.pipeline_stage_definitions.tenant_id', 'tenant.pipeline_stage_definitions.id'], name='fk_application_stage_history_from_stage'),
        ForeignKeyConstraint(['tenant_id', 'to_stage_id'], ['tenant.pipeline_stage_definitions.tenant_id', 'tenant.pipeline_stage_definitions.id'], name='fk_application_stage_history_to_stage'),
        ForeignKeyConstraint(['tenant_id', 'changed_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_application_stage_history_user'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    application_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    from_stage_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    to_stage_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    direction: Mapped[str] = mapped_column(StageDirectionEnum, nullable=False)
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    reason: Mapped[str | None] = mapped_column(Text())

    rel_fk_application_stage_history_application: Mapped["TenantApplications"] = relationship("TenantApplications", viewonly=True, foreign_keys="[TenantApplicationStageHistory.tenant_id, TenantApplicationStageHistory.application_id]")
    rel_fk_application_stage_history_from_stage: Mapped["TenantPipelineStageDefinitions"] = relationship("TenantPipelineStageDefinitions", viewonly=True, foreign_keys="[TenantApplicationStageHistory.tenant_id, TenantApplicationStageHistory.from_stage_id]")
    rel_fk_application_stage_history_to_stage: Mapped["TenantPipelineStageDefinitions"] = relationship("TenantPipelineStageDefinitions", viewonly=True, foreign_keys="[TenantApplicationStageHistory.tenant_id, TenantApplicationStageHistory.to_stage_id]")
    rel_fk_application_stage_history_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantApplicationStageHistory.tenant_id, TenantApplicationStageHistory.changed_by_user_id]")


class TenantInterviews(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "interviews"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_interviews_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'application_id'], ['tenant.applications.tenant_id', 'tenant.applications.id'], name='fk_interviews_application'),
        ForeignKeyConstraint(['tenant_id', 'created_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_interviews_created_by'),
        CheckConstraint('scheduled_end_at > scheduled_start_at', name='chk_interviews_schedule'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    application_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    interview_type: Mapped[str] = mapped_column(InterviewTypeEnum, nullable=False)
    status: Mapped[str] = mapped_column(InterviewStatusEnum, nullable=False, server_default=text("'scheduled'"))
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    scheduled_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(Text(), nullable=False)
    location: Mapped[str | None] = mapped_column(Text())
    meeting_url: Mapped[str | None] = mapped_column(Text())
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_interviews_application: Mapped["TenantApplications"] = relationship("TenantApplications", viewonly=True, foreign_keys="[TenantInterviews.tenant_id, TenantInterviews.application_id]")
    rel_fk_interviews_created_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantInterviews.tenant_id, TenantInterviews.created_by_user_id]")


class TenantInterviewPanelists(Base):
    __tablename__ = "interview_panelists"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'interview_id'], ['tenant.interviews.tenant_id', 'tenant.interviews.id'], name='fk_interview_panelists_interview'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_interview_panelists_user'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    interview_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    role_label: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'interviewer'"))
    is_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    response_status: Mapped[str] = mapped_column(ApprovalStatusEnum, nullable=False, server_default=text("'pending'"))

    rel_fk_interview_panelists_interview: Mapped["TenantInterviews"] = relationship("TenantInterviews", viewonly=True, foreign_keys="[TenantInterviewPanelists.tenant_id, TenantInterviewPanelists.interview_id]")
    rel_fk_interview_panelists_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantInterviewPanelists.tenant_id, TenantInterviewPanelists.user_id]")


class TenantScorecards(CreatedAtMixin, Base):
    __tablename__ = "scorecards"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_scorecards_tenant_id'),
        UniqueConstraint('tenant_id', 'interview_id', 'submitted_by_user_id', name='uq_scorecards_interview_user'),
        ForeignKeyConstraint(['tenant_id', 'interview_id'], ['tenant.interviews.tenant_id', 'tenant.interviews.id'], name='fk_scorecards_interview'),
        ForeignKeyConstraint(['tenant_id', 'submitted_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_scorecards_user'),
        CheckConstraint("recommendation IN ('strong_yes','yes','no','strong_no','hold')"),
        CheckConstraint('overall_rating BETWEEN 1 AND 5'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    interview_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    submitted_by_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    recommendation: Mapped[str] = mapped_column(Text(), nullable=False)
    overall_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    comments: Mapped[str | None] = mapped_column(Text())
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    rel_fk_scorecards_interview: Mapped["TenantInterviews"] = relationship("TenantInterviews", viewonly=True, foreign_keys="[TenantScorecards.tenant_id, TenantScorecards.interview_id]")
    rel_fk_scorecards_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantScorecards.tenant_id, TenantScorecards.submitted_by_user_id]")


class TenantScorecardCriteria(CreatedAtMixin, Base):
    __tablename__ = "scorecard_criteria"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_scorecard_criteria_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_scorecard_criteria_req'),
        ForeignKeyConstraint(['tenant_id', 'competency_id'], ['tenant.competency_taxonomy.tenant_id', 'tenant.competency_taxonomy.id'], name='fk_scorecard_criteria_comp'),
        CheckConstraint('weight > 0'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    requisition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    competency_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    criterion_name: Mapped[str] = mapped_column(Text(), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False, server_default=text('1'))
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_scorecard_criteria_req: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[TenantScorecardCriteria.tenant_id, TenantScorecardCriteria.requisition_id]")
    rel_fk_scorecard_criteria_comp: Mapped["TenantCompetencyTaxonomy"] = relationship("TenantCompetencyTaxonomy", viewonly=True, foreign_keys="[TenantScorecardCriteria.tenant_id, TenantScorecardCriteria.competency_id]")


class TenantScorecardRatings(Base):
    __tablename__ = "scorecard_ratings"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'scorecard_id'], ['tenant.scorecards.tenant_id', 'tenant.scorecards.id'], name='fk_scorecard_ratings_scorecard'),
        ForeignKeyConstraint(['tenant_id', 'criterion_id'], ['tenant.scorecard_criteria.tenant_id', 'tenant.scorecard_criteria.id'], name='fk_scorecard_ratings_criterion'),
        CheckConstraint('rating BETWEEN 1 AND 5'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    scorecard_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    criterion_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text())

    rel_fk_scorecard_ratings_scorecard: Mapped["TenantScorecards"] = relationship("TenantScorecards", viewonly=True, foreign_keys="[TenantScorecardRatings.tenant_id, TenantScorecardRatings.scorecard_id]")
    rel_fk_scorecard_ratings_criterion: Mapped["TenantScorecardCriteria"] = relationship("TenantScorecardCriteria", viewonly=True, foreign_keys="[TenantScorecardRatings.tenant_id, TenantScorecardRatings.criterion_id]")


class TenantOffers(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "offers"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_offers_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'application_id'], ['tenant.applications.tenant_id', 'tenant.applications.id'], name='fk_offers_application'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_offers_candidate'),
        ForeignKeyConstraint(['tenant_id', 'created_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_offers_created_by'),
        CheckConstraint("status <> 'accepted' OR accepted_at IS NOT NULL", name='chk_offers_accepted'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    application_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(OfferStatusEnum, nullable=False, server_default=text("'draft'"))
    currency: Mapped[str] = mapped_column(CurrencyCodeDomain, nullable=False)
    base_salary: Mapped[Decimal] = mapped_column(PositiveMoneyDomain, nullable=False)
    bonus_amount: Mapped[Decimal | None] = mapped_column(PositiveMoneyDomain)
    equity_text: Mapped[str | None] = mapped_column(Text())
    start_date: Mapped[date | None] = mapped_column(Date())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_offers_application: Mapped["TenantApplications"] = relationship("TenantApplications", viewonly=True, foreign_keys="[TenantOffers.tenant_id, TenantOffers.application_id]")
    rel_fk_offers_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantOffers.tenant_id, TenantOffers.candidate_id]")
    rel_fk_offers_created_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantOffers.tenant_id, TenantOffers.created_by_user_id]")


class TenantOfferApprovalSteps(TimestampMixin, Base):
    __tablename__ = "offer_approval_steps"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_offer_approval_steps_tenant_id'),
        UniqueConstraint('tenant_id', 'offer_id', 'step_order', name='uq_offer_approval_steps_order'),
        ForeignKeyConstraint(['tenant_id', 'offer_id'], ['tenant.offers.tenant_id', 'tenant.offers.id'], name='fk_offer_approval_steps_offer'),
        ForeignKeyConstraint(['tenant_id', 'approver_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_offer_approval_steps_user'),
        CheckConstraint('step_order>0'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    offer_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer(), nullable=False)
    approver_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(ApprovalStatusEnum, nullable=False, server_default=text("'pending'"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    comments: Mapped[str | None] = mapped_column(Text())

    rel_fk_offer_approval_steps_offer: Mapped["TenantOffers"] = relationship("TenantOffers", viewonly=True, foreign_keys="[TenantOfferApprovalSteps.tenant_id, TenantOfferApprovalSteps.offer_id]")
    rel_fk_offer_approval_steps_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantOfferApprovalSteps.tenant_id, TenantOfferApprovalSteps.approver_user_id]")


class TenantPreJoiningEngagements(TimestampMixin, Base):
    __tablename__ = "pre_joining_engagements"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_pre_joining_engagements_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'offer_id'], ['tenant.offers.tenant_id', 'tenant.offers.id'], name='fk_pre_joining_engagements_offer'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_pre_joining_engagements_candidate'),
        ForeignKeyConstraint(['tenant_id', 'owner_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_pre_joining_engagements_owner'),
        CheckConstraint("status IN ('active','completed','cancelled')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    offer_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    start_date: Mapped[date] = mapped_column(Date(), nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'active'"))

    rel_fk_pre_joining_engagements_offer: Mapped["TenantOffers"] = relationship("TenantOffers", viewonly=True, foreign_keys="[TenantPreJoiningEngagements.tenant_id, TenantPreJoiningEngagements.offer_id]")
    rel_fk_pre_joining_engagements_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantPreJoiningEngagements.tenant_id, TenantPreJoiningEngagements.candidate_id]")
    rel_fk_pre_joining_engagements_owner: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantPreJoiningEngagements.tenant_id, TenantPreJoiningEngagements.owner_user_id]")


class TenantPreJoiningTouchpoints(TimestampMixin, Base):
    __tablename__ = "pre_joining_touchpoints"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_pre_joining_touchpoints_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'engagement_id'], ['tenant.pre_joining_engagements.tenant_id', 'tenant.pre_joining_engagements.id'], name='fk_pre_joining_touchpoints_engagement'),
        CheckConstraint("status IN ('scheduled','sent','completed','cancelled','failed')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    engagement_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    touchpoint_type: Mapped[str] = mapped_column(Text(), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    channel: Mapped[str] = mapped_column(NotifChannelEnum, nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'scheduled'"))

    rel_fk_pre_joining_touchpoints_engagement: Mapped["TenantPreJoiningEngagements"] = relationship("TenantPreJoiningEngagements", viewonly=True, foreign_keys="[TenantPreJoiningTouchpoints.tenant_id, TenantPreJoiningTouchpoints.engagement_id]")


class TenantPreJoiningDocumentRequirements(CreatedAtMixin, Base):
    __tablename__ = "pre_joining_document_requirements"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_pre_joining_document_requirements_tenant_id'),
        UniqueConstraint('tenant_id', 'engagement_id', 'document_type', name='uq_pre_joining_document_requirements_type'),
        ForeignKeyConstraint(['tenant_id', 'engagement_id'], ['tenant.pre_joining_engagements.tenant_id', 'tenant.pre_joining_engagements.id'], name='fk_pre_joining_document_requirements_engagement'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    engagement_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    document_type: Mapped[str] = mapped_column(Text(), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_pre_joining_document_requirements_engagement: Mapped["TenantPreJoiningEngagements"] = relationship("TenantPreJoiningEngagements", viewonly=True, foreign_keys="[TenantPreJoiningDocumentRequirements.tenant_id, TenantPreJoiningDocumentRequirements.engagement_id]")


class TenantPreJoiningDocumentStatuses(TimestampMixin, Base):
    __tablename__ = "pre_joining_document_statuses"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_pre_joining_document_statuses_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'document_requirement_id'], ['tenant.pre_joining_document_requirements.tenant_id', 'tenant.pre_joining_document_requirements.id'], name='fk_pre_joining_document_statuses_requirement'),
        ForeignKeyConstraint(['tenant_id', 'candidate_document_id'], ['tenant.candidate_documents.tenant_id', 'tenant.candidate_documents.id'], name='fk_pre_joining_document_statuses_document'),
        ForeignKeyConstraint(['tenant_id', 'verified_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_pre_joining_document_statuses_verified_by'),
        CheckConstraint("status IN ('pending','submitted','verified','rejected','waived')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    document_requirement_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    candidate_document_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'pending'"))
    verified_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_pre_joining_document_statuses_requirement: Mapped["TenantPreJoiningDocumentRequirements"] = relationship("TenantPreJoiningDocumentRequirements", viewonly=True, foreign_keys="[TenantPreJoiningDocumentStatuses.tenant_id, TenantPreJoiningDocumentStatuses.document_requirement_id]")
    rel_fk_pre_joining_document_statuses_document: Mapped["TenantCandidateDocuments"] = relationship("TenantCandidateDocuments", viewonly=True, foreign_keys="[TenantPreJoiningDocumentStatuses.tenant_id, TenantPreJoiningDocumentStatuses.candidate_document_id]")
    rel_fk_pre_joining_document_statuses_verified_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantPreJoiningDocumentStatuses.tenant_id, TenantPreJoiningDocumentStatuses.verified_by_user_id]")


class TenantOnboardingTasks(TimestampMixin, Base):
    __tablename__ = "onboarding_tasks"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_onboarding_tasks_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'offer_id'], ['tenant.offers.tenant_id', 'tenant.offers.id'], name='fk_onboarding_tasks_offer'),
        ForeignKeyConstraint(['tenant_id', 'owner_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_onboarding_tasks_owner'),
        CheckConstraint("status IN ('open','in_progress','completed','cancelled')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    offer_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    task_key: Mapped[str] = mapped_column(Text(), nullable=False)
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'open'"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_onboarding_tasks_offer: Mapped["TenantOffers"] = relationship("TenantOffers", viewonly=True, foreign_keys="[TenantOnboardingTasks.tenant_id, TenantOnboardingTasks.offer_id]")
    rel_fk_onboarding_tasks_owner: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantOnboardingTasks.tenant_id, TenantOnboardingTasks.owner_user_id]")


class TenantJobBoardPostings(TimestampMixin, Base):
    __tablename__ = "job_board_postings"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_job_board_postings_tenant_id'),
        UniqueConstraint('tenant_id', 'job_board', 'external_posting_id', name='uq_job_board_postings_external'),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_job_board_postings_req'),
        CheckConstraint('view_count>=0'),
        CheckConstraint('application_count>=0'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    requisition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    connector_instance_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    job_board: Mapped[str] = mapped_column(Text(), nullable=False)
    external_posting_id: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(PostingStatusEnum, nullable=False, server_default=text("'pending'"))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    view_count: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    application_count: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_job_board_postings_req: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[TenantJobBoardPostings.tenant_id, TenantJobBoardPostings.requisition_id]")

