# gNxtHire regenerated PostgreSQL 16+ schema package

## 1. Requirement-to-domain inventory

| Phase | Requirements covered | Core entities / bounded contexts |
|---|---|---|
| Phase 1 | Multi-tenant architecture, platform administration, security and compliance | `platform.tenants`, tenant domains, infra pools, plans, quotas, features, support sessions, platform users, audit logs, SSO, MFA, RBAC, ABAC, field permissions, security events, branding, localization, DSR/consent |
| Phase 2 | Corporate ATS, workflow engine, RBAC deep dive | headcount plans, requisitions, requisition locations/openings, job descriptions, competency taxonomy, validation issues, pipelines, applications, interviews, scorecards, offers, onboarding, workflow templates, steps, transitions, approval tasks |
| Phase 3 | Agency ATS, AI recruiter, AI interview bot, telephony | agency clients, client contacts, mandates, fee terms, retainer milestones, client portal users, submittals, redacted profile snapshots, placements, recruiter personas, sourcing runs, match scores, screening, AI conversations, scheduling, AI interview sessions/evaluations, telephony configs, call records |
| Phase 4 | Integration framework, configuration framework, analytics, events | connector definitions/operations/versions, tenant connector instances/settings, sync jobs and records, webhook events, webhook subscriptions, HRMS mappings, calendar events/attendees, configuration definitions/values, domain events, outbox, metric/dimension definitions |
| Phase 5 | HITL, notifications, billing, scalability | review items, human decisions, notification templates/content/overrides, notification events/variables/deliveries/preferences/suppression, subscriptions, usage events, invoices, taxes, payments, credits, partition-ready high-volume event tables |
| Phase 6 | API strategy, DDD/microservices, mobile, white labeling, i18n | API versions, API keys/scopes, idempotency records, mobile device registrations, white-label domains, localization resources, service/event boundaries via schemas and outbox |
| Phase 7 | Journeys, KPIs, risk, enterprise readiness | dashboards, dashboard widgets/shares, report definitions/filters/columns/schedules, analytics event facts, daily metric facts, retention policies, legal holds, evidence packages/items, governance validation queries |

## 2. Final bounded-context decision

This package chooses **Option A: modular-monolith PostgreSQL with schemas and strong foreign keys**. The product is still organized by DDD boundaries (`platform`, `tenant`, `agency`, `ai`, `events`, `integrations`, `notif`, `billing`, `analytics`, `compliance`), but the database is a single shared PostgreSQL deployment with cross-schema referential integrity.

Reason: the requested rules explicitly require composite tenant-aware foreign keys and complete RLS. That is most reliable in a shared modular-monolith database. If the implementation later moves to true service-owned databases, cross-schema FKs should be replaced by event/API references and the `events.event_outbox` / `events.domain_events` tables become the integration contract.

## 3. JSONB / array replacement ledger

| Old pattern | New normalized structure | Reason |
|---|---|---|
| `platform.plans.included_quotas` | `platform.quota_definitions`, `platform.plan_quota_limits` | Queryable plan limits need typed constraints and billing joins. |
| `platform.plans.feature_flags` | `platform.feature_definitions`, `platform.plan_feature_entitlements` | Features are entitlements, not opaque blobs. |
| `platform.plan_addons.quota_delta` | `platform.addon_quota_deltas` | Add-on metering must be auditable per quota. |
| `platform.plan_addons.flag_delta` | `platform.addon_feature_entitlements` | Feature enablement requires FK-backed governance. |
| `billing.invoices.line_items` | `billing.invoice_line_items` | Invoice totals, tax, reconciliation need row-level integrity. |
| `billing.invoices.tax_breakdown` | `billing.invoice_taxes` | Taxes need jurisdiction/rate validation. |
| `billing.payment_methods.billing_address` | `billing.billing_addresses` | Address is reusable and validated. |
| `tenant.permissions.conditions` | `tenant.permission_condition_groups`, `tenant.permission_conditions` | RBAC conditions must be queryable and testable. |
| `tenant.abac_policies.attribute_condition` | `tenant.abac_policy_condition_groups`, `tenant.abac_policy_conditions` | ABAC cannot be hidden in opaque JSON. |
| `tenant.field_permissions.allowed_role_ids` | `tenant.field_permission_roles` | Many-to-many roles need bridge table. |
| `tenant.sso_configs.attribute_mapping` | `tenant.sso_attribute_mappings` | Claims mapping requires uniqueness and validation. |
| `tenant.sso_configs.group_role_mapping` | `tenant.sso_group_role_mappings` | SSO groups map to actual roles by FK. |
| `tenant.api_keys.scopes` | `tenant.api_key_scopes` | API key scopes reuse permission system. |
| `tenant.requisitions.location[]` | `tenant.requisition_locations` | Multi-location requisitions need typed fields. |
| `tenant.job_descriptions.competency_tags` | `tenant.competency_taxonomy`, `tenant.job_description_competencies` | Competencies drive matching/interviewing. |
| `tenant.job_descriptions.inclusive_language_flags` | `tenant.inclusive_language_findings` | Each finding has severity and suggestion. |
| `tenant.req_validation_results.issues` | `tenant.requisition_validation_issues` | AI validation issues need field-level tracking. |
| `tenant.pipeline_stage_definitions.auto_actions` | `tenant.pipeline_stage_auto_actions` | Stage automation requires auditing and enablement. |
| `tenant.applications.answers` | `tenant.application_questions`, `tenant.application_answers` | Screening answers are structured data. |
| `tenant.scorecards.competency_ratings` | `tenant.scorecard_criteria`, `tenant.scorecard_ratings` | Scorecards require criteria-level scoring. |
| `tenant.pre_joining_engagements.touchpoint_schedule` | `tenant.pre_joining_touchpoints` | Touchpoints are independently scheduled/tracked. |
| `tenant.pre_joining_engagements.document_collection_status` | `tenant.pre_joining_document_requirements`, `tenant.pre_joining_document_statuses` | Documents need status, verifier, and due dates. |
| `tenant.pre_joining_engagements.joining_risk_factors` | `ai.joining_risk_scores`, `ai.joining_risk_factors` | Risk factors belong to AI governance. |
| `tenant.workflow_templates.validation_errors` | `tenant.workflow_template_validation_errors` | Publish validation must be queryable. |
| `tenant.workflow_templates.canvas_state` | `tenant.workflow_canvas_nodes`, `tenant.workflow_canvas_edges` | Canvas topology is graph data. |
| `tenant.workflow_steps.config` | `tenant.workflow_step_settings` and typed step-config tables | Step config requires validation by type. |
| `tenant.workflow_steps.escalation_chain` | `tenant.workflow_escalation_rules` | Escalation chain is ordered workflow data. |
| `tenant.workflow_transitions.condition_expression` | `tenant.workflow_transition_condition_groups`, `tenant.workflow_transition_conditions` | Conditions need testability and indexing. |
| `tenant.workflow_simulation_runs.simulated_path` | `tenant.workflow_simulation_steps` | Simulation path is ordered rows. |
| `tenant.workflow_instances.context_snapshot` | `tenant.workflow_instance_context_values` | Context values need typed auditability. |
| `tenant.workflow_instance_history.conditions_evaluated` | `tenant.workflow_condition_evaluations` | Each evaluated condition is explainable. |
| `agency.client_portal_users.allowed_mandate_ids` | `agency.client_portal_user_mandates` | Portal scoping needs bridge table. |
| `agency.mandates.known_competing_agencies` | `agency.external_competing_agencies`, `agency.mandate_competing_agencies` | Competitor agencies are reusable entities. |
| `agency.submittals.client_visible_profile` | `agency.submittal_profile_snapshots`, `agency.submittal_profile_fields` | Redacted profiles need immutable snapshots. |
| `agency.placements.fee_structure_snapshot` | `agency.placement_fee_term_snapshots` | Fee terms require typed invoice reconciliation. |
| `ai.recruiter_personas.escalation_triggers` | `ai.persona_escalation_rules` | Escalation rules are operational. |
| `ai.recruiter_personas.jurisdiction_disclosures` | `ai.persona_jurisdiction_disclosures` | Jurisdiction disclosures need locale/region lookup. |
| `ai.sourcing_runs.search_criteria` | `ai.sourcing_criteria` | Sourcing criteria are weighted filters. |
| `ai.match_scores.criteria_applied` | `ai.match_score_criteria` | Match explainability must be per criterion. |
| `ai.match_scores.bias_flags`, `ai.screening_results.bias_flags` | `ai.ai_bias_flags` | Bias flags require shared governance table. |
| `ai.screening_results.criteria_breakdown` | `ai.screening_criteria_results` | Screening evidence needs criteria-level rows. |
| `ai.ai_conversations.turns` | `ai.conversation_messages` | Conversations are ordered messages. |
| `ai.ai_conversations.escalation_flags` | `ai.conversation_escalation_flags` | Escalations need lifecycle tracking. |
| `ai.scheduling_requests participant/proposed/calendar JSON` | `ai.scheduling_participants`, `ai.scheduling_proposed_slots`, `ai.scheduling_calendar_sync_statuses` | Scheduling is relational and multi-party. |
| `ai.interview_sessions.responses` | `ai.interview_responses`, `ai.interview_response_media` | Responses/media need timestamps and storage URIs. |
| `ai.interview_question_sets.questions` | `ai.interview_questions` | Questions are versioned rows. |
| `ai.interview_question_sets.competency_coverage` | `ai.interview_question_competencies` | Competency coverage is many-to-many. |
| `ai.interview_evaluations.competency_scores` | `ai.interview_evaluation_competency_scores` | Evaluation scoring is per competency. |
| `ai.interview_evaluations.flags` | `ai.interview_evaluation_flags` | Evaluation flags have severity/status. |
| `ai.interview_evaluations.low_confidence_segments` | `ai.interview_low_confidence_segments` | Transcript confidence gaps need segment offsets. |
| `ai.tenant_telephony_configs.region_routing_rules` | `ai.telephony_region_routes` | Routing is prioritized by region. |
| `ai.call_records.real_time_flags` | `ai.call_real_time_flags` | Call flags need timestamped rows. |
| `connector_definitions.supported_operations` | `platform.connector_operations` | Connector capabilities need typed operations. |
| `connector_instances.config` | `tenant.connector_instance_settings` | Connector settings need typed values. |
| `connector_instances.hrms_field_mapping` | `tenant.hrms_field_mappings` | HRMS mappings are tenant-configurable rows. |
| `sync_jobs.failed_record_refs` | `tenant.sync_job_records` | Partial retry requires per-record status. |
| `calendar_events.attendees` | `tenant.calendar_event_attendees` | Attendees need response status and FKs. |
| `webhook_subscriptions.event_types` | `tenant.webhook_subscription_event_types` | Webhook event subscriptions are many-to-many. |
| `notification_templates.default_content` | `notif.notification_template_contents` | Content is per channel/locale. |
| `notification_template_overrides.custom_content` | `tenant.notification_template_override_contents` | Tenant overrides are per channel/locale. |
| `notification_events.payload_vars` | `notif.notification_event_variables` | Template variables need deterministic validation. |
| `dashboards.widgets` | `tenant.dashboard_widgets` | Widgets need layout, type, and report FK. |
| `dashboards.shared_with` | `tenant.dashboard_shares` | Sharing is many-to-many. |
| `report_definitions.filters` | `tenant.report_filters` | Report filters are typed conditions. |
| `report_definitions.columns/group_by` | `tenant.report_columns` | Report layout is ordered relational metadata. |
| `report_definitions.schedule_recipients` | `tenant.report_schedule_recipients` | Recipients are user FKs. |
| `analytics_events.metrics/dimensions` | `analytics.metric_definitions`, `analytics.dimension_definitions`, `analytics.analytics_event_metric_values`, `analytics.analytics_event_dimension_values`, `analytics.daily_metric_facts` | Analytics must be queryable and aggregatable. |

## 4. Remaining JSONB policy

Remaining JSONB is intentionally limited to immutable raw/snapshot payloads: audit before/after/diff snapshots, raw security/webhook/domain/outbox events, idempotency response snapshots, and raw model responses. The file `14_validation_queries.sql` includes a query that lists every JSONB column and joins it to `platform.allowed_jsonb_columns`.

## 5. Execution order

Run files in numeric order from `00_extensions_schemas_types.sql` through `14_validation_queries.sql`. File 14 is validation only and should be run in CI after schema creation.
