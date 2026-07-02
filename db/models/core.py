# db/models/core.py
from __future__ import annotations

import uuid
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, CHAR, CheckConstraint, DateTime, MetaData, Numeric, Table, Text, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def check_constraint_token(constraint: object, table: Table) -> str:
    if isinstance(constraint, CheckConstraint):
        source = str(constraint.sqltext)
    else:
        source = table.name
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:10]
    return digest


NAMING_CONVENTION: dict[str, object] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(check_hash)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
    "check_hash": check_constraint_token,
}


class Base(DeclarativeBase):
    """Shared declarative base used by Alembic target_metadata."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    """Safe only for tables where `id` is the sole primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


class TenantIdMixin:
    """Tenant marker mixin. Do not use this when tenant_id participates in composite PK/FK definitions."""

    tenant_id: Mapped[uuid.UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LockVersionMixin:
    lock_version: Mapped[int] = mapped_column(BigInteger(), nullable=False, server_default=text("0"))


# PostgreSQL DOMAIN types used by the regenerated schema.
CurrencyCodeDomain = postgresql.DOMAIN(
    "currency_code",
    CHAR(3),
    check="VALUE ~ '^[A-Z]{3}$'",
    create_type=True,
)
Percent0100Domain = postgresql.DOMAIN(
    "percent_0_100",
    Numeric(5, 2),
    check="VALUE >= 0 AND VALUE <= 100",
    create_type=True,
)
ConfidenceScoreDomain = postgresql.DOMAIN(
    "confidence_score",
    Numeric(5, 4),
    check="VALUE >= 0 AND VALUE <= 1",
    create_type=True,
)
PositiveMoneyDomain = postgresql.DOMAIN(
    "positive_money",
    Numeric(14, 2),
    check="VALUE >= 0",
    create_type=True,
)


# PostgreSQL ENUM types. Kept as shared singleton objects so models and Alembic
# autogenerate refer to a stable database type name.
AbacEffectEnum = postgresql.ENUM('allow', 'deny', name='abac_effect_enum', create_type=True)
AiActionTypeEnum = postgresql.ENUM('sourcing_match', 'resume_screening', 'outreach_draft', 'interview_scheduling', 'interview_evaluation', 'offer_draft', 'rejection_draft', 'joining_risk_score', 'jd_generation', 'jd_validation', 'bias_check', 'language_detection', 'sentiment_analysis', 'call_quality_check', name='ai_action_type_enum', create_type=True)
AiAutonomyModeEnum = postgresql.ENUM('full_auto', 'human_approval_required', 'suggest_only', name='ai_autonomy_mode_enum', create_type=True)
AiProviderEnum = postgresql.ENUM('anthropic', 'openai', 'google', 'azure_openai', 'bedrock', 'ollama', 'custom', name='ai_provider_enum', create_type=True)
AiSessionStatusEnum = postgresql.ENUM('not_started', 'in_progress', 'completed', 'expired', 'paused', 'cancelled', name='ai_session_status_enum', create_type=True)
ApplicationStatusEnum = postgresql.ENUM('applied', 'under_review', 'shortlisted', 'in_interview', 'offer_extended', 'hired', 'rejected', 'withdrawn', name='application_status_enum', create_type=True)
ApprovalStatusEnum = postgresql.ENUM('pending', 'approved', 'rejected', 'delegated', 'expired', 'skipped', 'reassigned', name='approval_status_enum', create_type=True)
ApproverResolutionEnum = postgresql.ENUM('by_role', 'by_specific_user', 'by_org_hierarchy', 'by_policy', name='approver_resolution_enum', create_type=True)
AuditActorTypeEnum = postgresql.ENUM('tenant_user', 'platform_user', 'ai_agent', 'system', 'webhook', 'scheduler', name='audit_actor_type_enum', create_type=True)
BillingIntervalEnum = postgresql.ENUM('monthly', 'annual', 'custom', name='billing_interval_enum', create_type=True)
CallDirectionEnum = postgresql.ENUM('inbound', 'outbound', name='call_direction_enum', create_type=True)
ClientStatusEnum = postgresql.ENUM('active', 'paused', 'churned', 'pending', 'deleted', name='client_status_enum', create_type=True)
CompetencyLevelEnum = postgresql.ENUM('must_have', 'nice_to_have', 'preferred', 'bonus', name='competency_level_enum', create_type=True)
ComplianceFrameworkEnum = postgresql.ENUM('SOC2', 'ISO27001', 'GDPR', 'CCPA', 'HIPAA', 'OFCCP', 'EEO', 'AI_ACT_EU', 'NYC_LL144', 'DPDPA', name='compliance_framework_enum', create_type=True)
ConditionOperatorEnum = postgresql.ENUM('equals', 'not_equals', 'in', 'not_in', 'contains', 'starts_with', 'ends_with', 'greater_than', 'greater_or_equal', 'less_than', 'less_or_equal', 'is_null', 'is_not_null', 'between', name='condition_operator_enum', create_type=True)
ConfigScopeEnum = postgresql.ENUM('platform', 'tenant', 'business_unit', 'team', 'user', name='config_scope_enum', create_type=True)
ConfigValueTypeEnum = postgresql.ENUM('boolean', 'string', 'number', 'integer', 'enum', 'secret_ref', name='config_value_type_enum', create_type=True)
ConnectorAuthTypeEnum = postgresql.ENUM('oauth2', 'api_key', 'saml', 'basic_auth', 'webhook_secret', 'none', name='connector_auth_type_enum', create_type=True)
ConnectorCategoryEnum = postgresql.ENUM('job_board', 'hrms', 'calendar', 'video', 'payroll', 'background_check', 'telephony', 'crm', 'assessment', 'email', 'custom', name='connector_category_enum', create_type=True)
ConnectorStatusEnum = postgresql.ENUM('connected', 'degraded', 'down', 'expired', 'disconnected', 'pending_setup', name='connector_status_enum', create_type=True)
ConsentTypeEnum = postgresql.ENUM('data_processing', 'marketing', 'ai_evaluation', 'call_recording', 'talent_pool_retention', 'data_transfer', 'background_check', name='consent_type_enum', create_type=True)
ContractTypeEnum = postgresql.ENUM('retained', 'contingency', 'rpo', 'time_and_materials', name='contract_type_enum', create_type=True)
DataTierEnum = postgresql.ENUM('hot', 'warm', 'cold', 'archive', name='data_tier_enum', create_type=True)
DelegationStatusEnum = postgresql.ENUM('active', 'expired', 'revoked', name='delegation_status_enum', create_type=True)
DsrStatusEnum = postgresql.ENUM('submitted', 'verifying_identity', 'in_progress', 'completed', 'rejected', 'cancelled', name='dsr_status_enum', create_type=True)
DsrTypeEnum = postgresql.ENUM('access', 'erasure', 'portability', 'rectification', 'restriction', 'objection', name='dsr_type_enum', create_type=True)
EmploymentTypeEnum = postgresql.ENUM('full_time', 'part_time', 'contract', 'internship', 'freelance', name='employment_type_enum', create_type=True)
ExclusivityEnum = postgresql.ENUM('exclusive', 'non_exclusive', 'retained', name='exclusivity_enum', create_type=True)
FeeStructureEnum = postgresql.ENUM('percentage_of_salary', 'flat_fee', 'retainer', 'time_and_materials', name='fee_structure_enum', create_type=True)
FieldRedactionEnum = postgresql.ENUM('hide_field', 'mask_value', 'show_aggregate_only', name='field_redaction_enum', create_type=True)
GuaranteeStatusEnum = postgresql.ENUM('active', 'breached', 'cleared', 'waived', name='guarantee_status_enum', create_type=True)
HeadcountTypeEnum = postgresql.ENUM('new', 'backfill', 'expansion', 'replacement', name='headcount_type_enum', create_type=True)
InterviewStatusEnum = postgresql.ENUM('scheduled', 'in_progress', 'completed', 'cancelled', 'no_show_candidate', 'no_show_interviewer', 'rescheduled', name='interview_status_enum', create_type=True)
InterviewTypeEnum = postgresql.ENUM('phone', 'video', 'onsite', 'ai_async', 'ai_live_voice', 'panel', name='interview_type_enum', create_type=True)
InvoiceStatusEnum = postgresql.ENUM('draft', 'pending', 'paid', 'past_due', 'void', 'uncollectible', name='invoice_status_enum', create_type=True)
IsolationTierEnum = postgresql.ENUM('shared', 'dedicated_compute', 'dedicated_db', 'fully_isolated', name='isolation_tier_enum', create_type=True)
JobDescriptionStatusEnum = postgresql.ENUM('draft', 'pending_human_review', 'approved', 'published', 'archived', name='job_description_status_enum', create_type=True)
MandateStatusEnum = postgresql.ENUM('draft', 'active', 'on_hold', 'filled', 'cancelled', 'expired', name='mandate_status_enum', create_type=True)
MfaMethodEnum = postgresql.ENUM('totp', 'sms', 'push', 'hardware_key', 'recovery_code', name='mfa_method_enum', create_type=True)
NotifCategoryEnum = postgresql.ENUM('transactional', 'marketing', 'system_alert', 'sla_alert', 'ai_alert', 'governance', name='notif_category_enum', create_type=True)
NotifChannelEnum = postgresql.ENUM('email', 'sms', 'push', 'in_app', 'whatsapp', 'slack', name='notif_channel_enum', create_type=True)
NotifDeliveryStatusEnum = postgresql.ENUM('queued', 'sent', 'delivered', 'opened', 'clicked', 'bounced', 'failed', 'suppressed', 'cancelled', name='notif_delivery_status_enum', create_type=True)
NotifRecipientTypeEnum = postgresql.ENUM('tenant_user', 'candidate', 'client_contact', 'platform_user', name='notif_recipient_type_enum', create_type=True)
OfferStatusEnum = postgresql.ENUM('draft', 'pending_approval', 'approved', 'sent', 'accepted', 'declined', 'rescinded', 'expired', name='offer_status_enum', create_type=True)
PaymentStatusEnum = postgresql.ENUM('pending', 'succeeded', 'failed', 'disputed', 'refunded', 'partially_refunded', name='payment_status_enum', create_type=True)
PlanStatusEnum = postgresql.ENUM('draft', 'active', 'deprecated', 'archived', name='plan_status_enum', create_type=True)
PlatformUserStatusEnum = postgresql.ENUM('invited', 'active', 'locked', 'suspended', 'deleted', name='platform_user_status_enum', create_type=True)
PostingStatusEnum = postgresql.ENUM('pending', 'active', 'paused', 'closed', 'expired', 'failed', name='posting_status_enum', create_type=True)
RegionEnum = postgresql.ENUM('US', 'EU', 'IN', 'ME', 'APAC', 'UK', 'CA', 'AU', name='region_enum', create_type=True)
ReportFormatEnum = postgresql.ENUM('csv', 'xlsx', 'pdf', 'json', name='report_format_enum', create_type=True)
RequisitionStatusEnum = postgresql.ENUM('draft', 'pending_approval', 'approved', 'on_hold', 'sourcing', 'closed', 'cancelled', name='requisition_status_enum', create_type=True)
ReviewItemStatusEnum = postgresql.ENUM('pending', 'approved', 'rejected', 'modified', 'expired', 'escalated', name='review_item_status_enum', create_type=True)
RolloutStrategyEnum = postgresql.ENUM('blue_green', 'canary', 'rolling', 'immediate', name='rollout_strategy_enum', create_type=True)
SecurityEventOutcomeEnum = postgresql.ENUM('success', 'failure', 'blocked', name='security_event_outcome_enum', create_type=True)
SecurityEventSeverityEnum = postgresql.ENUM('info', 'low', 'medium', 'high', 'critical', name='security_event_severity_enum', create_type=True)
SecurityEventTypeEnum = postgresql.ENUM('login_success', 'login_failed', 'logout', 'logout_all', 'session_revoked', 'password_changed', 'password_reset_requested', 'password_reset_completed', 'email_verification_requested', 'email_verified', 'mfa_enabled', 'mfa_disabled', 'mfa_failed', 'account_locked', 'account_unlocked', 'sso_login_success', 'sso_login_failed', 'api_key_created', 'api_key_revoked', 'suspicious_login', 'impossible_travel', 'brute_force_detected', name='security_event_type_enum', create_type=True)
SlaSeverityEnum = postgresql.ENUM('warning', 'breached', 'critical', name='sla_severity_enum', create_type=True)
SsoProviderEnum = postgresql.ENUM('google', 'microsoft', 'okta', 'custom_oidc', 'custom_saml', name='sso_provider_enum', create_type=True)
SsoStatusEnum = postgresql.ENUM('active', 'disabled', 'deleted', name='sso_status_enum', create_type=True)
StageDirectionEnum = postgresql.ENUM('forward', 'backward', 'lateral', name='stage_direction_enum', create_type=True)
SubmittalStatusEnum = postgresql.ENUM('draft', 'submitted', 'client_reviewing', 'client_interview', 'placed', 'rejected_by_client', 'withdrawn', name='submittal_status_enum', create_type=True)
SuppressionReasonEnum = postgresql.ENUM('do_not_contact', 'hard_bounce', 'opted_out', 'dnc_list', 'legal_hold', 'client_specific', 'competitor_conflict', name='suppression_reason_enum', create_type=True)
SyncStatusEnum = postgresql.ENUM('pending', 'running', 'success', 'partial_failure', 'failed', 'skipped', name='sync_status_enum', create_type=True)
SyncTypeEnum = postgresql.ENUM('webhook', 'polling', 'batch', 'real_time', name='sync_type_enum', create_type=True)
TenantStatusEnum = postgresql.ENUM('provisioning', 'trial', 'active', 'suspended', 'churned', 'pending_deletion', 'deleted', name='tenant_status_enum', create_type=True)
TenantTypeEnum = postgresql.ENUM('corporate', 'staffing_agency', 'rpo', 'executive_search', name='tenant_type_enum', create_type=True)
TenantUserStatusEnum = postgresql.ENUM('invited', 'active', 'locked', 'suspended', 'deleted', name='tenant_user_status_enum', create_type=True)
TicketPriorityEnum = postgresql.ENUM('P1', 'P2', 'P3', 'P4', name='ticket_priority_enum', create_type=True)
TicketStatusEnum = postgresql.ENUM('open', 'in_progress', 'waiting_on_customer', 'resolved', 'closed', name='ticket_status_enum', create_type=True)
UsageSourceEnum = postgresql.ENUM('api', 'ui', 'worker', 'webhook', 'ai_agent', 'mobile', name='usage_source_enum', create_type=True)
WfInstanceStatusEnum = postgresql.ENUM('running', 'waiting', 'completed', 'failed', 'cancelled', 'migrating', name='wf_instance_status_enum', create_type=True)
WfStepTypeEnum = postgresql.ENUM('approval', 'task', 'ai_action', 'notification', 'wait', 'condition', 'parallel', 'subprocess', name='wf_step_type_enum', create_type=True)
WfTemplateStatusEnum = postgresql.ENUM('draft', 'published', 'deprecated', 'archived', name='wf_template_status_enum', create_type=True)
