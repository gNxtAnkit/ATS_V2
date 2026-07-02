# 33 — Service to Table Ownership Matrix

## Ownership summary

| Service | Schemas | Owned table groups |
| --- | --- | --- |
| Platform Admin | platform | tenants, plans, quotas, features, support, audit, SLO, deployments, AI governance |
| Identity | tenant/platform | tenant users/sessions/MFA/tokens/SSO/security events; platform admin users by platform realm |
| Tenant Core/RBAC | tenant | business units, teams, roles, permissions, ABAC, field permissions, delegations, API keys, calendars |
| Configuration | platform/tenant | config definitions, values, change log |
| Candidate | tenant | candidates, contacts, documents, consent, DSR task primitives, talent pools, suppressions, skills, EEO, duplicates |
| Corporate ATS | tenant | headcount, requisitions, job descriptions, applications, interviews, scorecards, offers, onboarding |
| Workflow | tenant | workflow templates, steps, transitions, instances, history, approval tasks |
| Agency ATS | agency | clients, contacts, portal users, mandates, submittals, feedback, placements, guarantees |
| AI Recruiter | ai | personas, prompts, agents, sourcing, matching, screening, conversations, scheduling, usage |
| AI Interview/Telephony | ai | interview sessions/questions/responses/evaluations; telephony config/calls/quality |
| Events | events | outbox, domain events, subscriptions, delivery attempts, idempotency |
| Notifications | notif/tenant | templates, contents, events, deliveries, suppression, preferences, overrides |
| Integrations | platform/tenant | connector definitions/versions; connector instances, sync jobs, webhooks, calendar, HRMS mappings |
| Billing | billing | subscriptions, usage, invoices, line items, taxes, payments, credits |
| Reporting | tenant/analytics | dashboards, reports, exports, metrics, dimensions, analytics events, facts |
| Compliance | compliance/tenant/platform | retention, legal holds, evidence, DSR/consent/audit coordination |


## Full table inventory by schema

### agency

client_contacts, client_domains, client_portal_user_mandates, client_portal_users, clients, competitor_conflicts, external_competing_agencies, mandate_competing_agencies, mandate_fee_terms, mandates, placement_fee_term_snapshots, placement_guarantees, placements, retainer_milestones, submittal_feedback, submittal_profile_fields, submittal_profile_snapshots, submittals

### ai

agent_business_units, agent_identities, agent_permissions, ai_bias_flags, ai_conversations, ai_usage_events, call_quality_metrics, call_real_time_flags, call_records, conversation_escalation_flags, conversation_messages, interview_evaluation_competency_scores, interview_evaluation_flags, interview_evaluations, interview_low_confidence_segments, interview_question_competencies, interview_question_sets, interview_questions, interview_response_media, interview_responses, interview_sessions, joining_risk_factors, joining_risk_scores, live_interview_calls, match_score_criteria, match_scores, persona_banned_topics, persona_escalation_rules, persona_jurisdiction_disclosures, persona_languages, persona_required_disclosures, prompt_template_policy_flags, prompt_template_variables, prompt_templates, recruiter_personas, scheduling_calendar_sync_statuses, scheduling_participants, scheduling_proposed_slots, scheduling_requests, screening_criteria_results, screening_results, sourcing_criteria, sourcing_runs, sourcing_sources, telephony_numbers, telephony_region_routes, tenant_telephony_configs

### analytics

analytics_event_dimension_values, analytics_event_metric_values, analytics_events, daily_metric_facts, dimension_definitions, metric_definitions

### billing

billing_addresses, credits, invoice_line_items, invoice_taxes, invoices, payment_attempts, payment_methods, subscription_items, subscriptions, tenant_addon_subscriptions, tenant_quota_overrides, usage_aggregations, usage_events

### compliance

evidence_items, evidence_packages, legal_holds, retention_policies

### events

domain_events, event_delivery_attempts, event_outbox, event_subscription_event_types, event_subscriptions, idempotency_records

### notif

notification_deliveries, notification_delivery_attempts, notification_event_variables, notification_events, notification_template_channels, notification_template_contents, notification_template_variables, notification_templates, suppression_list

### platform

addon_feature_entitlements, addon_quota_deltas, ai_governance_alert_evidence, ai_governance_alerts, ai_model_definitions, ai_model_region_restrictions, ai_quality_metrics, allowed_array_columns, allowed_jsonb_columns, api_versions, audit_logs, benchmark_cohorts, benchmark_metrics, compliance_framework_regions, compliance_frameworks, config_allowed_values, config_definitions, config_scope_levels, connector_definitions, connector_operations, connector_versions, deployments, error_budget_status, feature_definitions, feature_flag_registry, feature_flag_tenant_overrides, infra_pools, plan_addons, plan_feature_entitlements, plan_quota_limits, plans, platform_permissions, platform_role_permissions, platform_roles, platform_user_roles, platform_users, quota_definitions, sla_policies, slo_definitions, support_sessions, support_tickets, tenant_compliance_frameworks, tenant_domains, tenant_lifecycle_events, tenant_provisioning_jobs, tenant_provisioning_steps, tenants

### tenant

abac_policies, abac_policy_condition_groups, abac_policy_conditions, ai_action_autonomy_configs, api_key_scopes, api_keys, application_answers, application_questions, application_stage_history, applications, approval_tasks, business_units, calendar_event_attendees, calendar_events, calendar_holidays, candidate_contacts, candidate_documents, candidate_duplicate_flag_reasons, candidate_duplicate_flags, candidate_education, candidate_eeo_data, candidate_skills, candidate_suppressions, candidate_work_history, candidate_work_history_skills, candidates, competency_taxonomy, config_change_log, config_values, connector_instance_settings, connector_instances, consent_records, dashboard_shares, dashboard_widgets, dashboards, data_subject_request_tasks, data_subject_requests, delegations, domain_verifications, email_verification_tokens, entity_references, export_jobs, field_permission_roles, field_permissions, headcount_plans, hrms_field_mappings, hrms_sync_records, human_decisions, inclusive_language_findings, interview_panelists, interviews, job_board_postings, job_description_competencies, job_descriptions, localization_resources, mobile_device_registrations, notification_preference_channels, notification_preferences, notification_template_override_contents, notification_template_overrides, offer_approval_steps, offers, onboarding_tasks, password_reset_tokens, permission_condition_groups, permission_conditions, permissions, pipeline_stage_auto_actions, pipeline_stage_definitions, pre_joining_document_requirements, pre_joining_document_statuses, pre_joining_engagements, pre_joining_touchpoints, report_columns, report_definitions, report_filters, report_schedule_recipients, requisition_locations, requisition_openings, requisition_validation_issues, requisition_validation_results, requisitions, review_item_relations, review_items, role_permissions, roles, salary_benchmarks, scorecard_criteria, scorecard_ratings, scorecards, security_events, skill_taxonomy, sso_attribute_mappings, sso_configs, sso_group_role_mappings, sync_job_records, sync_jobs, talent_pool_entries, talent_pool_entry_mandates, talent_pools, team_members, teams, tenant_branding, user_mfa_factors, user_role_assignments, user_sessions, users, webhook_events, webhook_subscription_event_types, webhook_subscriptions, white_label_domains, workflow_canvas_edges, workflow_canvas_nodes, workflow_condition_evaluations, workflow_escalation_rules, workflow_instance_context_values, workflow_instance_history, workflow_instances, workflow_simulation_runs, workflow_simulation_steps, workflow_step_ai_action_configs, workflow_step_approval_configs, workflow_step_settings, workflow_steps, workflow_template_change_log, workflow_template_validation_errors, workflow_templates, workflow_transition_condition_groups, workflow_transition_conditions, workflow_transitions, working_calendar_days, working_calendars


## Private tables

All operational tables are private to their owner service by default. Other services read through APIs, events, read models, or approved views only.

## Read-through-API/event-only domains

Candidate master, corporate applications/requisitions, agency client/submittal data, AI outputs/evaluations, billing invoices/payment data, compliance/legal-hold/DSR data, and security/audit logs.

## Cross-service dependency risks

Reporting direct table coupling, billing inferred from private tables, notification querying operational tables, workflow embedding corporate-specific rules, and platform admin mutating tenant data outside support sessions.
