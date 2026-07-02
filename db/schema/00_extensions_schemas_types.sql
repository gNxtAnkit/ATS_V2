-- ============================================================
-- gNxtHire AI-Native Multi-Tenant ATS Platform
-- PostgreSQL 16+ Production Schema Regeneration
-- File 00: Extensions, schemas, shared types, app context helpers
-- Architecture: shared modular-monolith database with schema boundaries.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS platform;
CREATE SCHEMA IF NOT EXISTS tenant;
CREATE SCHEMA IF NOT EXISTS agency;
CREATE SCHEMA IF NOT EXISTS ai;
CREATE SCHEMA IF NOT EXISTS events;
CREATE SCHEMA IF NOT EXISTS integrations;
CREATE SCHEMA IF NOT EXISTS notif;
CREATE SCHEMA IF NOT EXISTS billing;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS compliance;

-- -------------------------------
-- Application/session context helpers for RLS.
-- Application must SET LOCAL app.current_tenant_id, app.user_id, app.permissions,
-- and app.is_platform_admin inside every request transaction.
-- -------------------------------
CREATE OR REPLACE FUNCTION app.current_tenant_id()
RETURNS uuid
LANGUAGE sql
STABLE
AS $$ SELECT NULLIF(current_setting('app.current_tenant_id', true), '')::uuid $$;

CREATE OR REPLACE FUNCTION app.current_user_id()
RETURNS uuid
LANGUAGE sql
STABLE
AS $$ SELECT NULLIF(current_setting('app.user_id', true), '')::uuid $$;

CREATE OR REPLACE FUNCTION app.is_platform_admin()
RETURNS boolean
LANGUAGE sql
STABLE
AS $$ SELECT COALESCE(NULLIF(current_setting('app.is_platform_admin', true), '')::boolean, false) $$;

CREATE OR REPLACE FUNCTION app.has_permission(permission_key text)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
  SELECT app.is_platform_admin()
      OR permission_key = ANY(string_to_array(COALESCE(current_setting('app.permissions', true), ''), ','));
$$;

CREATE OR REPLACE FUNCTION app.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION app.bump_lock_version()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    NEW.lock_version := COALESCE(OLD.lock_version, 0) + 1;
  END IF;
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION app.deny_update_delete()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION '% is append-only and does not allow %', TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME, TG_OP;
END;
$$;

CREATE OR REPLACE FUNCTION app.validate_one_of_refs()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  ref_count int := 0;
BEGIN
  ref_count :=
    (CASE WHEN NEW.candidate_id IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN NEW.requisition_id IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN NEW.application_id IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN NEW.interview_id IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN NEW.offer_id IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN NEW.client_id IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN NEW.mandate_id IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN NEW.submittal_id IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN NEW.placement_id IS NULL THEN 0 ELSE 1 END);
  IF ref_count <> 1 THEN
    RAISE EXCEPTION 'entity reference must point to exactly one supported subject, got % references', ref_count;
  END IF;
  RETURN NEW;
END;
$$;

-- -------------------------------
-- Domains
-- -------------------------------
CREATE DOMAIN currency_code AS char(3)
  CHECK (VALUE ~ '^[A-Z]{3}$');

CREATE DOMAIN percent_0_100 AS numeric(5,2)
  CHECK (VALUE >= 0 AND VALUE <= 100);

CREATE DOMAIN confidence_score AS numeric(5,4)
  CHECK (VALUE >= 0 AND VALUE <= 1);

CREATE DOMAIN positive_money AS numeric(14,2)
  CHECK (VALUE >= 0);

-- -------------------------------
-- Enums
-- -------------------------------
CREATE TYPE tenant_type_enum AS ENUM ('corporate', 'staffing_agency', 'rpo', 'executive_search');
CREATE TYPE tenant_status_enum AS ENUM ('provisioning', 'trial', 'active', 'suspended', 'churned', 'pending_deletion', 'deleted');
CREATE TYPE isolation_tier_enum AS ENUM ('shared', 'dedicated_compute', 'dedicated_db', 'fully_isolated');
CREATE TYPE region_enum AS ENUM ('US', 'EU', 'IN', 'ME', 'APAC', 'UK', 'CA', 'AU');
CREATE TYPE billing_interval_enum AS ENUM ('monthly', 'annual', 'custom');
CREATE TYPE plan_status_enum AS ENUM ('draft', 'active', 'deprecated', 'archived');
CREATE TYPE platform_user_status_enum AS ENUM ('invited', 'active', 'locked', 'suspended', 'deleted');
CREATE TYPE tenant_user_status_enum AS ENUM ('invited', 'active', 'locked', 'suspended', 'deleted');
CREATE TYPE audit_actor_type_enum AS ENUM ('tenant_user', 'platform_user', 'ai_agent', 'system', 'webhook', 'scheduler');
CREATE TYPE security_event_type_enum AS ENUM ('login_success','login_failed','logout','logout_all','session_revoked','password_changed','password_reset_requested','password_reset_completed','email_verification_requested','email_verified','mfa_enabled','mfa_disabled','mfa_failed','account_locked','account_unlocked','sso_login_success','sso_login_failed','api_key_created','api_key_revoked','suspicious_login','impossible_travel','brute_force_detected');
CREATE TYPE security_event_outcome_enum AS ENUM ('success','failure','blocked');
CREATE TYPE security_event_severity_enum AS ENUM ('info','low','medium','high','critical');
CREATE TYPE mfa_method_enum AS ENUM ('totp','sms','push','hardware_key','recovery_code');
CREATE TYPE sso_provider_enum AS ENUM ('google','microsoft','okta','custom_oidc','custom_saml');
CREATE TYPE sso_status_enum AS ENUM ('active','disabled','deleted');
CREATE TYPE config_scope_enum AS ENUM ('platform','tenant','business_unit','team','user');
CREATE TYPE config_value_type_enum AS ENUM ('boolean','string','number','integer','enum','secret_ref');
CREATE TYPE abac_effect_enum AS ENUM ('allow','deny');
CREATE TYPE condition_operator_enum AS ENUM ('equals','not_equals','in','not_in','contains','starts_with','ends_with','greater_than','greater_or_equal','less_than','less_or_equal','is_null','is_not_null','between');
CREATE TYPE field_redaction_enum AS ENUM ('hide_field','mask_value','show_aggregate_only');
CREATE TYPE delegation_status_enum AS ENUM ('active','expired','revoked');
CREATE TYPE headcount_type_enum AS ENUM ('new','backfill','expansion','replacement');
CREATE TYPE requisition_status_enum AS ENUM ('draft','pending_approval','approved','on_hold','sourcing','closed','cancelled');
CREATE TYPE employment_type_enum AS ENUM ('full_time','part_time','contract','internship','freelance');
CREATE TYPE job_description_status_enum AS ENUM ('draft','pending_human_review','approved','published','archived');
CREATE TYPE application_status_enum AS ENUM ('applied','under_review','shortlisted','in_interview','offer_extended','hired','rejected','withdrawn');
CREATE TYPE stage_direction_enum AS ENUM ('forward','backward','lateral');
CREATE TYPE interview_type_enum AS ENUM ('phone','video','onsite','ai_async','ai_live_voice','panel');
CREATE TYPE interview_status_enum AS ENUM ('scheduled','in_progress','completed','cancelled','no_show_candidate','no_show_interviewer','rescheduled');
CREATE TYPE offer_status_enum AS ENUM ('draft','pending_approval','approved','sent','accepted','declined','rescinded','expired');
CREATE TYPE approval_status_enum AS ENUM ('pending','approved','rejected','delegated','expired','skipped','reassigned');
CREATE TYPE contract_type_enum AS ENUM ('retained','contingency','rpo','time_and_materials');
CREATE TYPE fee_structure_enum AS ENUM ('percentage_of_salary','flat_fee','retainer','time_and_materials');
CREATE TYPE exclusivity_enum AS ENUM ('exclusive','non_exclusive','retained');
CREATE TYPE client_status_enum AS ENUM ('active','paused','churned','pending','deleted');
CREATE TYPE mandate_status_enum AS ENUM ('draft','active','on_hold','filled','cancelled','expired');
CREATE TYPE submittal_status_enum AS ENUM ('draft','submitted','client_reviewing','client_interview','placed','rejected_by_client','withdrawn');
CREATE TYPE guarantee_status_enum AS ENUM ('active','breached','cleared','waived');
CREATE TYPE wf_template_status_enum AS ENUM ('draft','published','deprecated','archived');
CREATE TYPE wf_instance_status_enum AS ENUM ('running','waiting','completed','failed','cancelled','migrating');
CREATE TYPE wf_step_type_enum AS ENUM ('approval','task','ai_action','notification','wait','condition','parallel','subprocess');
CREATE TYPE approver_resolution_enum AS ENUM ('by_role','by_specific_user','by_org_hierarchy','by_policy');
CREATE TYPE ai_provider_enum AS ENUM ('anthropic','openai','google','azure_openai','bedrock','ollama','custom');
CREATE TYPE ai_autonomy_mode_enum AS ENUM ('full_auto','human_approval_required','suggest_only');
CREATE TYPE ai_action_type_enum AS ENUM ('sourcing_match','resume_screening','outreach_draft','interview_scheduling','interview_evaluation','offer_draft','rejection_draft','joining_risk_score','jd_generation','jd_validation','bias_check','language_detection','sentiment_analysis','call_quality_check');
CREATE TYPE ai_session_status_enum AS ENUM ('not_started','in_progress','completed','expired','paused','cancelled');
CREATE TYPE connector_category_enum AS ENUM ('job_board','hrms','calendar','video','payroll','background_check','telephony','crm','assessment','email','custom');
CREATE TYPE connector_auth_type_enum AS ENUM ('oauth2','api_key','saml','basic_auth','webhook_secret','none');
CREATE TYPE connector_status_enum AS ENUM ('connected','degraded','down','expired','disconnected','pending_setup');
CREATE TYPE sync_type_enum AS ENUM ('webhook','polling','batch','real_time');
CREATE TYPE sync_status_enum AS ENUM ('pending','running','success','partial_failure','failed','skipped');
CREATE TYPE posting_status_enum AS ENUM ('pending','active','paused','closed','expired','failed');
CREATE TYPE notif_channel_enum AS ENUM ('email','sms','push','in_app','whatsapp','slack');
CREATE TYPE notif_recipient_type_enum AS ENUM ('tenant_user','candidate','client_contact','platform_user');
CREATE TYPE notif_delivery_status_enum AS ENUM ('queued','sent','delivered','opened','clicked','bounced','failed','suppressed','cancelled');
CREATE TYPE notif_category_enum AS ENUM ('transactional','marketing','system_alert','sla_alert','ai_alert','governance');
CREATE TYPE review_item_status_enum AS ENUM ('pending','approved','rejected','modified','expired','escalated');
CREATE TYPE invoice_status_enum AS ENUM ('draft','pending','paid','past_due','void','uncollectible');
CREATE TYPE payment_status_enum AS ENUM ('pending','succeeded','failed','disputed','refunded','partially_refunded');
CREATE TYPE usage_source_enum AS ENUM ('api','ui','worker','webhook','ai_agent','mobile');
CREATE TYPE report_format_enum AS ENUM ('csv','xlsx','pdf','json');
CREATE TYPE call_direction_enum AS ENUM ('inbound','outbound');
CREATE TYPE consent_type_enum AS ENUM ('data_processing','marketing','ai_evaluation','call_recording','talent_pool_retention','data_transfer','background_check');
CREATE TYPE dsr_type_enum AS ENUM ('access','erasure','portability','rectification','restriction','objection');
CREATE TYPE dsr_status_enum AS ENUM ('submitted','verifying_identity','in_progress','completed','rejected','cancelled');
CREATE TYPE suppression_reason_enum AS ENUM ('do_not_contact','hard_bounce','opted_out','dnc_list','legal_hold','client_specific','competitor_conflict');
CREATE TYPE compliance_framework_enum AS ENUM ('SOC2','ISO27001','GDPR','CCPA','HIPAA','OFCCP','EEO','AI_ACT_EU','NYC_LL144','DPDPA');
CREATE TYPE data_tier_enum AS ENUM ('hot','warm','cold','archive');
CREATE TYPE rollout_strategy_enum AS ENUM ('blue_green','canary','rolling','immediate');
CREATE TYPE ticket_priority_enum AS ENUM ('P1','P2','P3','P4');
CREATE TYPE ticket_status_enum AS ENUM ('open','in_progress','waiting_on_customer','resolved','closed');
CREATE TYPE sla_severity_enum AS ENUM ('warning','breached','critical');
CREATE TYPE competency_level_enum AS ENUM ('must_have','nice_to_have','preferred','bonus');

COMMENT ON SCHEMA platform IS 'Platform-admin owned metadata, tenants, plans, global governance, and audit.';
COMMENT ON SCHEMA tenant IS 'Tenant-scoped identity, corporate ATS, candidate, configuration, workflow, and tenant-facing operations.';
COMMENT ON SCHEMA agency IS 'Agency/RPO/executive-search domain tables scoped by tenant and client.';
COMMENT ON SCHEMA ai IS 'AI recruiter, AI interview, telephony, evaluation, usage, and governance records.';
COMMENT ON SCHEMA events IS 'Internal domain events, outbox, webhook delivery, and idempotency.';
COMMENT ON SCHEMA billing IS 'Subscription, invoice, payment, metering, and revenue tables.';
COMMENT ON SCHEMA analytics IS 'Reporting metrics, dimensions, event facts, and aggregate facts.';
COMMENT ON SCHEMA compliance IS 'Retention, legal hold, evidence package, and DSR audit support.';
