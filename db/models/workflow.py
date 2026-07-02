# db/models/workflow.py
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



class TenantEntityReferences(CreatedAtMixin, Base):
    __tablename__ = "entity_references"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_entity_references_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_entity_references_tenant'),
        ForeignKeyConstraint(['tenant_id', 'candidate_id'], ['tenant.candidates.tenant_id', 'tenant.candidates.id'], name='fk_entity_references_candidate'),
        ForeignKeyConstraint(['tenant_id', 'requisition_id'], ['tenant.requisitions.tenant_id', 'tenant.requisitions.id'], name='fk_entity_references_requisition'),
        ForeignKeyConstraint(['tenant_id', 'application_id'], ['tenant.applications.tenant_id', 'tenant.applications.id'], name='fk_entity_references_application'),
        ForeignKeyConstraint(['tenant_id', 'interview_id'], ['tenant.interviews.tenant_id', 'tenant.interviews.id'], name='fk_entity_references_interview'),
        ForeignKeyConstraint(['tenant_id', 'offer_id'], ['tenant.offers.tenant_id', 'tenant.offers.id'], name='fk_entity_references_offer'),
        ForeignKeyConstraint(['tenant_id', 'client_id'], ['agency.clients.tenant_id', 'agency.clients.id'], name='fk_entity_references_client'),
        ForeignKeyConstraint(['tenant_id', 'mandate_id'], ['agency.mandates.tenant_id', 'agency.mandates.id'], name='fk_entity_references_mandate'),
        ForeignKeyConstraint(['tenant_id', 'submittal_id'], ['agency.submittals.tenant_id', 'agency.submittals.id'], name='fk_entity_references_submittal'),
        ForeignKeyConstraint(['tenant_id', 'placement_id'], ['agency.placements.tenant_id', 'agency.placements.id'], name='fk_entity_references_placement'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    display_label: Mapped[str | None] = mapped_column(Text())
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    requisition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    application_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    interview_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    offer_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    client_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    mandate_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    submittal_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    placement_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_entity_references_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantEntityReferences.tenant_id]")
    rel_fk_entity_references_candidate: Mapped["TenantCandidates"] = relationship("TenantCandidates", viewonly=True, foreign_keys="[TenantEntityReferences.tenant_id, TenantEntityReferences.candidate_id]")
    rel_fk_entity_references_requisition: Mapped["TenantRequisitions"] = relationship("TenantRequisitions", viewonly=True, foreign_keys="[TenantEntityReferences.tenant_id, TenantEntityReferences.requisition_id]")
    rel_fk_entity_references_application: Mapped["TenantApplications"] = relationship("TenantApplications", viewonly=True, foreign_keys="[TenantEntityReferences.tenant_id, TenantEntityReferences.application_id]")
    rel_fk_entity_references_interview: Mapped["TenantInterviews"] = relationship("TenantInterviews", viewonly=True, foreign_keys="[TenantEntityReferences.tenant_id, TenantEntityReferences.interview_id]")
    rel_fk_entity_references_offer: Mapped["TenantOffers"] = relationship("TenantOffers", viewonly=True, foreign_keys="[TenantEntityReferences.tenant_id, TenantEntityReferences.offer_id]")
    rel_fk_entity_references_client: Mapped["AgencyClients"] = relationship("AgencyClients", viewonly=True, foreign_keys="[TenantEntityReferences.tenant_id, TenantEntityReferences.client_id]")
    rel_fk_entity_references_mandate: Mapped["AgencyMandates"] = relationship("AgencyMandates", viewonly=True, foreign_keys="[TenantEntityReferences.tenant_id, TenantEntityReferences.mandate_id]")
    rel_fk_entity_references_submittal: Mapped["AgencySubmittals"] = relationship("AgencySubmittals", viewonly=True, foreign_keys="[TenantEntityReferences.tenant_id, TenantEntityReferences.submittal_id]")
    rel_fk_entity_references_placement: Mapped["AgencyPlacements"] = relationship("AgencyPlacements", viewonly=True, foreign_keys="[TenantEntityReferences.tenant_id, TenantEntityReferences.placement_id]")


class TenantWorkflowTemplates(TimestampMixin, SoftDeleteMixin, LockVersionMixin, Base):
    __tablename__ = "workflow_templates"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_templates_tenant_id'),
        UniqueConstraint('tenant_id', 'template_key', 'version', name='uq_workflow_templates_key_version'),
        ForeignKeyConstraint(['tenant_id', 'owner_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_workflow_templates_owner'),
        CheckConstraint('version>0'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    template_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(WfTemplateStatusEnum, nullable=False, server_default=text("'draft'"))
    version: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('1'))
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_workflow_templates_owner: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantWorkflowTemplates.tenant_id, TenantWorkflowTemplates.owner_user_id]")


class TenantWorkflowTemplateValidationErrors(CreatedAtMixin, Base):
    __tablename__ = "workflow_template_validation_errors"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_template_validation_errors_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'workflow_template_id'], ['tenant.workflow_templates.tenant_id', 'tenant.workflow_templates.id'], name='fk_workflow_template_validation_errors_template'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    step_key: Mapped[str | None] = mapped_column(Text())
    error_code: Mapped[str] = mapped_column(Text(), nullable=False)
    error_message: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_workflow_template_validation_errors_template: Mapped["TenantWorkflowTemplates"] = relationship("TenantWorkflowTemplates", viewonly=True, foreign_keys="[TenantWorkflowTemplateValidationErrors.tenant_id, TenantWorkflowTemplateValidationErrors.workflow_template_id]")


class TenantWorkflowCanvasNodes(CreatedAtMixin, Base):
    __tablename__ = "workflow_canvas_nodes"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_canvas_nodes_tenant_id'),
        UniqueConstraint('tenant_id', 'workflow_template_id', 'node_key', name='uq_workflow_canvas_nodes_key'),
        ForeignKeyConstraint(['tenant_id', 'workflow_template_id'], ['tenant.workflow_templates.tenant_id', 'tenant.workflow_templates.id'], name='fk_workflow_canvas_nodes_template'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    node_key: Mapped[str] = mapped_column(Text(), nullable=False)
    step_type: Mapped[str] = mapped_column(WfStepTypeEnum, nullable=False)
    position_x: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    position_y: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    rel_fk_workflow_canvas_nodes_template: Mapped["TenantWorkflowTemplates"] = relationship("TenantWorkflowTemplates", viewonly=True, foreign_keys="[TenantWorkflowCanvasNodes.tenant_id, TenantWorkflowCanvasNodes.workflow_template_id]")


class TenantWorkflowCanvasEdges(CreatedAtMixin, Base):
    __tablename__ = "workflow_canvas_edges"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_canvas_edges_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'workflow_template_id'], ['tenant.workflow_templates.tenant_id', 'tenant.workflow_templates.id'], name='fk_workflow_canvas_edges_template'),
        ForeignKeyConstraint(['tenant_id', 'from_node_id'], ['tenant.workflow_canvas_nodes.tenant_id', 'tenant.workflow_canvas_nodes.id'], name='fk_workflow_canvas_edges_from'),
        ForeignKeyConstraint(['tenant_id', 'to_node_id'], ['tenant.workflow_canvas_nodes.tenant_id', 'tenant.workflow_canvas_nodes.id'], name='fk_workflow_canvas_edges_to'),
        CheckConstraint('from_node_id <> to_node_id', name='chk_workflow_canvas_edges_not_self'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    from_node_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    to_node_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    label: Mapped[str | None] = mapped_column(Text())

    rel_fk_workflow_canvas_edges_template: Mapped["TenantWorkflowTemplates"] = relationship("TenantWorkflowTemplates", viewonly=True, foreign_keys="[TenantWorkflowCanvasEdges.tenant_id, TenantWorkflowCanvasEdges.workflow_template_id]")
    rel_fk_workflow_canvas_edges_from: Mapped["TenantWorkflowCanvasNodes"] = relationship("TenantWorkflowCanvasNodes", viewonly=True, foreign_keys="[TenantWorkflowCanvasEdges.tenant_id, TenantWorkflowCanvasEdges.from_node_id]")
    rel_fk_workflow_canvas_edges_to: Mapped["TenantWorkflowCanvasNodes"] = relationship("TenantWorkflowCanvasNodes", viewonly=True, foreign_keys="[TenantWorkflowCanvasEdges.tenant_id, TenantWorkflowCanvasEdges.to_node_id]")


class TenantWorkflowSteps(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "workflow_steps"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_steps_tenant_id'),
        UniqueConstraint('tenant_id', 'workflow_template_id', 'step_key', name='uq_workflow_steps_key'),
        ForeignKeyConstraint(['tenant_id', 'workflow_template_id'], ['tenant.workflow_templates.tenant_id', 'tenant.workflow_templates.id'], name='fk_workflow_steps_template'),
        CheckConstraint('sla_minutes IS NULL OR sla_minutes>0'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    step_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    step_type: Mapped[str] = mapped_column(WfStepTypeEnum, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    sla_minutes: Mapped[int | None] = mapped_column(Integer())

    rel_fk_workflow_steps_template: Mapped["TenantWorkflowTemplates"] = relationship("TenantWorkflowTemplates", viewonly=True, foreign_keys="[TenantWorkflowSteps.tenant_id, TenantWorkflowSteps.workflow_template_id]")


class TenantWorkflowStepSettings(CreatedAtMixin, Base):
    __tablename__ = "workflow_step_settings"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_step_settings_tenant_id'),
        UniqueConstraint('tenant_id', 'workflow_step_id', 'setting_key', name='uq_workflow_step_settings_key'),
        ForeignKeyConstraint(['tenant_id', 'workflow_step_id'], ['tenant.workflow_steps.tenant_id', 'tenant.workflow_steps.id'], name='fk_workflow_step_settings_step'),
        CheckConstraint('(CASE WHEN value_text IS NULL THEN 0 ELSE 1 END)+(CASE WHEN value_number IS NULL THEN 0 ELSE 1 END)+(CASE WHEN value_bool IS NULL THEN 0 ELSE 1 END)+(CASE WHEN value_integer IS NULL THEN 0 ELSE 1 END)=1', name='chk_workflow_step_settings_one_value'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_step_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    setting_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text())
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    value_bool: Mapped[bool | None] = mapped_column(Boolean())
    value_integer: Mapped[int | None] = mapped_column(BigInteger())

    rel_fk_workflow_step_settings_step: Mapped["TenantWorkflowSteps"] = relationship("TenantWorkflowSteps", viewonly=True, foreign_keys="[TenantWorkflowStepSettings.tenant_id, TenantWorkflowStepSettings.workflow_step_id]")


class TenantWorkflowStepApprovalConfigs(Base):
    __tablename__ = "workflow_step_approval_configs"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'workflow_step_id'], ['tenant.workflow_steps.tenant_id', 'tenant.workflow_steps.id'], name='fk_workflow_step_approval_configs_step'),
        ForeignKeyConstraint(['tenant_id', 'approver_role_id'], ['tenant.roles.tenant_id', 'tenant.roles.id'], name='fk_workflow_step_approval_configs_role'),
        ForeignKeyConstraint(['tenant_id', 'approver_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_workflow_step_approval_configs_user'),
        CheckConstraint('org_hierarchy_levels IS NULL OR org_hierarchy_levels>0'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    workflow_step_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    resolution_mode: Mapped[str] = mapped_column(ApproverResolutionEnum, nullable=False)
    approver_role_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    approver_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    org_hierarchy_levels: Mapped[int | None] = mapped_column(Integer())
    allow_delegation: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))

    rel_fk_workflow_step_approval_configs_step: Mapped["TenantWorkflowSteps"] = relationship("TenantWorkflowSteps", viewonly=True, foreign_keys="[TenantWorkflowStepApprovalConfigs.tenant_id, TenantWorkflowStepApprovalConfigs.workflow_step_id]")
    rel_fk_workflow_step_approval_configs_role: Mapped["TenantRoles"] = relationship("TenantRoles", viewonly=True, foreign_keys="[TenantWorkflowStepApprovalConfigs.tenant_id, TenantWorkflowStepApprovalConfigs.approver_role_id]")
    rel_fk_workflow_step_approval_configs_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantWorkflowStepApprovalConfigs.tenant_id, TenantWorkflowStepApprovalConfigs.approver_user_id]")


class TenantWorkflowStepAiActionConfigs(Base):
    __tablename__ = "workflow_step_ai_action_configs"
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'workflow_step_id'], ['tenant.workflow_steps.tenant_id', 'tenant.workflow_steps.id'], name='fk_workflow_step_ai_action_configs_step'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    workflow_step_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True)
    action_type: Mapped[str] = mapped_column(AiActionTypeEnum, nullable=False)
    autonomy_mode: Mapped[str] = mapped_column(AiAutonomyModeEnum, nullable=False)
    confidence_threshold: Mapped[Decimal | None] = mapped_column(ConfidenceScoreDomain)

    rel_fk_workflow_step_ai_action_configs_step: Mapped["TenantWorkflowSteps"] = relationship("TenantWorkflowSteps", viewonly=True, foreign_keys="[TenantWorkflowStepAiActionConfigs.tenant_id, TenantWorkflowStepAiActionConfigs.workflow_step_id]")


class TenantWorkflowEscalationRules(CreatedAtMixin, Base):
    __tablename__ = "workflow_escalation_rules"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_escalation_rules_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'workflow_step_id'], ['tenant.workflow_steps.tenant_id', 'tenant.workflow_steps.id'], name='fk_workflow_escalation_rules_step'),
        ForeignKeyConstraint(['tenant_id', 'escalate_to_role_id'], ['tenant.roles.tenant_id', 'tenant.roles.id'], name='fk_workflow_escalation_rules_role'),
        ForeignKeyConstraint(['tenant_id', 'escalate_to_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_workflow_escalation_rules_user'),
        CheckConstraint('trigger_after_minutes>0'),
        CheckConstraint('escalate_to_role_id IS NOT NULL OR escalate_to_user_id IS NOT NULL', name='chk_workflow_escalation_rules_target'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_step_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    trigger_after_minutes: Mapped[int] = mapped_column(Integer(), nullable=False)
    escalate_to_role_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    escalate_to_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    notification_template_key: Mapped[str | None] = mapped_column(Text())

    rel_fk_workflow_escalation_rules_step: Mapped["TenantWorkflowSteps"] = relationship("TenantWorkflowSteps", viewonly=True, foreign_keys="[TenantWorkflowEscalationRules.tenant_id, TenantWorkflowEscalationRules.workflow_step_id]")
    rel_fk_workflow_escalation_rules_role: Mapped["TenantRoles"] = relationship("TenantRoles", viewonly=True, foreign_keys="[TenantWorkflowEscalationRules.tenant_id, TenantWorkflowEscalationRules.escalate_to_role_id]")
    rel_fk_workflow_escalation_rules_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantWorkflowEscalationRules.tenant_id, TenantWorkflowEscalationRules.escalate_to_user_id]")


class TenantWorkflowTransitions(CreatedAtMixin, Base):
    __tablename__ = "workflow_transitions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_transitions_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'workflow_template_id'], ['tenant.workflow_templates.tenant_id', 'tenant.workflow_templates.id'], name='fk_workflow_transitions_template'),
        ForeignKeyConstraint(['tenant_id', 'from_step_id'], ['tenant.workflow_steps.tenant_id', 'tenant.workflow_steps.id'], name='fk_workflow_transitions_from'),
        ForeignKeyConstraint(['tenant_id', 'to_step_id'], ['tenant.workflow_steps.tenant_id', 'tenant.workflow_steps.id'], name='fk_workflow_transitions_to'),
        CheckConstraint('from_step_id<>to_step_id', name='chk_workflow_transitions_not_self'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    from_step_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    to_step_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))

    rel_fk_workflow_transitions_template: Mapped["TenantWorkflowTemplates"] = relationship("TenantWorkflowTemplates", viewonly=True, foreign_keys="[TenantWorkflowTransitions.tenant_id, TenantWorkflowTransitions.workflow_template_id]")
    rel_fk_workflow_transitions_from: Mapped["TenantWorkflowSteps"] = relationship("TenantWorkflowSteps", viewonly=True, foreign_keys="[TenantWorkflowTransitions.tenant_id, TenantWorkflowTransitions.from_step_id]")
    rel_fk_workflow_transitions_to: Mapped["TenantWorkflowSteps"] = relationship("TenantWorkflowSteps", viewonly=True, foreign_keys="[TenantWorkflowTransitions.tenant_id, TenantWorkflowTransitions.to_step_id]")


class TenantWorkflowTransitionConditionGroups(CreatedAtMixin, Base):
    __tablename__ = "workflow_transition_condition_groups"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_transition_condition_groups_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'transition_id'], ['tenant.workflow_transitions.tenant_id', 'tenant.workflow_transitions.id'], name='fk_workflow_transition_condition_groups_transition'),
        CheckConstraint("group_operator IN('AND','OR')"),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    transition_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    group_operator: Mapped[str] = mapped_column(Text(), nullable=False)

    rel_fk_workflow_transition_condition_groups_transition: Mapped["TenantWorkflowTransitions"] = relationship("TenantWorkflowTransitions", viewonly=True, foreign_keys="[TenantWorkflowTransitionConditionGroups.tenant_id, TenantWorkflowTransitionConditionGroups.transition_id]")


class TenantWorkflowTransitionConditions(Base):
    __tablename__ = "workflow_transition_conditions"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_transition_conditions_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'condition_group_id'], ['tenant.workflow_transition_condition_groups.tenant_id', 'tenant.workflow_transition_condition_groups.id'], name='fk_workflow_transition_conditions_group'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    condition_group_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    field_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    operator: Mapped[str] = mapped_column(ConditionOperatorEnum, nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text())
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    value_bool: Mapped[bool | None] = mapped_column(Boolean())
    value_date: Mapped[date | None] = mapped_column(Date())

    rel_fk_workflow_transition_conditions_group: Mapped["TenantWorkflowTransitionConditionGroups"] = relationship("TenantWorkflowTransitionConditionGroups", viewonly=True, foreign_keys="[TenantWorkflowTransitionConditions.tenant_id, TenantWorkflowTransitionConditions.condition_group_id]")


class TenantWorkflowTemplateChangeLog(Base):
    __tablename__ = "workflow_template_change_log"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_template_change_log_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'workflow_template_id'], ['tenant.workflow_templates.tenant_id', 'tenant.workflow_templates.id'], name='fk_workflow_template_change_log_template'),
        ForeignKeyConstraint(['tenant_id', 'changed_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_workflow_template_change_log_user'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    change_reason: Mapped[str] = mapped_column(Text(), nullable=False)
    diff_summary: Mapped[dict[str, Any] | None] = mapped_column(postgresql.JSONB())
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    rel_fk_workflow_template_change_log_template: Mapped["TenantWorkflowTemplates"] = relationship("TenantWorkflowTemplates", viewonly=True, foreign_keys="[TenantWorkflowTemplateChangeLog.tenant_id, TenantWorkflowTemplateChangeLog.workflow_template_id]")
    rel_fk_workflow_template_change_log_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantWorkflowTemplateChangeLog.tenant_id, TenantWorkflowTemplateChangeLog.changed_by_user_id]")


class TenantWorkflowSimulationRuns(CreatedAtMixin, Base):
    __tablename__ = "workflow_simulation_runs"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_simulation_runs_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'workflow_template_id'], ['tenant.workflow_templates.tenant_id', 'tenant.workflow_templates.id'], name='fk_workflow_simulation_runs_template'),
        ForeignKeyConstraint(['tenant_id', 'entity_reference_id'], ['tenant.entity_references.tenant_id', 'tenant.entity_references.id'], name='fk_workflow_simulation_runs_entity'),
        ForeignKeyConstraint(['tenant_id', 'started_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_workflow_simulation_runs_user'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    entity_reference_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(SyncStatusEnum, nullable=False, server_default=text("'pending'"))
    started_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_workflow_simulation_runs_template: Mapped["TenantWorkflowTemplates"] = relationship("TenantWorkflowTemplates", viewonly=True, foreign_keys="[TenantWorkflowSimulationRuns.tenant_id, TenantWorkflowSimulationRuns.workflow_template_id]")
    rel_fk_workflow_simulation_runs_entity: Mapped["TenantEntityReferences"] = relationship("TenantEntityReferences", viewonly=True, foreign_keys="[TenantWorkflowSimulationRuns.tenant_id, TenantWorkflowSimulationRuns.entity_reference_id]")
    rel_fk_workflow_simulation_runs_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantWorkflowSimulationRuns.tenant_id, TenantWorkflowSimulationRuns.started_by_user_id]")


class TenantWorkflowSimulationSteps(CreatedAtMixin, Base):
    __tablename__ = "workflow_simulation_steps"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_simulation_steps_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'simulation_run_id'], ['tenant.workflow_simulation_runs.tenant_id', 'tenant.workflow_simulation_runs.id'], name='fk_workflow_simulation_steps_run'),
        ForeignKeyConstraint(['tenant_id', 'step_id'], ['tenant.workflow_steps.tenant_id', 'tenant.workflow_steps.id'], name='fk_workflow_simulation_steps_step'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    simulation_run_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    step_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    outcome: Mapped[str] = mapped_column(Text(), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False)

    rel_fk_workflow_simulation_steps_run: Mapped["TenantWorkflowSimulationRuns"] = relationship("TenantWorkflowSimulationRuns", viewonly=True, foreign_keys="[TenantWorkflowSimulationSteps.tenant_id, TenantWorkflowSimulationSteps.simulation_run_id]")
    rel_fk_workflow_simulation_steps_step: Mapped["TenantWorkflowSteps"] = relationship("TenantWorkflowSteps", viewonly=True, foreign_keys="[TenantWorkflowSimulationSteps.tenant_id, TenantWorkflowSimulationSteps.step_id]")


class TenantWorkflowInstances(TimestampMixin, LockVersionMixin, Base):
    __tablename__ = "workflow_instances"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_instances_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'workflow_template_id'], ['tenant.workflow_templates.tenant_id', 'tenant.workflow_templates.id'], name='fk_workflow_instances_template'),
        ForeignKeyConstraint(['tenant_id', 'entity_reference_id'], ['tenant.entity_references.tenant_id', 'tenant.entity_references.id'], name='fk_workflow_instances_entity'),
        ForeignKeyConstraint(['tenant_id', 'current_step_id'], ['tenant.workflow_steps.tenant_id', 'tenant.workflow_steps.id'], name='fk_workflow_instances_current_step'),
        ForeignKeyConstraint(['tenant_id', 'started_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_workflow_instances_started_by'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_template_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    entity_reference_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(WfInstanceStatusEnum, nullable=False, server_default=text("'running'"))
    current_step_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    started_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rel_fk_workflow_instances_template: Mapped["TenantWorkflowTemplates"] = relationship("TenantWorkflowTemplates", viewonly=True, foreign_keys="[TenantWorkflowInstances.tenant_id, TenantWorkflowInstances.workflow_template_id]")
    rel_fk_workflow_instances_entity: Mapped["TenantEntityReferences"] = relationship("TenantEntityReferences", viewonly=True, foreign_keys="[TenantWorkflowInstances.tenant_id, TenantWorkflowInstances.entity_reference_id]")
    rel_fk_workflow_instances_current_step: Mapped["TenantWorkflowSteps"] = relationship("TenantWorkflowSteps", viewonly=True, foreign_keys="[TenantWorkflowInstances.tenant_id, TenantWorkflowInstances.current_step_id]")
    rel_fk_workflow_instances_started_by: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantWorkflowInstances.tenant_id, TenantWorkflowInstances.started_by_user_id]")


class TenantWorkflowInstanceContextValues(Base):
    __tablename__ = "workflow_instance_context_values"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_instance_context_values_tenant_id'),
        UniqueConstraint('tenant_id', 'workflow_instance_id', 'context_key', name='uq_workflow_instance_context_values_key'),
        ForeignKeyConstraint(['tenant_id', 'workflow_instance_id'], ['tenant.workflow_instances.tenant_id', 'tenant.workflow_instances.id'], name='fk_workflow_instance_context_values_instance'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_instance_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    context_key: Mapped[str] = mapped_column(postgresql.CITEXT(), nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text())
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    value_bool: Mapped[bool | None] = mapped_column(Boolean())
    value_date: Mapped[date | None] = mapped_column(Date())
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    rel_fk_workflow_instance_context_values_instance: Mapped["TenantWorkflowInstances"] = relationship("TenantWorkflowInstances", viewonly=True, foreign_keys="[TenantWorkflowInstanceContextValues.tenant_id, TenantWorkflowInstanceContextValues.workflow_instance_id]")


class TenantWorkflowInstanceHistory(Base):
    __tablename__ = "workflow_instance_history"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_instance_history_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'workflow_instance_id'], ['tenant.workflow_instances.tenant_id', 'tenant.workflow_instances.id'], name='fk_workflow_instance_history_instance'),
        ForeignKeyConstraint(['tenant_id', 'from_step_id'], ['tenant.workflow_steps.tenant_id', 'tenant.workflow_steps.id'], name='fk_workflow_instance_history_from'),
        ForeignKeyConstraint(['tenant_id', 'to_step_id'], ['tenant.workflow_steps.tenant_id', 'tenant.workflow_steps.id'], name='fk_workflow_instance_history_to'),
        ForeignKeyConstraint(['tenant_id', 'actor_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_workflow_instance_history_actor'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_instance_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    from_step_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    to_step_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    action_key: Mapped[str] = mapped_column(Text(), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    comments: Mapped[str | None] = mapped_column(Text())

    rel_fk_workflow_instance_history_instance: Mapped["TenantWorkflowInstances"] = relationship("TenantWorkflowInstances", viewonly=True, foreign_keys="[TenantWorkflowInstanceHistory.tenant_id, TenantWorkflowInstanceHistory.workflow_instance_id]")
    rel_fk_workflow_instance_history_from: Mapped["TenantWorkflowSteps"] = relationship("TenantWorkflowSteps", viewonly=True, foreign_keys="[TenantWorkflowInstanceHistory.tenant_id, TenantWorkflowInstanceHistory.from_step_id]")
    rel_fk_workflow_instance_history_to: Mapped["TenantWorkflowSteps"] = relationship("TenantWorkflowSteps", viewonly=True, foreign_keys="[TenantWorkflowInstanceHistory.tenant_id, TenantWorkflowInstanceHistory.to_step_id]")
    rel_fk_workflow_instance_history_actor: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantWorkflowInstanceHistory.tenant_id, TenantWorkflowInstanceHistory.actor_user_id]")


class TenantWorkflowConditionEvaluations(Base):
    __tablename__ = "workflow_condition_evaluations"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_workflow_condition_evaluations_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'workflow_history_id'], ['tenant.workflow_instance_history.tenant_id', 'tenant.workflow_instance_history.id'], name='fk_workflow_condition_evaluations_history'),
        ForeignKeyConstraint(['tenant_id', 'condition_id'], ['tenant.workflow_transition_conditions.tenant_id', 'tenant.workflow_transition_conditions.id'], name='fk_workflow_condition_evaluations_condition'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_history_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    condition_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    result: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    actual_value: Mapped[str | None] = mapped_column(Text())
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    rel_fk_workflow_condition_evaluations_history: Mapped["TenantWorkflowInstanceHistory"] = relationship("TenantWorkflowInstanceHistory", viewonly=True, foreign_keys="[TenantWorkflowConditionEvaluations.tenant_id, TenantWorkflowConditionEvaluations.workflow_history_id]")
    rel_fk_workflow_condition_evaluations_condition: Mapped["TenantWorkflowTransitionConditions"] = relationship("TenantWorkflowTransitionConditions", viewonly=True, foreign_keys="[TenantWorkflowConditionEvaluations.tenant_id, TenantWorkflowConditionEvaluations.condition_id]")


class TenantApprovalTasks(TimestampMixin, LockVersionMixin, Base):
    __tablename__ = "approval_tasks"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_approval_tasks_tenant_id'),
        ForeignKeyConstraint(['tenant_id', 'workflow_instance_id'], ['tenant.workflow_instances.tenant_id', 'tenant.workflow_instances.id'], name='fk_approval_tasks_instance'),
        ForeignKeyConstraint(['tenant_id', 'entity_reference_id'], ['tenant.entity_references.tenant_id', 'tenant.entity_references.id'], name='fk_approval_tasks_entity'),
        ForeignKeyConstraint(['tenant_id', 'approver_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_approval_tasks_approver'),
        ForeignKeyConstraint(['tenant_id', 'delegated_from_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_approval_tasks_delegated_from'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    workflow_instance_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    entity_reference_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    approver_user_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    delegated_from_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(ApprovalStatusEnum, nullable=False, server_default=text("'pending'"))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_comment: Mapped[str | None] = mapped_column(Text())

    rel_fk_approval_tasks_instance: Mapped["TenantWorkflowInstances"] = relationship("TenantWorkflowInstances", viewonly=True, foreign_keys="[TenantApprovalTasks.tenant_id, TenantApprovalTasks.workflow_instance_id]")
    rel_fk_approval_tasks_entity: Mapped["TenantEntityReferences"] = relationship("TenantEntityReferences", viewonly=True, foreign_keys="[TenantApprovalTasks.tenant_id, TenantApprovalTasks.entity_reference_id]")
    rel_fk_approval_tasks_approver: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantApprovalTasks.tenant_id, TenantApprovalTasks.approver_user_id]")
    rel_fk_approval_tasks_delegated_from: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantApprovalTasks.tenant_id, TenantApprovalTasks.delegated_from_user_id]")


class TenantAiActionAutonomyConfigs(CreatedAtMixin, Base):
    __tablename__ = "ai_action_autonomy_configs"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'id', name='uq_ai_action_autonomy_configs_tenant_id'),
        ForeignKeyConstraint(['tenant_id'], ['platform.tenants.id'], name='fk_ai_action_autonomy_configs_tenant'),
        ForeignKeyConstraint(['tenant_id', 'business_unit_id'], ['tenant.business_units.tenant_id', 'tenant.business_units.id'], name='fk_ai_action_autonomy_configs_bu'),
        ForeignKeyConstraint(['tenant_id', 'created_by_user_id'], ['tenant.users.tenant_id', 'tenant.users.id'], name='fk_ai_action_autonomy_configs_user'),
        CheckConstraint('effective_to IS NULL OR effective_to > effective_from', name='chk_ai_action_autonomy_configs_period'),
        {"schema": "tenant"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    action_type: Mapped[str] = mapped_column(AiActionTypeEnum, nullable=False)
    scope_level: Mapped[str] = mapped_column(ConfigScopeEnum, nullable=False, server_default=text("'tenant'"))
    business_unit_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    autonomy_mode: Mapped[str] = mapped_column(AiAutonomyModeEnum, nullable=False)
    confidence_threshold: Mapped[Decimal | None] = mapped_column(ConfidenceScoreDomain)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))

    rel_fk_ai_action_autonomy_configs_tenant: Mapped["PlatformTenants"] = relationship("PlatformTenants", viewonly=True, foreign_keys="[TenantAiActionAutonomyConfigs.tenant_id]")
    rel_fk_ai_action_autonomy_configs_bu: Mapped["TenantBusinessUnits"] = relationship("TenantBusinessUnits", viewonly=True, foreign_keys="[TenantAiActionAutonomyConfigs.tenant_id, TenantAiActionAutonomyConfigs.business_unit_id]")
    rel_fk_ai_action_autonomy_configs_user: Mapped["TenantUsers"] = relationship("TenantUsers", viewonly=True, foreign_keys="[TenantAiActionAutonomyConfigs.tenant_id, TenantAiActionAutonomyConfigs.created_by_user_id]")

