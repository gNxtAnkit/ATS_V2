# db/models/ai.py
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



class AiRecruiterPersonas(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "recruiter_personas"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_recruiter_personas_tenant_id'),
        UniqueConstraint('tenant_id', 'name', name='uq_recruiter_personas_name'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_recruiter_personas_tenant'),
        Index('uq_recruiter_personas_default', 'tenant_id', unique=True, postgresql_where=text('is_default AND deleted_at IS NULL')),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    default_tone: Mapped[str | None] = mapped_column(Text())
    autonomy_mode: Mapped[str] = mapped_column(AiAutonomyModeEnum, nullable=False, server_default=text("'human_approval_required'"))
    is_default: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_recruiter_personas_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[AiRecruiterPersonas.tenant_id]")


class AiPersonaLanguages(Base):
    __tablename__ = "persona_languages"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'persona_id'], ['ai.recruiter_personas.tenant_id', 'ai.recruiter_personas.id'], name='fk_persona_languages_persona'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    persona_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    locale: Mapped[str] = mapped_column(Text(), primary_key=True)

    rel_fk_persona_languages_persona: Mapped["AiRecruiterPersonas"] = relationship("AiRecruiterPersonas", viewonly=True, foreign_keys="[AiPersonaLanguages.tenant_id, AiPersonaLanguages.persona_id]")


class AiPersonaBannedTopics(Base):
    __tablename__ = "persona_banned_topics"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'persona_id'], ['ai.recruiter_personas.tenant_id', 'ai.recruiter_personas.id'], name='fk_persona_banned_topics_persona'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    persona_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    topic_key: Mapped[str] = mapped_column(Text(), primary_key=True)

    rel_fk_persona_banned_topics_persona: Mapped["AiRecruiterPersonas"] = relationship("AiRecruiterPersonas", viewonly=True, foreign_keys="[AiPersonaBannedTopics.tenant_id, AiPersonaBannedTopics.persona_id]")


class AiPersonaRequiredDisclosures(CreatedAtMixin, Base):
    __tablename__ = "persona_required_disclosures"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_persona_required_disclosures_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'persona_id'], ['ai.recruiter_personas.tenant_id', 'ai.recruiter_personas.id'], name='fk_persona_required_disclosures_persona'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    persona_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    disclosure_key: Mapped[str] = mapped_column(Text(), nullable=False)
    disclosure_text: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_persona_required_disclosures_persona: Mapped["AiRecruiterPersonas"] = relationship("AiRecruiterPersonas", viewonly=True, foreign_keys="[AiPersonaRequiredDisclosures.tenant_id, AiPersonaRequiredDisclosures.persona_id]")


class AiPersonaEscalationRules(CreatedAtMixin, Base):
    __tablename__ = "persona_escalation_rules"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_persona_escalation_rules_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'persona_id'], ['ai.recruiter_personas.tenant_id', 'ai.recruiter_personas.id'], name='fk_persona_escalation_rules_persona'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    persona_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    trigger_key: Mapped[str] = mapped_column(Text(), nullable=False)
    condition_key: Mapped[str] = mapped_column(Text(), nullable=False)
    action_key: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_persona_escalation_rules_persona: Mapped["AiRecruiterPersonas"] = relationship("AiRecruiterPersonas", viewonly=True, foreign_keys="[AiPersonaEscalationRules.tenant_id, AiPersonaEscalationRules.persona_id]")


class AiPersonaJurisdictionDisclosures(CreatedAtMixin, Base):
    __tablename__ = "persona_jurisdiction_disclosures"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_persona_jurisdiction_disclosures_tenant_id'),
        UniqueConstraint('tenant_id', 'persona_id', 'region', name='uq_persona_jurisdiction_disclosures_region'),
        ForeignKeyConstraint(['tenant_id', 'persona_id'], ['ai.recruiter_personas.tenant_id', 'ai.recruiter_personas.id'], name='fk_persona_jurisdiction_disclosures_persona'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    persona_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    region: Mapped[str] = mapped_column(RegionEnum, nullable=False)
    disclosure_text: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_persona_jurisdiction_disclosures_persona: Mapped["AiRecruiterPersonas"] = relationship("AiRecruiterPersonas", viewonly=True, foreign_keys="[AiPersonaJurisdictionDisclosures.tenant_id, AiPersonaJurisdictionDisclosures.persona_id]")


class AiAgentIdentities(TimestampMixin, Base):
    __tablename__ = "agent_identities"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_agent_identities_tenant_id'),
        UniqueConstraint('tenant_id', 'agent_key', name='uq_agent_identities_key'),
        ForeignKeyConstraint(['tenant_id', 'persona_id'], ['ai.recruiter_personas.tenant_id', 'ai.recruiter_personas.id'], name='fk_agent_identities_persona'),
        CheckConstraint("status IN('active','disabled','deleted')"),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    persona_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    agent_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    display_name: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'active'"))

    rel_fk_agent_identities_persona: Mapped["AiRecruiterPersonas"] = relationship("AiRecruiterPersonas", viewonly=True, foreign_keys="[AiAgentIdentities.tenant_id, AiAgentIdentities.persona_id]")


class AiAgentPermissions(Base):
    __tablename__ = "agent_permissions"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'agent_id'], ['ai.agent_identities.tenant_id', 'ai.agent_identities.id'], name='fk_agent_permissions_agent'),
        ForeignKeyConstraint(['tenant_id', 'permission_id'], ['tenant.permissions.tenant_id', 'tenant.permissions.id'], name='fk_agent_permissions_permission'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    rel_fk_agent_permissions_agent: Mapped["AiAgentIdentities"] = relationship("AiAgentIdentities", viewonly=True, foreign_keys="[AiAgentPermissions.tenant_id, AiAgentPermissions.agent_id]")
    rel_fk_agent_permissions_permission: Mapped["TenantPermissions"] = relationship("TenantPermissions", viewonly=True, foreign_keys="[AiAgentPermissions.tenant_id, AiAgentPermissions.permission_id]")


class AiAgentBusinessUnits(Base):
    __tablename__ = "agent_business_units"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'agent_id'], ['ai.agent_identities.tenant_id', 'ai.agent_identities.id'], name='fk_agent_business_units_agent'),
        ForeignKeyConstraint(['tenant_id', 'business_unit_id'], ['tenant.business_units.tenant_id', 'tenant.business_units.id'], name='fk_agent_business_units_bu'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    business_unit_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    rel_fk_agent_business_units_agent: Mapped["AiAgentIdentities"] = relationship("AiAgentIdentities", viewonly=True, foreign_keys="[AiAgentBusinessUnits.tenant_id, AiAgentBusinessUnits.agent_id]")
    rel_fk_agent_business_units_bu: Mapped["TenantBusinessUnits"] = relationship("TenantBusinessUnits", viewonly=True, foreign_keys="[AiAgentBusinessUnits.tenant_id, AiAgentBusinessUnits.business_unit_id]")


class AiPromptTemplates(TimestampMixin, Base):
    __tablename__ = "prompt_templates"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_prompt_templates_tenant_id'),
        UniqueConstraint('tenant_id', 'template_key', 'version', name='uq_prompt_templates_key_version'),
        ForeignKeyConstraint(['model_definition_id'], ['platform.ai_model_definitions.id'], name='fk_prompt_templates_model'),
        ForeignKeyConstraint(['tenant_id', 'created_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_prompt_templates_user'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    template_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    action_type: Mapped[str] = mapped_column(AiActionTypeEnum, nullable=False)
    version: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('1'))
    template_text: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(WfTemplateStatusEnum, nullable=False, server_default=text("'draft'"))
    model_definition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_prompt_templates_model: Mapped["PlatformAiModelDefinitions"] = relationship("PlatformAiModelDefinitions", viewonly=True, foreign_keys="[AiPromptTemplates.model_definition_id]")
    rel_fk_prompt_templates_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[AiPromptTemplates.tenant_id, AiPromptTemplates.created_by_user_id]")


class AiPromptTemplateVariables(Base):
    __tablename__ = "prompt_template_variables"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'prompt_template_id'], ['ai.prompt_templates.tenant_id', 'ai.prompt_templates.id'], name='fk_prompt_template_variables_template'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    prompt_template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    variable_key: Mapped[str] = mapped_column(postgresql.CITEXT(), primary_key=True)
    is_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_prompt_template_variables_template: Mapped["AiPromptTemplates"] = relationship("AiPromptTemplates", viewonly=True, foreign_keys="[AiPromptTemplateVariables.tenant_id, AiPromptTemplateVariables.prompt_template_id]")


class AiPromptTemplatePolicyFlags(Base):
    __tablename__ = "prompt_template_policy_flags"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'prompt_template_id'], ['ai.prompt_templates.tenant_id', 'ai.prompt_templates.id'], name='fk_prompt_template_policy_flags_template'),
        CheckConstraint("severity IN('low','medium','high','critical')"),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    prompt_template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    policy_key: Mapped[str] = mapped_column(Text(), primary_key=True)
    severity: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_prompt_template_policy_flags_template: Mapped["AiPromptTemplates"] = relationship("AiPromptTemplates", viewonly=True, foreign_keys="[AiPromptTemplatePolicyFlags.tenant_id, AiPromptTemplatePolicyFlags.prompt_template_id]")


class AiSourcingRuns(TimestampMixin, Base):
    __tablename__ = "sourcing_runs"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_sourcing_runs_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_sourcing_runs_requisition'),
        ForeignKeyConstraint(['tenant_id', 'mandate_id'], ['agency.mandates.tenant_id', 'agency.mandates.id'], name='fk_sourcing_runs_mandate'),
        ForeignKeyConstraint(['tenant_id', 'persona_id'], ['ai.recruiter_personas.tenant_id', 'ai.recruiter_personas.id'], name='fk_sourcing_runs_persona'),
        ForeignKeyConstraint(['tenant_id', 'started_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_sourcing_runs_user'),
        CheckConstraint('(requisition_id IS NOT NULL)::int + (mandate_id IS NOT NULL)::int = 1', name='chk_sourcing_runs_subject'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    requisition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    mandate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    persona_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    started_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False, server_default=text("'pending'"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_sourcing_runs_requisition: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[AiSourcingRuns.tenant_id, AiSourcingRuns.requisition_id]")
    rel_fk_sourcing_runs_mandate: Mapped["AgencyMandates"] = relationship("AgencyMandates", viewonly=True, foreign_keys="[AiSourcingRuns.tenant_id, AiSourcingRuns.mandate_id]")
    rel_fk_sourcing_runs_persona: Mapped["AiRecruiterPersonas"] = relationship("AiRecruiterPersonas", viewonly=True, foreign_keys="[AiSourcingRuns.tenant_id, AiSourcingRuns.persona_id]")
    rel_fk_sourcing_runs_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[AiSourcingRuns.tenant_id, AiSourcingRuns.started_by_user_id]")


class AiSourcingCriteria(Base):
    __tablename__ = "sourcing_criteria"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_sourcing_criteria_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'sourcing_run_id'], ['ai.sourcing_runs.tenant_id', 'ai.sourcing_runs.id'], name='fk_sourcing_criteria_run'),
        CheckConstraint('weight>0'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    sourcing_run_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    criterion_key: Mapped[str] = mapped_column(Text(), nullable=False)
    operator: Mapped[str] = mapped_column(ConditionOperatorEnum, nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text())
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    value_bool: Mapped[bool | None] = mapped_column(Boolean())
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False, server_default=text('1'))

    rel_fk_sourcing_criteria_run: Mapped["AiSourcingRuns"] = relationship("AiSourcingRuns", viewonly=True, foreign_keys="[AiSourcingCriteria.tenant_id, AiSourcingCriteria.sourcing_run_id]")


class AiSourcingSources(Base):
    __tablename__ = "sourcing_sources"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'sourcing_run_id'], ['ai.sourcing_runs.tenant_id', 'ai.sourcing_runs.id'], name='fk_sourcing_sources_run'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    sourcing_run_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    source_key: Mapped[str] = mapped_column(Text(), primary_key=True)

    rel_fk_sourcing_sources_run: Mapped["AiSourcingRuns"] = relationship("AiSourcingRuns", viewonly=True, foreign_keys="[AiSourcingSources.tenant_id, AiSourcingSources.sourcing_run_id]")


class AiMatchScores(CreatedAtMixin, Base):
    __tablename__ = "match_scores"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_match_scores_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'sourcing_run_id'], ['ai.sourcing_runs.tenant_id', 'ai.sourcing_runs.id'], name='fk_match_scores_run'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_match_scores_candidate'),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_match_scores_requisition'),
        ForeignKeyConstraint(['tenant_id', 'mandate_id'], ['agency.mandates.tenant_id', 'agency.mandates.id'], name='fk_match_scores_mandate'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    sourcing_run_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    requisition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    mandate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    score: Mapped[Decimal] = mapped_column(ConfidenceScoreDomain, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text())

    rel_fk_match_scores_run: Mapped["AiSourcingRuns"] = relationship("AiSourcingRuns", viewonly=True, foreign_keys="[AiMatchScores.tenant_id, AiMatchScores.sourcing_run_id]")
    rel_fk_match_scores_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[AiMatchScores.tenant_id, AiMatchScores.candidate_id]")
    rel_fk_match_scores_requisition: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[AiMatchScores.tenant_id, AiMatchScores.requisition_id]")
    rel_fk_match_scores_mandate: Mapped["AgencyMandates"] = relationship("AgencyMandates", viewonly=True, foreign_keys="[AiMatchScores.tenant_id, AiMatchScores.mandate_id]")


class AiMatchScoreCriteria(Base):
    __tablename__ = "match_score_criteria"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_match_score_criteria_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'match_score_id'], ['ai.match_scores.tenant_id', 'ai.match_scores.id'], name='fk_match_score_criteria_score'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    match_score_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    criterion_key: Mapped[str] = mapped_column(Text(), nullable=False)
    criterion_score: Mapped[Decimal] = mapped_column(ConfidenceScoreDomain, nullable=False)
    evidence_text: Mapped[str | None] = mapped_column(Text())

    rel_fk_match_score_criteria_score: Mapped["AiMatchScores"] = relationship("AiMatchScores", viewonly=True, foreign_keys="[AiMatchScoreCriteria.tenant_id, AiMatchScoreCriteria.match_score_id]")


class AiScreeningResults(CreatedAtMixin, Base):
    __tablename__ = "screening_results"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_screening_results_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'application_id'], ['tenant.applications.tenant_id', 'tenant.applications.id'], name='fk_screening_results_application'),
        ForeignKeyConstraint(['tenant_id', 'submittal_id'], ['agency.submittals.tenant_id', 'agency.submittals.id'], name='fk_screening_results_submittal'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_screening_results_candidate'),
        CheckConstraint("recommendation IN('advance','reject','hold','human_review')"),
        CheckConstraint('(application_id IS NOT NULL)::int + (submittal_id IS NOT NULL)::int <= 1', name='chk_screening_results_subject'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    application_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    submittal_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    overall_score: Mapped[Decimal] = mapped_column(ConfidenceScoreDomain, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text(), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(ConfidenceScoreDomain, nullable=False)
    reasoning_summary: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_screening_results_application: Mapped["TenantApplications"] = relationship("TenantApplications", viewonly=True, foreign_keys="[AiScreeningResults.tenant_id, AiScreeningResults.application_id]")
    rel_fk_screening_results_submittal: Mapped["AgencySubmittals"] = relationship("AgencySubmittals", viewonly=True, foreign_keys="[AiScreeningResults.tenant_id, AiScreeningResults.submittal_id]")
    rel_fk_screening_results_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[AiScreeningResults.tenant_id, AiScreeningResults.candidate_id]")


class AiScreeningCriteriaResults(Base):
    __tablename__ = "screening_criteria_results"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_screening_criteria_results_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'screening_result_id'], ['ai.screening_results.tenant_id', 'ai.screening_results.id'], name='fk_screening_criteria_results_screening'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    screening_result_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    criterion_key: Mapped[str] = mapped_column(Text(), nullable=False)
    met: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    score: Mapped[Decimal | None] = mapped_column(ConfidenceScoreDomain)
    evidence_text: Mapped[str | None] = mapped_column(Text())

    rel_fk_screening_criteria_results_screening: Mapped["AiScreeningResults"] = relationship("AiScreeningResults", viewonly=True, foreign_keys="[AiScreeningCriteriaResults.tenant_id, AiScreeningCriteriaResults.screening_result_id]")


class AiAiBiasFlags(CreatedAtMixin, Base):
    __tablename__ = "ai_bias_flags"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_ai_bias_flags_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'match_score_id'], ['ai.match_scores.tenant_id', 'ai.match_scores.id'], name='fk_ai_bias_flags_match'),
        ForeignKeyConstraint(['tenant_id', 'screening_result_id'], ['ai.screening_results.tenant_id', 'ai.screening_results.id'], name='fk_ai_bias_flags_screening'),
        CheckConstraint("severity IN('low','medium','high','critical')"),
        CheckConstraint('(match_score_id IS NOT NULL)::int+(screening_result_id IS NOT NULL)::int+(interview_evaluation_id IS NOT NULL)::int=1', name='chk_ai_bias_flags_one_subject'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    match_score_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    screening_result_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    interview_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    flag_key: Mapped[str] = mapped_column(Text(), nullable=False)
    severity: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_ai_bias_flags_match: Mapped["AiMatchScores"] = relationship("AiMatchScores", viewonly=True, foreign_keys="[AiAiBiasFlags.tenant_id, AiAiBiasFlags.match_score_id]")
    rel_fk_ai_bias_flags_screening: Mapped["AiScreeningResults"] = relationship("AiScreeningResults", viewonly=True, foreign_keys="[AiAiBiasFlags.tenant_id, AiAiBiasFlags.screening_result_id]")


class AiAiConversations(TimestampMixin, Base):
    __tablename__ = "ai_conversations"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_ai_conversations_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_ai_conversations_candidate'),
        ForeignKeyConstraint(['tenant_id', 'application_id'], ['tenant.applications.tenant_id', 'tenant.applications.id'], name='fk_ai_conversations_application'),
        ForeignKeyConstraint(['tenant_id', 'submittal_id'], ['agency.submittals.tenant_id', 'agency.submittals.id'], name='fk_ai_conversations_submittal'),
        ForeignKeyConstraint(['tenant_id', 'persona_id'], ['ai.recruiter_personas.tenant_id', 'ai.recruiter_personas.id'], name='fk_ai_conversations_persona'),
        CheckConstraint("status IN('open','closed','escalated')"),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    application_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    submittal_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    persona_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    channel: Mapped[str] = mapped_column(NotifChannelEnum, nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'open'"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_ai_conversations_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[AiAiConversations.tenant_id, AiAiConversations.candidate_id]")
    rel_fk_ai_conversations_application: Mapped["TenantApplications"] = relationship("TenantApplications", viewonly=True, foreign_keys="[AiAiConversations.tenant_id, AiAiConversations.application_id]")
    rel_fk_ai_conversations_submittal: Mapped["AgencySubmittals"] = relationship("AgencySubmittals", viewonly=True, foreign_keys="[AiAiConversations.tenant_id, AiAiConversations.submittal_id]")
    rel_fk_ai_conversations_persona: Mapped["AiRecruiterPersonas"] = relationship("AiRecruiterPersonas", viewonly=True, foreign_keys="[AiAiConversations.tenant_id, AiAiConversations.persona_id]")


class AiConversationMessages(CreatedAtMixin, Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_conversation_messages_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'conversation_id'], ['ai.ai_conversations.tenant_id', 'ai.ai_conversations.id'], name='fk_conversation_messages_conversation'),
        ForeignKeyConstraint(['tenant_id', 'sender_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_conversation_messages_user'),
        ForeignKeyConstraint(['model_definition_id'], ['platform.ai_model_definitions.id'], name='fk_conversation_messages_model'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    conversation_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    sender_type: Mapped[str] = mapped_column(AuditActorTypeEnum, nullable=False)
    sender_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    message_text: Mapped[str] = mapped_column(Text(), nullable=False)
    model_definition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    raw_model_response: Mapped[dict[str, Any] | None] = mapped_column(postgresql.JSONB())

    rel_fk_conversation_messages_conversation: Mapped["AiAiConversations"] = relationship("AiAiConversations", viewonly=True, foreign_keys="[AiConversationMessages.tenant_id, AiConversationMessages.conversation_id]")
    rel_fk_conversation_messages_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[AiConversationMessages.tenant_id, AiConversationMessages.sender_user_id]")
    rel_fk_conversation_messages_model: Mapped["PlatformAiModelDefinitions"] = relationship("PlatformAiModelDefinitions", viewonly=True, foreign_keys="[AiConversationMessages.model_definition_id]")


class AiConversationEscalationFlags(CreatedAtMixin, Base):
    __tablename__ = "conversation_escalation_flags"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_conversation_escalation_flags_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'conversation_id'], ['ai.ai_conversations.tenant_id', 'ai.ai_conversations.id'], name='fk_conversation_escalation_flags_conversation'),
        CheckConstraint("status IN('open','resolved','dismissed')"),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    conversation_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    flag_key: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'open'"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_conversation_escalation_flags_conversation: Mapped["AiAiConversations"] = relationship("AiAiConversations", viewonly=True, foreign_keys="[AiConversationEscalationFlags.tenant_id, AiConversationEscalationFlags.conversation_id]")


class AiSchedulingRequests(TimestampMixin, Base):
    __tablename__ = "scheduling_requests"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_scheduling_requests_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'application_id'], ['tenant.applications.tenant_id', 'tenant.applications.id'], name='fk_scheduling_requests_application'),
        ForeignKeyConstraint(['tenant_id', 'submittal_id'], ['agency.submittals.tenant_id', 'agency.submittals.id'], name='fk_scheduling_requests_submittal'),
        ForeignKeyConstraint(['tenant_id', 'requested_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_scheduling_requests_user'),
        CheckConstraint("status IN('pending','proposed','confirmed','cancelled','failed')"),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    application_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    submittal_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(Text(), nullable=False, server_default=text("'pending'"))

    rel_fk_scheduling_requests_application: Mapped["TenantApplications"] = relationship("TenantApplications", viewonly=True, foreign_keys="[AiSchedulingRequests.tenant_id, AiSchedulingRequests.application_id]")
    rel_fk_scheduling_requests_submittal: Mapped["AgencySubmittals"] = relationship("AgencySubmittals", viewonly=True, foreign_keys="[AiSchedulingRequests.tenant_id, AiSchedulingRequests.submittal_id]")
    rel_fk_scheduling_requests_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[AiSchedulingRequests.tenant_id, AiSchedulingRequests.requested_by_user_id]")


class AiSchedulingParticipants(Base):
    __tablename__ = "scheduling_participants"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_scheduling_participants_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'scheduling_request_id'], ['ai.scheduling_requests.tenant_id', 'ai.scheduling_requests.id'], name='fk_scheduling_participants_request'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_scheduling_participants_user'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_scheduling_participants_candidate'),
        ForeignKeyConstraint(['tenant_id', 'client_contact_id'], ['agency.client_contacts.tenant_id', 'agency.client_contacts.id'], name='fk_scheduling_participants_contact'),
        CheckConstraint('(user_id IS NOT NULL)::int+(candidate_id IS NOT NULL)::int+(client_contact_id IS NOT NULL)::int=1', name='chk_scheduling_participants_one_party'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    scheduling_request_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    client_contact_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    participant_role: Mapped[str] = mapped_column(Text(), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_scheduling_participants_request: Mapped["AiSchedulingRequests"] = relationship("AiSchedulingRequests", viewonly=True, foreign_keys="[AiSchedulingParticipants.tenant_id, AiSchedulingParticipants.scheduling_request_id]")
    rel_fk_scheduling_participants_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[AiSchedulingParticipants.tenant_id, AiSchedulingParticipants.user_id]")
    rel_fk_scheduling_participants_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[AiSchedulingParticipants.tenant_id, AiSchedulingParticipants.candidate_id]")
    rel_fk_scheduling_participants_contact: Mapped["AgencyClientContacts"] = relationship("AgencyClientContacts", viewonly=True, foreign_keys="[AiSchedulingParticipants.tenant_id, AiSchedulingParticipants.client_contact_id]")


class AiSchedulingProposedSlots(CreatedAtMixin, Base):
    __tablename__ = "scheduling_proposed_slots"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_scheduling_proposed_slots_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'scheduling_request_id'], ['ai.scheduling_requests.tenant_id', 'ai.scheduling_requests.id'], name='fk_scheduling_proposed_slots_request'),
        CheckConstraint('end_at>start_at', name='chk_scheduling_proposed_slots_time'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    scheduling_request_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(Text(), nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_scheduling_proposed_slots_request: Mapped["AiSchedulingRequests"] = relationship("AiSchedulingRequests", viewonly=True, foreign_keys="[AiSchedulingProposedSlots.tenant_id, AiSchedulingProposedSlots.scheduling_request_id]")


class AiSchedulingCalendarSyncStatuses(Base):
    __tablename__ = "scheduling_calendar_sync_statuses"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_scheduling_calendar_sync_statuses_tenant_id'),
        UniqueConstraint('tenant_id', 'scheduling_request_id', 'participant_id', name='uq_scheduling_calendar_sync_statuses_participant'),
        ForeignKeyConstraint(['tenant_id', 'scheduling_request_id'], ['ai.scheduling_requests.tenant_id', 'ai.scheduling_requests.id'], name='fk_scheduling_calendar_sync_statuses_request'),
        ForeignKeyConstraint(['tenant_id', 'participant_id'], ['ai.scheduling_participants.tenant_id', 'ai.scheduling_participants.id'], name='fk_scheduling_calendar_sync_statuses_participant'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    scheduling_request_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    participant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    connector_instance_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False, server_default=text("'pending'"))
    external_event_id: Mapped[str | None] = mapped_column(Text())
    error_message: Mapped[str | None] = mapped_column(Text())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    rel_fk_scheduling_calendar_sync_statuses_request: Mapped["AiSchedulingRequests"] = relationship("AiSchedulingRequests", viewonly=True, foreign_keys="[AiSchedulingCalendarSyncStatuses.tenant_id, AiSchedulingCalendarSyncStatuses.scheduling_request_id]")
    rel_fk_scheduling_calendar_sync_statuses_participant: Mapped["AiSchedulingParticipants"] = relationship("AiSchedulingParticipants", viewonly=True, foreign_keys="[AiSchedulingCalendarSyncStatuses.tenant_id, AiSchedulingCalendarSyncStatuses.participant_id]")


class AiInterviewSessions(TimestampMixin, Base):
    __tablename__ = "interview_sessions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_interview_sessions_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'interview_id'], ['tenant.interviews.tenant_id', 'tenant.interviews.id'], name='fk_interview_sessions_interview'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_interview_sessions_candidate'),
        ForeignKeyConstraint(['tenant_id', 'consent_record_id'], ['tenant.consent_records.tenant_id', 'tenant.consent_records.id'], name='fk_interview_sessions_consent'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    interview_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    mode: Mapped[str] = mapped_column(InterviewTypeEnum, nullable=False)
    status: Mapped[str] = mapped_column(AiSessionStatusEnum, nullable=False, server_default=text("'not_started'"))
    consent_record_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recording_uri: Mapped[str | None] = mapped_column(Text())
    transcript_uri: Mapped[str | None] = mapped_column(Text())
    accommodation_notes: Mapped[str | None] = mapped_column(Text())

    rel_fk_interview_sessions_interview: Mapped["TenantInterviews"] = relationship("TenantInterviews", viewonly=True, foreign_keys="[AiInterviewSessions.tenant_id, AiInterviewSessions.interview_id]")
    rel_fk_interview_sessions_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[AiInterviewSessions.tenant_id, AiInterviewSessions.candidate_id]")
    rel_fk_interview_sessions_consent: Mapped["TenantConsentRecords"] = relationship("TenantConsentRecords", viewonly=True, foreign_keys="[AiInterviewSessions.tenant_id, AiInterviewSessions.consent_record_id]")


class AiInterviewQuestionSets(TimestampMixin, Base):
    __tablename__ = "interview_question_sets"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_interview_question_sets_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_interview_question_sets_req'),
        ForeignKeyConstraint(['tenant_id', 'mandate_id'], ['agency.mandates.tenant_id', 'agency.mandates.id'], name='fk_interview_question_sets_mandate'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    requisition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    mandate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    version: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('1'))

    rel_fk_interview_question_sets_req: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[AiInterviewQuestionSets.tenant_id, AiInterviewQuestionSets.requisition_id]")
    rel_fk_interview_question_sets_mandate: Mapped["AgencyMandates"] = relationship("AgencyMandates", viewonly=True, foreign_keys="[AiInterviewQuestionSets.tenant_id, AiInterviewQuestionSets.mandate_id]")


class AiInterviewQuestions(CreatedAtMixin, Base):
    __tablename__ = "interview_questions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_interview_questions_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'question_set_id'], ['ai.interview_question_sets.tenant_id', 'ai.interview_question_sets.id'], name='fk_interview_questions_set'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    question_set_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    question_text: Mapped[str] = mapped_column(Text(), nullable=False)
    expected_answer_guide: Mapped[str | None] = mapped_column(Text())
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_interview_questions_set: Mapped["AiInterviewQuestionSets"] = relationship("AiInterviewQuestionSets", viewonly=True, foreign_keys="[AiInterviewQuestions.tenant_id, AiInterviewQuestions.question_set_id]")


class AiInterviewQuestionCompetencies(Base):
    __tablename__ = "interview_question_competencies"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'question_id'], ['ai.interview_questions.tenant_id', 'ai.interview_questions.id'], name='fk_interview_question_competencies_question'),
        ForeignKeyConstraint(['tenant_id', 'competency_id'], ['tenant.competency_taxonomy.tenant_id', 'tenant.competency_taxonomy.id'], name='fk_interview_question_competencies_comp'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    question_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    competency_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)

    rel_fk_interview_question_competencies_question: Mapped["AiInterviewQuestions"] = relationship("AiInterviewQuestions", viewonly=True, foreign_keys="[AiInterviewQuestionCompetencies.tenant_id, AiInterviewQuestionCompetencies.question_id]")
    rel_fk_interview_question_competencies_comp: Mapped["TenantCompetencyTaxonomy"] = relationship("TenantCompetencyTaxonomy", viewonly=True, foreign_keys="[AiInterviewQuestionCompetencies.tenant_id, AiInterviewQuestionCompetencies.competency_id]")


class AiInterviewResponses(CreatedAtMixin, Base):
    __tablename__ = "interview_responses"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_interview_responses_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'interview_session_id'], ['ai.interview_sessions.tenant_id', 'ai.interview_sessions.id'], name='fk_interview_responses_session'),
        ForeignKeyConstraint(['tenant_id', 'question_id'], ['ai.interview_questions.tenant_id', 'ai.interview_questions.id'], name='fk_interview_responses_question'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    interview_session_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    question_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    answer_text: Mapped[str | None] = mapped_column(Text())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confidence: Mapped[Decimal | None] = mapped_column(ConfidenceScoreDomain)

    rel_fk_interview_responses_session: Mapped["AiInterviewSessions"] = relationship("AiInterviewSessions", viewonly=True, foreign_keys="[AiInterviewResponses.tenant_id, AiInterviewResponses.interview_session_id]")
    rel_fk_interview_responses_question: Mapped["AiInterviewQuestions"] = relationship("AiInterviewQuestions", viewonly=True, foreign_keys="[AiInterviewResponses.tenant_id, AiInterviewResponses.question_id]")


class AiInterviewResponseMedia(CreatedAtMixin, Base):
    __tablename__ = "interview_response_media"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_interview_response_media_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'interview_response_id'], ['ai.interview_responses.tenant_id', 'ai.interview_responses.id'], name='fk_interview_response_media_response'),
        CheckConstraint("media_type IN('audio','video','image','transcript')"),
        CheckConstraint('duration_ms IS NULL OR duration_ms>=0'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    interview_response_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    media_type: Mapped[str] = mapped_column(Text(), nullable=False)
    storage_uri: Mapped[str] = mapped_column(Text(), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer())

    rel_fk_interview_response_media_response: Mapped["AiInterviewResponses"] = relationship("AiInterviewResponses", viewonly=True, foreign_keys="[AiInterviewResponseMedia.tenant_id, AiInterviewResponseMedia.interview_response_id]")


class AiInterviewEvaluations(CreatedAtMixin, Base):
    __tablename__ = "interview_evaluations"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_interview_evaluations_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'interview_session_id'], ['ai.interview_sessions.tenant_id', 'ai.interview_sessions.id'], name='fk_interview_evaluations_session'),
        CheckConstraint("recommendation IN('advance','reject','hold','human_review')"),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    interview_session_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    overall_score: Mapped[Decimal] = mapped_column(ConfidenceScoreDomain, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text(), nullable=False)
    reasoning_summary: Mapped[str] = mapped_column(Text(), nullable=False)
    raw_model_response: Mapped[dict[str, Any] | None] = mapped_column(postgresql.JSONB())

    rel_fk_interview_evaluations_session: Mapped["AiInterviewSessions"] = relationship("AiInterviewSessions", viewonly=True, foreign_keys="[AiInterviewEvaluations.tenant_id, AiInterviewEvaluations.interview_session_id]")


class AiInterviewEvaluationCompetencyScores(Base):
    __tablename__ = "interview_evaluation_competency_scores"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'interview_evaluation_id'], ['ai.interview_evaluations.tenant_id', 'ai.interview_evaluations.id'], name='fk_interview_evaluation_competency_scores_eval'),
        ForeignKeyConstraint(['tenant_id', 'competency_id'], ['tenant.competency_taxonomy.tenant_id', 'tenant.competency_taxonomy.id'], name='fk_interview_evaluation_competency_scores_comp'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    interview_evaluation_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    competency_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    score: Mapped[Decimal] = mapped_column(ConfidenceScoreDomain, nullable=False)
    evidence_text: Mapped[str | None] = mapped_column(Text())

    rel_fk_interview_evaluation_competency_scores_eval: Mapped["AiInterviewEvaluations"] = relationship("AiInterviewEvaluations", viewonly=True, foreign_keys="[AiInterviewEvaluationCompetencyScores.tenant_id, AiInterviewEvaluationCompetencyScores.interview_evaluation_id]")
    rel_fk_interview_evaluation_competency_scores_comp: Mapped["TenantCompetencyTaxonomy"] = relationship("TenantCompetencyTaxonomy", viewonly=True, foreign_keys="[AiInterviewEvaluationCompetencyScores.tenant_id, AiInterviewEvaluationCompetencyScores.competency_id]")


class AiInterviewEvaluationFlags(CreatedAtMixin, Base):
    __tablename__ = "interview_evaluation_flags"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_interview_evaluation_flags_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'interview_evaluation_id'], ['ai.interview_evaluations.tenant_id', 'ai.interview_evaluations.id'], name='fk_interview_evaluation_flags_eval'),
        CheckConstraint("severity IN('low','medium','high','critical')"),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    interview_evaluation_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    flag_key: Mapped[str] = mapped_column(Text(), nullable=False)
    severity: Mapped[str] = mapped_column(Text(), nullable=False)
    details: Mapped[str | None] = mapped_column(Text())

    rel_fk_interview_evaluation_flags_eval: Mapped["AiInterviewEvaluations"] = relationship("AiInterviewEvaluations", viewonly=True, foreign_keys="[AiInterviewEvaluationFlags.tenant_id, AiInterviewEvaluationFlags.interview_evaluation_id]")


class AiInterviewLowConfidenceSegments(CreatedAtMixin, Base):
    __tablename__ = "interview_low_confidence_segments"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_interview_low_confidence_segments_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'interview_evaluation_id'], ['ai.interview_evaluations.tenant_id', 'ai.interview_evaluations.id'], name='fk_interview_low_confidence_segments_eval'),
        CheckConstraint('start_ms>=0'),
        CheckConstraint('end_ms>start_ms'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    interview_evaluation_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer(), nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer(), nullable=False)
    reason: Mapped[str] = mapped_column(Text(), nullable=False)
    excluded_from_score: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_interview_low_confidence_segments_eval: Mapped["AiInterviewEvaluations"] = relationship("AiInterviewEvaluations", viewonly=True, foreign_keys="[AiInterviewLowConfidenceSegments.tenant_id, AiInterviewLowConfidenceSegments.interview_evaluation_id]")


class AiTenantTelephonyConfigs(TimestampMixin, Base):
    __tablename__ = "tenant_telephony_configs"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_tenant_telephony_configs_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_tenant_telephony_configs_tenant'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    provider: Mapped[str] = mapped_column(Text(), nullable=False)
    default_region: Mapped[str] = mapped_column(RegionEnum, nullable=False)
    recording_enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    transcription_enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_tenant_telephony_configs_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[AiTenantTelephonyConfigs.tenant_id]")


class AiTelephonyNumbers(CreatedAtMixin, Base):
    __tablename__ = "telephony_numbers"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_telephony_numbers_tenant_id'),
        UniqueConstraint('phone_number_e164', name='uq_telephony_numbers_number'),
        ForeignKeyConstraint(['tenant_id', 'telephony_config_id'], ['ai.tenant_telephony_configs.tenant_id', 'ai.tenant_telephony_configs.id'], name='fk_telephony_numbers_config'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    telephony_config_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    phone_number_e164: Mapped[str] = mapped_column(Text(), nullable=False)
    region: Mapped[str] = mapped_column(RegionEnum, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))

    rel_fk_telephony_numbers_config: Mapped["AiTenantTelephonyConfigs"] = relationship("AiTenantTelephonyConfigs", viewonly=True, foreign_keys="[AiTelephonyNumbers.tenant_id, AiTelephonyNumbers.telephony_config_id]")


class AiTelephonyRegionRoutes(CreatedAtMixin, Base):
    __tablename__ = "telephony_region_routes"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_telephony_region_routes_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'telephony_config_id'], ['ai.tenant_telephony_configs.tenant_id', 'ai.tenant_telephony_configs.id'], name='fk_telephony_region_routes_config'),
        CheckConstraint('priority>0'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    telephony_config_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    region: Mapped[str] = mapped_column(RegionEnum, nullable=False)
    infrastructure_endpoint: Mapped[str] = mapped_column(Text(), nullable=False)
    priority: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('1'))

    rel_fk_telephony_region_routes_config: Mapped["AiTenantTelephonyConfigs"] = relationship("AiTenantTelephonyConfigs", viewonly=True, foreign_keys="[AiTelephonyRegionRoutes.tenant_id, AiTelephonyRegionRoutes.telephony_config_id]")


class AiCallRecords(TimestampMixin, Base):
    __tablename__ = "call_records"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_call_records_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'interview_session_id'], ['ai.interview_sessions.tenant_id', 'ai.interview_sessions.id'], name='fk_call_records_session'),
        ForeignKeyConstraint(['tenant_id', 'conversation_id'], ['ai.ai_conversations.tenant_id', 'ai.ai_conversations.id'], name='fk_call_records_conversation'),
        CheckConstraint('duration_seconds IS NULL OR duration_seconds>=0'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    interview_session_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    direction: Mapped[str] = mapped_column(CallDirectionEnum, nullable=False)
    from_number: Mapped[str | None] = mapped_column(Text())
    to_number: Mapped[str | None] = mapped_column(Text())
    provider_call_id: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(Text(), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer())
    recording_uri: Mapped[str | None] = mapped_column(Text())
    transcript_uri: Mapped[str | None] = mapped_column(Text())

    rel_fk_call_records_session: Mapped["AiInterviewSessions"] = relationship("AiInterviewSessions", viewonly=True, foreign_keys="[AiCallRecords.tenant_id, AiCallRecords.interview_session_id]")
    rel_fk_call_records_conversation: Mapped["AiAiConversations"] = relationship("AiAiConversations", viewonly=True, foreign_keys="[AiCallRecords.tenant_id, AiCallRecords.conversation_id]")


class AiCallRealTimeFlags(CreatedAtMixin, Base):
    __tablename__ = "call_real_time_flags"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_call_real_time_flags_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'call_record_id'], ['ai.call_records.tenant_id', 'ai.call_records.id'], name='fk_call_real_time_flags_call'),
        CheckConstraint('timestamp_ms>=0'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    call_record_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    flag_key: Mapped[str] = mapped_column(Text(), nullable=False)
    timestamp_ms: Mapped[int] = mapped_column(Integer(), nullable=False)
    details: Mapped[str | None] = mapped_column(Text())

    rel_fk_call_real_time_flags_call: Mapped["AiCallRecords"] = relationship("AiCallRecords", viewonly=True, foreign_keys="[AiCallRealTimeFlags.tenant_id, AiCallRealTimeFlags.call_record_id]")


class AiCallQualityMetrics(CreatedAtMixin, Base):
    __tablename__ = "call_quality_metrics"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_call_quality_metrics_tenant_id'),
        UniqueConstraint('tenant_id', 'call_record_id', 'metric_key', name='uq_call_quality_metrics_key'),
        ForeignKeyConstraint(['tenant_id', 'call_record_id'], ['ai.call_records.tenant_id', 'ai.call_records.id'], name='fk_call_quality_metrics_call'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    call_record_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    metric_key: Mapped[str] = mapped_column(Text(), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)

    rel_fk_call_quality_metrics_call: Mapped["AiCallRecords"] = relationship("AiCallRecords", viewonly=True, foreign_keys="[AiCallQualityMetrics.tenant_id, AiCallQualityMetrics.call_record_id]")


class AiLiveInterviewCalls(TimestampMixin, Base):
    __tablename__ = "live_interview_calls"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_live_interview_calls_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'call_record_id'], ['ai.call_records.tenant_id', 'ai.call_records.id'], name='fk_live_interview_calls_call'),
        ForeignKeyConstraint(['tenant_id', 'interviewer_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_live_interview_calls_interviewer'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    call_record_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    interviewer_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(InterviewStatusEnum, nullable=False)

    rel_fk_live_interview_calls_call: Mapped["AiCallRecords"] = relationship("AiCallRecords", viewonly=True, foreign_keys="[AiLiveInterviewCalls.tenant_id, AiLiveInterviewCalls.call_record_id]")
    rel_fk_live_interview_calls_interviewer: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[AiLiveInterviewCalls.tenant_id, AiLiveInterviewCalls.interviewer_user_id]")


class AiAiUsageEvents(Base):
    __tablename__ = "ai_usage_events"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', 'occurred_at', name='uq_ai_usage_events_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_ai_usage_events_tenant'),
        ForeignKeyConstraint(['model_definition_id'], ['platform.ai_model_definitions.id'], name='fk_ai_usage_events_model'),
        CheckConstraint('input_tokens>=0'),
        CheckConstraint('output_tokens>=0'),
        CheckConstraint('audio_seconds>=0'),
        Index('idx_ai_usage_events_tenant_time', 'tenant_id', text('occurred_at DESC')),
        {"schema": "ai", "postgresql_partition_by": "RANGE(occurred_at)"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    model_definition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    action_type: Mapped[str] = mapped_column(AiActionTypeEnum, nullable=False)
    source: Mapped[str] = mapped_column(UsageSourceEnum, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    output_tokens: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    audio_seconds: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    cost_amount: Mapped[Decimal | None] = mapped_column(PositiveMoneyDomain)
    currency: Mapped[str | None] = mapped_column(CurrencyCodeDomain, server_default=text("'USD'"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, server_default=text('now()'))

    rel_fk_ai_usage_events_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[AiAiUsageEvents.tenant_id]")
    rel_fk_ai_usage_events_model: Mapped["PlatformAiModelDefinitions"] = relationship("PlatformAiModelDefinitions", viewonly=True, foreign_keys="[AiAiUsageEvents.model_definition_id]")


class AiJoiningRiskScores(CreatedAtMixin, Base):
    __tablename__ = "joining_risk_scores"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_joining_risk_scores_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'engagement_id'], ['tenant.pre_joining_engagements.tenant_id', 'tenant.pre_joining_engagements.id'], name='fk_joining_risk_scores_engagement'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_joining_risk_scores_candidate'),
        CheckConstraint("risk_level IN('low','medium','high','critical')"),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    engagement_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(ConfidenceScoreDomain, nullable=False)
    risk_level: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_joining_risk_scores_engagement: Mapped["TenantPreJoiningEngagements"] = relationship("TenantPreJoiningEngagements", viewonly=True, foreign_keys="[AiJoiningRiskScores.tenant_id, AiJoiningRiskScores.engagement_id]")
    rel_fk_joining_risk_scores_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[AiJoiningRiskScores.tenant_id, AiJoiningRiskScores.candidate_id]")


class AiJoiningRiskFactors(CreatedAtMixin, Base):
    __tablename__ = "joining_risk_factors"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_joining_risk_factors_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'joining_risk_score_id'], ['ai.joining_risk_scores.tenant_id', 'ai.joining_risk_scores.id'], name='fk_joining_risk_factors_score'),
        CheckConstraint('weight>=0'),
        {"schema": "ai"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    joining_risk_score_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    factor_key: Mapped[str] = mapped_column(Text(), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    signal_value: Mapped[str | None] = mapped_column(Text())
    evidence_text: Mapped[str | None] = mapped_column(Text())

    rel_fk_joining_risk_factors_score: Mapped["AiJoiningRiskScores"] = relationship("AiJoiningRiskScores", viewonly=True, foreign_keys="[AiJoiningRiskFactors.tenant_id, AiJoiningRiskFactors.joining_risk_score_id]")

