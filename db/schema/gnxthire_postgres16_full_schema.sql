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
CREATE TYPE platform_user_status_enum AS ENUM ('invited', 'active', 'suspended', 'deleted');
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
-- ============================================================
-- File 01: Platform administration, tenancy, plans, quotas, features, support, governance
-- ============================================================

CREATE TABLE platform.allowed_jsonb_columns (
  schema_name text NOT NULL,
  table_name text NOT NULL,
  column_name text NOT NULL,
  allowed_reason text NOT NULL,
  PRIMARY KEY (schema_name, table_name, column_name)
);

CREATE TABLE platform.allowed_array_columns (
  schema_name text NOT NULL,
  table_name text NOT NULL,
  column_name text NOT NULL,
  allowed_reason text NOT NULL,
  PRIMARY KEY (schema_name, table_name, column_name)
);

CREATE TABLE platform.plans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code citext NOT NULL,
  name text NOT NULL,
  description text,
  status plan_status_enum NOT NULL DEFAULT 'draft',
  billing_interval billing_interval_enum NOT NULL,
  base_price positive_money NOT NULL DEFAULT 0,
  currency currency_code NOT NULL DEFAULT 'USD',
  min_seats integer NOT NULL DEFAULT 1 CHECK (min_seats >= 1),
  max_seats integer CHECK (max_seats IS NULL OR max_seats >= min_seats),
  trial_days integer NOT NULL DEFAULT 0 CHECK (trial_days >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  lock_version bigint NOT NULL DEFAULT 0,
  CONSTRAINT uq_plans_code UNIQUE (code)
);
COMMENT ON TABLE platform.plans IS 'Subscription plan catalogue. Feature and quota entitlements are normalized into child tables.';

CREATE TABLE platform.quota_definitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  quota_key citext NOT NULL,
  display_name text NOT NULL,
  unit text NOT NULL,
  reset_period text NOT NULL CHECK (reset_period IN ('none','daily','monthly','annual')),
  is_metered boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_quota_definitions_quota_key UNIQUE (quota_key)
);

CREATE TABLE platform.plan_quota_limits (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id uuid NOT NULL,
  quota_definition_id uuid NOT NULL,
  hard_limit numeric(18,4) CHECK (hard_limit IS NULL OR hard_limit >= 0),
  soft_limit numeric(18,4) CHECK (soft_limit IS NULL OR soft_limit >= 0),
  overage_unit_price positive_money NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_plan_quota_limits_plan FOREIGN KEY (plan_id) REFERENCES platform.plans(id),
  CONSTRAINT fk_plan_quota_limits_quota FOREIGN KEY (quota_definition_id) REFERENCES platform.quota_definitions(id),
  CONSTRAINT uq_plan_quota_limits_plan_quota UNIQUE (plan_id, quota_definition_id),
  CONSTRAINT chk_plan_quota_limits_soft_lte_hard CHECK (hard_limit IS NULL OR soft_limit IS NULL OR soft_limit <= hard_limit)
);

CREATE TABLE platform.feature_definitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  feature_key citext NOT NULL,
  name text NOT NULL,
  description text,
  category text NOT NULL DEFAULT 'core',
  default_enabled boolean NOT NULL DEFAULT false,
  requires_human_governance boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_feature_definitions_feature_key UNIQUE (feature_key)
);

CREATE TABLE platform.plan_feature_entitlements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id uuid NOT NULL,
  feature_definition_id uuid NOT NULL,
  is_enabled boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_plan_feature_entitlements_plan FOREIGN KEY (plan_id) REFERENCES platform.plans(id),
  CONSTRAINT fk_plan_feature_entitlements_feature FOREIGN KEY (feature_definition_id) REFERENCES platform.feature_definitions(id),
  CONSTRAINT uq_plan_feature_entitlements_plan_feature UNIQUE (plan_id, feature_definition_id)
);

CREATE TABLE platform.plan_addons (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code citext NOT NULL,
  name text NOT NULL,
  description text,
  status plan_status_enum NOT NULL DEFAULT 'draft',
  price positive_money NOT NULL DEFAULT 0,
  currency currency_code NOT NULL DEFAULT 'USD',
  billing_interval billing_interval_enum NOT NULL DEFAULT 'monthly',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  CONSTRAINT uq_plan_addons_code UNIQUE (code)
);

CREATE TABLE platform.addon_quota_deltas (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  addon_id uuid NOT NULL,
  quota_definition_id uuid NOT NULL,
  delta_value numeric(18,4) NOT NULL CHECK (delta_value <> 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_addon_quota_deltas_addon FOREIGN KEY (addon_id) REFERENCES platform.plan_addons(id),
  CONSTRAINT fk_addon_quota_deltas_quota FOREIGN KEY (quota_definition_id) REFERENCES platform.quota_definitions(id),
  CONSTRAINT uq_addon_quota_deltas_addon_quota UNIQUE (addon_id, quota_definition_id)
);

CREATE TABLE platform.addon_feature_entitlements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  addon_id uuid NOT NULL,
  feature_definition_id uuid NOT NULL,
  is_enabled boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_addon_feature_entitlements_addon FOREIGN KEY (addon_id) REFERENCES platform.plan_addons(id),
  CONSTRAINT fk_addon_feature_entitlements_feature FOREIGN KEY (feature_definition_id) REFERENCES platform.feature_definitions(id),
  CONSTRAINT uq_addon_feature_entitlements_addon_feature UNIQUE (addon_id, feature_definition_id)
);

CREATE TABLE platform.infra_pools (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  pool_key citext NOT NULL,
  region region_enum NOT NULL,
  isolation_tier isolation_tier_enum NOT NULL DEFAULT 'shared',
  database_cluster_ref text,
  search_cluster_ref text,
  storage_bucket_prefix text,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','draining','retired')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_infra_pools_pool_key UNIQUE (pool_key)
);

CREATE TABLE platform.tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  legal_entity_name text,
  tenant_type tenant_type_enum NOT NULL,
  primary_admin_email citext NOT NULL,
  plan_id uuid,
  status tenant_status_enum NOT NULL DEFAULT 'provisioning',
  isolation_tier isolation_tier_enum NOT NULL DEFAULT 'shared',
  region region_enum NOT NULL DEFAULT 'US',
  data_residency_zone text,
  infra_pool_id uuid,
  activated_at timestamptz,
  suspended_at timestamptz,
  churned_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  lock_version bigint NOT NULL DEFAULT 0,
  CONSTRAINT fk_tenants_plan FOREIGN KEY (plan_id) REFERENCES platform.plans(id),
  CONSTRAINT fk_tenants_infra_pool FOREIGN KEY (infra_pool_id) REFERENCES platform.infra_pools(id),
  CONSTRAINT uq_tenants_id UNIQUE (id),
  CONSTRAINT chk_tenants_active_has_activated CHECK (status <> 'active' OR activated_at IS NOT NULL)
);
COMMENT ON TABLE platform.tenants IS 'Global tenant registry; tenant-scoped tables reference this and enforce tenant isolation with RLS.';

CREATE TABLE platform.tenant_domains (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  domain citext NOT NULL,
  is_primary boolean NOT NULL DEFAULT false,
  verification_status text NOT NULL DEFAULT 'pending' CHECK (verification_status IN ('pending','verified','failed','revoked')),
  verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_tenant_domains_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT uq_tenant_domains_domain UNIQUE (domain)
);
CREATE UNIQUE INDEX uq_tenant_domains_one_primary ON platform.tenant_domains(tenant_id) WHERE is_primary;

CREATE TABLE platform.tenant_lifecycle_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  event_key text NOT NULL,
  from_status tenant_status_enum,
  to_status tenant_status_enum,
  actor_platform_user_id uuid,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  reason text,
  CONSTRAINT fk_tenant_lifecycle_events_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
);

CREATE TABLE platform.tenant_provisioning_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  idempotency_key text NOT NULL,
  status sync_status_enum NOT NULL DEFAULT 'pending',
  started_at timestamptz,
  completed_at timestamptz,
  failed_at timestamptz,
  error_code text,
  error_message text,
  retry_count integer NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_tenant_provisioning_jobs_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT uq_tenant_provisioning_jobs_idempotency UNIQUE (tenant_id, idempotency_key),
  CONSTRAINT chk_tenant_provisioning_jobs_finished_once CHECK (completed_at IS NULL OR failed_at IS NULL)
);

CREATE TABLE platform.tenant_provisioning_steps (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provisioning_job_id uuid NOT NULL,
  step_key text NOT NULL,
  status sync_status_enum NOT NULL DEFAULT 'pending',
  started_at timestamptz,
  completed_at timestamptz,
  error_message text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_tenant_provisioning_steps_job FOREIGN KEY (provisioning_job_id) REFERENCES platform.tenant_provisioning_jobs(id),
  CONSTRAINT uq_tenant_provisioning_steps_job_step UNIQUE (provisioning_job_id, step_key)
);

CREATE TABLE platform.platform_permissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  permission_key citext NOT NULL,
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_platform_permissions_key UNIQUE (permission_key)
);

CREATE TABLE platform.platform_roles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  role_key citext NOT NULL,
  name text NOT NULL,
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_platform_roles_key UNIQUE (role_key)
);

CREATE TABLE platform.platform_role_permissions (
  role_id uuid NOT NULL,
  permission_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (role_id, permission_id),
  CONSTRAINT fk_platform_role_permissions_role FOREIGN KEY (role_id) REFERENCES platform.platform_roles(id),
  CONSTRAINT fk_platform_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES platform.platform_permissions(id)
);

CREATE TABLE platform.platform_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email citext NOT NULL,
  display_name text NOT NULL,
  status platform_user_status_enum NOT NULL DEFAULT 'invited',
  last_login_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  CONSTRAINT uq_platform_users_email UNIQUE (email)
);

CREATE TABLE platform.platform_user_roles (
  platform_user_id uuid NOT NULL,
  role_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (platform_user_id, role_id),
  CONSTRAINT fk_platform_user_roles_user FOREIGN KEY (platform_user_id) REFERENCES platform.platform_users(id),
  CONSTRAINT fk_platform_user_roles_role FOREIGN KEY (role_id) REFERENCES platform.platform_roles(id)
);

CREATE TABLE platform.support_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  platform_user_id uuid NOT NULL,
  approved_by_user_id uuid,
  reason text NOT NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  ended_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_support_sessions_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_support_sessions_platform_user FOREIGN KEY (platform_user_id) REFERENCES platform.platform_users(id),
  CONSTRAINT chk_support_sessions_time CHECK (expires_at > started_at)
);

CREATE TABLE platform.audit_logs (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  tenant_id uuid,
  actor_type audit_actor_type_enum NOT NULL,
  actor_tenant_user_id uuid,
  actor_platform_user_id uuid,
  action_key text NOT NULL,
  object_schema text NOT NULL,
  object_table text NOT NULL,
  object_id uuid,
  before_state jsonb,
  after_state jsonb,
  diff_state jsonb,
  ip_address inet,
  user_agent text,
  request_id text,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id, occurred_at),
  CONSTRAINT fk_audit_logs_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
) PARTITION BY RANGE (occurred_at);
CREATE TABLE platform.audit_logs_default PARTITION OF platform.audit_logs DEFAULT;
COMMENT ON TABLE platform.audit_logs IS 'Append-only audit log. JSONB is allowed only for immutable before/after/diff snapshots.';

CREATE TABLE platform.support_tickets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid,
  requester_email citext NOT NULL,
  subject text NOT NULL,
  description text NOT NULL,
  priority ticket_priority_enum NOT NULL DEFAULT 'P3',
  status ticket_status_enum NOT NULL DEFAULT 'open',
  assigned_platform_user_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  closed_at timestamptz,
  CONSTRAINT fk_support_tickets_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_support_tickets_assigned_user FOREIGN KEY (assigned_platform_user_id) REFERENCES platform.platform_users(id)
);

CREATE TABLE platform.sla_policies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_key citext NOT NULL,
  name text NOT NULL,
  severity sla_severity_enum NOT NULL,
  response_minutes integer NOT NULL CHECK (response_minutes > 0),
  resolution_minutes integer NOT NULL CHECK (resolution_minutes >= response_minutes),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_sla_policies_key UNIQUE (policy_key)
);

CREATE TABLE platform.compliance_frameworks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  framework compliance_framework_enum NOT NULL,
  display_name text NOT NULL,
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_compliance_frameworks_framework UNIQUE (framework)
);

CREATE TABLE platform.compliance_framework_regions (
  framework_id uuid NOT NULL,
  region region_enum NOT NULL,
  PRIMARY KEY (framework_id, region),
  CONSTRAINT fk_compliance_framework_regions_framework FOREIGN KEY (framework_id) REFERENCES platform.compliance_frameworks(id)
);

CREATE TABLE platform.tenant_compliance_frameworks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  framework_id uuid NOT NULL,
  enabled_at timestamptz NOT NULL DEFAULT now(),
  disabled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_tenant_compliance_frameworks_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_tenant_compliance_frameworks_framework FOREIGN KEY (framework_id) REFERENCES platform.compliance_frameworks(id),
  CONSTRAINT uq_tenant_compliance_frameworks_active UNIQUE (tenant_id, framework_id, disabled_at)
);

CREATE TABLE platform.ai_model_definitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider ai_provider_enum NOT NULL,
  model_key citext NOT NULL,
  display_name text NOT NULL,
  max_context_tokens integer CHECK (max_context_tokens IS NULL OR max_context_tokens > 0),
  supports_embeddings boolean NOT NULL DEFAULT false,
  supports_audio boolean NOT NULL DEFAULT false,
  supports_video boolean NOT NULL DEFAULT false,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_ai_model_definitions_provider_model UNIQUE (provider, model_key)
);

CREATE TABLE platform.ai_model_region_restrictions (
  model_definition_id uuid NOT NULL,
  region region_enum NOT NULL,
  restriction_reason text,
  PRIMARY KEY (model_definition_id, region),
  CONSTRAINT fk_ai_model_region_restrictions_model FOREIGN KEY (model_definition_id) REFERENCES platform.ai_model_definitions(id)
);

CREATE TABLE platform.feature_flag_registry (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  flag_key citext NOT NULL,
  description text NOT NULL,
  default_enabled boolean NOT NULL DEFAULT false,
  rollout_percentage percent_0_100 NOT NULL DEFAULT 0,
  kill_switch boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_feature_flag_registry_key UNIQUE (flag_key)
);

CREATE TABLE platform.feature_flag_tenant_overrides (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  feature_flag_id uuid NOT NULL,
  is_enabled boolean NOT NULL,
  reason text,
  created_by_platform_user_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz,
  CONSTRAINT fk_feature_flag_tenant_overrides_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_feature_flag_tenant_overrides_flag FOREIGN KEY (feature_flag_id) REFERENCES platform.feature_flag_registry(id),
  CONSTRAINT fk_feature_flag_tenant_overrides_created_by FOREIGN KEY (created_by_platform_user_id) REFERENCES platform.platform_users(id),
  CONSTRAINT uq_feature_flag_tenant_overrides_active UNIQUE (tenant_id, feature_flag_id, expires_at)
);

CREATE TABLE platform.api_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_label citext NOT NULL,
  released_at timestamptz NOT NULL,
  deprecated_at timestamptz,
  sunset_at timestamptz,
  migration_guide_url text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_api_versions_label UNIQUE (version_label),
  CONSTRAINT chk_api_versions_sunset_after_deprecation CHECK (sunset_at IS NULL OR deprecated_at IS NOT NULL AND sunset_at > deprecated_at)
);

CREATE TABLE platform.deployments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  environment text NOT NULL CHECK (environment IN ('dev','qa','staging','production')),
  version_label text NOT NULL,
  rollout_strategy rollout_strategy_enum NOT NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  rollback_of_deployment_id uuid,
  status text NOT NULL DEFAULT 'running' CHECK (status IN ('running','succeeded','failed','rolled_back')),
  CONSTRAINT fk_deployments_rollback FOREIGN KEY (rollback_of_deployment_id) REFERENCES platform.deployments(id)
);

CREATE TABLE platform.slo_definitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slo_key citext NOT NULL,
  service_name text NOT NULL,
  objective_percent percent_0_100 NOT NULL,
  window_days integer NOT NULL CHECK (window_days > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_slo_definitions_key UNIQUE (slo_key)
);

CREATE TABLE platform.error_budget_status (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slo_definition_id uuid NOT NULL,
  period_start date NOT NULL,
  period_end date NOT NULL,
  consumed_percent percent_0_100 NOT NULL DEFAULT 0,
  burn_rate numeric(12,4) NOT NULL DEFAULT 0 CHECK (burn_rate >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_error_budget_status_slo FOREIGN KEY (slo_definition_id) REFERENCES platform.slo_definitions(id),
  CONSTRAINT uq_error_budget_status_slo_period UNIQUE (slo_definition_id, period_start, period_end),
  CONSTRAINT chk_error_budget_status_period CHECK (period_end >= period_start)
);

CREATE TABLE platform.ai_quality_metrics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid,
  action_type ai_action_type_enum NOT NULL,
  model_definition_id uuid,
  sample_period_start date NOT NULL,
  sample_period_end date NOT NULL,
  sample_count integer NOT NULL CHECK (sample_count >= 0),
  human_override_rate percent_0_100,
  bias_flag_rate percent_0_100,
  avg_confidence confidence_score,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_ai_quality_metrics_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_ai_quality_metrics_model FOREIGN KEY (model_definition_id) REFERENCES platform.ai_model_definitions(id),
  CONSTRAINT chk_ai_quality_metrics_period CHECK (sample_period_end >= sample_period_start)
);

CREATE TABLE platform.ai_governance_alerts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid,
  action_type ai_action_type_enum NOT NULL,
  severity sla_severity_enum NOT NULL,
  alert_key text NOT NULL,
  title text NOT NULL,
  description text NOT NULL,
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','acknowledged','resolved','dismissed')),
  opened_at timestamptz NOT NULL DEFAULT now(),
  resolved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_ai_governance_alerts_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
);

CREATE TABLE platform.ai_governance_alert_evidence (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_id uuid NOT NULL,
  evidence_schema text NOT NULL,
  evidence_table text NOT NULL,
  evidence_id uuid NOT NULL,
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_ai_governance_alert_evidence_alert FOREIGN KEY (alert_id) REFERENCES platform.ai_governance_alerts(id)
);

CREATE TABLE platform.benchmark_cohorts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cohort_key citext NOT NULL,
  description text,
  region region_enum,
  tenant_type tenant_type_enum,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_benchmark_cohorts_key UNIQUE (cohort_key)
);

CREATE TABLE platform.benchmark_metrics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cohort_id uuid NOT NULL,
  metric_key text NOT NULL,
  period_start date NOT NULL,
  period_end date NOT NULL,
  metric_value numeric(18,6) NOT NULL,
  sample_size integer NOT NULL CHECK (sample_size >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_benchmark_metrics_cohort FOREIGN KEY (cohort_id) REFERENCES platform.benchmark_cohorts(id),
  CONSTRAINT uq_benchmark_metrics_cohort_metric_period UNIQUE (cohort_id, metric_key, period_start, period_end),
  CONSTRAINT chk_benchmark_metrics_period CHECK (period_end >= period_start)
);

INSERT INTO platform.allowed_jsonb_columns(schema_name, table_name, column_name, allowed_reason) VALUES
('platform','audit_logs','before_state','Immutable audit before snapshot'),
('platform','audit_logs','after_state','Immutable audit after snapshot'),
('platform','audit_logs','diff_state','Immutable audit diff snapshot')
ON CONFLICT DO NOTHING;
-- ============================================================
-- File 02: Tenant identity, RBAC/ABAC, configuration, branding, calendars, API keys
-- ============================================================

CREATE TABLE tenant.business_units (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  parent_business_unit_id uuid,
  code citext NOT NULL,
  name text NOT NULL,
  cost_center text,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','archived')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  CONSTRAINT uq_business_units_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_business_units_tenant_code UNIQUE (tenant_id, code),
  CONSTRAINT fk_business_units_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_business_units_parent FOREIGN KEY (tenant_id, parent_business_unit_id) REFERENCES tenant.business_units(tenant_id, id)
);

CREATE TABLE tenant.users (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  business_unit_id uuid,
  email citext NOT NULL,
  display_name text NOT NULL,
  given_name text,
  family_name text,
  status tenant_user_status_enum NOT NULL DEFAULT 'invited',
  provisioning_source text NOT NULL DEFAULT 'manual' CHECK (provisioning_source IN ('manual','sso_jit','scim','api')),
  is_tenant_admin boolean NOT NULL DEFAULT false,
  password_hash text,
  email_verified_at timestamptz,
  last_login_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  CONSTRAINT uq_users_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_users_tenant_email UNIQUE (tenant_id, email),
  CONSTRAINT fk_users_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_users_business_unit FOREIGN KEY (tenant_id, business_unit_id) REFERENCES tenant.business_units(tenant_id, id)
);

CREATE TABLE tenant.user_mfa_factors (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  method mfa_method_enum NOT NULL,
  secret_ref text,
  phone_e164 text,
  is_primary boolean NOT NULL DEFAULT false,
  enabled_at timestamptz NOT NULL DEFAULT now(),
  disabled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_user_mfa_factors_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_user_mfa_factors_user FOREIGN KEY (tenant_id, user_id) REFERENCES tenant.users(tenant_id, id)
);
CREATE UNIQUE INDEX uq_user_mfa_factors_primary ON tenant.user_mfa_factors(tenant_id, user_id) WHERE is_primary AND disabled_at IS NULL;

CREATE TABLE tenant.user_sessions (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  session_token_hash text NOT NULL,
  ip_address inet,
  user_agent text,
  mfa_verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  PRIMARY KEY (id),
  CONSTRAINT uq_user_sessions_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_user_sessions_token_hash UNIQUE (session_token_hash),
  CONSTRAINT fk_user_sessions_user FOREIGN KEY (tenant_id, user_id) REFERENCES tenant.users(tenant_id, id),
  CONSTRAINT chk_user_sessions_expires_after_created CHECK (expires_at > created_at)
);

CREATE TABLE tenant.password_reset_tokens (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  token_hmac text NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','used','expired','revoked')),
  requested_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  used_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_password_reset_tokens_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_password_reset_tokens_hmac UNIQUE (tenant_id, token_hmac),
  CONSTRAINT fk_password_reset_tokens_user FOREIGN KEY (tenant_id, user_id) REFERENCES tenant.users(tenant_id, id),
  CONSTRAINT chk_password_reset_tokens_expires_after_requested CHECK (expires_at > requested_at)
);
CREATE UNIQUE INDEX uq_password_reset_tokens_one_active ON tenant.password_reset_tokens(tenant_id, user_id) WHERE status = 'pending';

CREATE TABLE tenant.email_verification_tokens (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  token_hmac text NOT NULL,
  email citext NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','used','expired','revoked')),
  requested_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  used_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_email_verification_tokens_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_email_verification_tokens_hmac UNIQUE (tenant_id, token_hmac),
  CONSTRAINT fk_email_verification_tokens_user FOREIGN KEY (tenant_id, user_id) REFERENCES tenant.users(tenant_id, id),
  CONSTRAINT chk_email_verification_tokens_expires_after_requested CHECK (expires_at > requested_at)
);

CREATE TABLE tenant.roles (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  role_key citext NOT NULL,
  name text NOT NULL,
  description text,
  is_system_role boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  CONSTRAINT uq_roles_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_roles_tenant_key UNIQUE (tenant_id, role_key),
  CONSTRAINT fk_roles_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
);

CREATE TABLE tenant.permissions (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  permission_key citext NOT NULL,
  resource_key citext NOT NULL,
  action_key citext NOT NULL,
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_permissions_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_permissions_tenant_key UNIQUE (tenant_id, permission_key),
  CONSTRAINT fk_permissions_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
);

CREATE TABLE tenant.permission_condition_groups (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  permission_id uuid NOT NULL,
  group_operator text NOT NULL DEFAULT 'AND' CHECK (group_operator IN ('AND','OR')),
  sort_order integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_permission_condition_groups_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_permission_condition_groups_permission FOREIGN KEY (tenant_id, permission_id) REFERENCES tenant.permissions(tenant_id, id)
);

CREATE TABLE tenant.permission_conditions (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  condition_group_id uuid NOT NULL,
  attribute_key citext NOT NULL,
  operator condition_operator_enum NOT NULL,
  value_text text,
  value_number numeric(18,6),
  value_bool boolean,
  value_date date,
  sort_order integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_permission_conditions_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_permission_conditions_group FOREIGN KEY (tenant_id, condition_group_id) REFERENCES tenant.permission_condition_groups(tenant_id, id),
  CONSTRAINT chk_permission_conditions_one_value CHECK (
    (CASE WHEN value_text IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN value_number IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN value_bool IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN value_date IS NULL THEN 0 ELSE 1 END) <= 1
  )
);

CREATE TABLE tenant.role_permissions (
  tenant_id uuid NOT NULL,
  role_id uuid NOT NULL,
  permission_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, role_id, permission_id),
  CONSTRAINT fk_role_permissions_role FOREIGN KEY (tenant_id, role_id) REFERENCES tenant.roles(tenant_id, id),
  CONSTRAINT fk_role_permissions_permission FOREIGN KEY (tenant_id, permission_id) REFERENCES tenant.permissions(tenant_id, id)
);

CREATE TABLE tenant.user_role_assignments (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  role_id uuid NOT NULL,
  business_unit_id uuid,
  starts_at timestamptz NOT NULL DEFAULT now(),
  ends_at timestamptz,
  assigned_by_user_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_user_role_assignments_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_user_role_assignments_user FOREIGN KEY (tenant_id, user_id) REFERENCES tenant.users(tenant_id, id),
  CONSTRAINT fk_user_role_assignments_role FOREIGN KEY (tenant_id, role_id) REFERENCES tenant.roles(tenant_id, id),
  CONSTRAINT fk_user_role_assignments_business_unit FOREIGN KEY (tenant_id, business_unit_id) REFERENCES tenant.business_units(tenant_id, id),
  CONSTRAINT fk_user_role_assignments_assigned_by FOREIGN KEY (tenant_id, assigned_by_user_id) REFERENCES tenant.users(tenant_id, id),
  CONSTRAINT chk_user_role_assignments_dates CHECK (ends_at IS NULL OR ends_at > starts_at)
);
CREATE UNIQUE INDEX uq_user_role_assignments_active ON tenant.user_role_assignments(tenant_id, user_id, role_id, COALESCE(business_unit_id, '00000000-0000-0000-0000-000000000000'::uuid)) WHERE ends_at IS NULL;

CREATE TABLE tenant.abac_policies (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  policy_key citext NOT NULL,
  name text NOT NULL,
  effect abac_effect_enum NOT NULL,
  resource_key citext NOT NULL,
  action_key citext NOT NULL,
  priority integer NOT NULL DEFAULT 100 CHECK (priority >= 0),
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  PRIMARY KEY (id),
  CONSTRAINT uq_abac_policies_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_abac_policies_tenant_key UNIQUE (tenant_id, policy_key),
  CONSTRAINT fk_abac_policies_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
);

CREATE TABLE tenant.abac_policy_condition_groups (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  policy_id uuid NOT NULL,
  parent_group_id uuid,
  group_operator text NOT NULL CHECK (group_operator IN ('AND','OR')),
  sort_order integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_abac_policy_condition_groups_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_abac_policy_condition_groups_policy FOREIGN KEY (tenant_id, policy_id) REFERENCES tenant.abac_policies(tenant_id, id),
  CONSTRAINT fk_abac_policy_condition_groups_parent FOREIGN KEY (tenant_id, parent_group_id) REFERENCES tenant.abac_policy_condition_groups(tenant_id, id)
);

CREATE TABLE tenant.abac_policy_conditions (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  condition_group_id uuid NOT NULL,
  attribute_key citext NOT NULL,
  operator condition_operator_enum NOT NULL,
  value_text text,
  value_number numeric(18,6),
  value_bool boolean,
  value_date date,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_abac_policy_conditions_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_abac_policy_conditions_group FOREIGN KEY (tenant_id, condition_group_id) REFERENCES tenant.abac_policy_condition_groups(tenant_id, id),
  CONSTRAINT chk_abac_policy_conditions_one_value CHECK (
    (CASE WHEN value_text IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN value_number IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN value_bool IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN value_date IS NULL THEN 0 ELSE 1 END) <= 1
  )
);

CREATE TABLE tenant.field_permissions (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  resource_key citext NOT NULL,
  field_key citext NOT NULL,
  redaction field_redaction_enum NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_field_permissions_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_field_permissions_resource_field UNIQUE (tenant_id, resource_key, field_key),
  CONSTRAINT fk_field_permissions_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
);

CREATE TABLE tenant.field_permission_roles (
  tenant_id uuid NOT NULL,
  field_permission_id uuid NOT NULL,
  role_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, field_permission_id, role_id),
  CONSTRAINT fk_field_permission_roles_field_permission FOREIGN KEY (tenant_id, field_permission_id) REFERENCES tenant.field_permissions(tenant_id, id),
  CONSTRAINT fk_field_permission_roles_role FOREIGN KEY (tenant_id, role_id) REFERENCES tenant.roles(tenant_id, id)
);

CREATE TABLE tenant.delegations (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  delegator_user_id uuid NOT NULL,
  delegate_user_id uuid NOT NULL,
  role_id uuid,
  starts_at timestamptz NOT NULL,
  ends_at timestamptz NOT NULL,
  status delegation_status_enum NOT NULL DEFAULT 'active',
  reason text NOT NULL,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_delegations_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_delegations_delegator FOREIGN KEY (tenant_id, delegator_user_id) REFERENCES tenant.users(tenant_id, id),
  CONSTRAINT fk_delegations_delegate FOREIGN KEY (tenant_id, delegate_user_id) REFERENCES tenant.users(tenant_id, id),
  CONSTRAINT fk_delegations_role FOREIGN KEY (tenant_id, role_id) REFERENCES tenant.roles(tenant_id, id),
  CONSTRAINT chk_delegations_dates CHECK (ends_at > starts_at),
  CONSTRAINT chk_delegations_not_self CHECK (delegator_user_id <> delegate_user_id)
);

CREATE TABLE tenant.sso_configs (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  provider sso_provider_enum NOT NULL,
  status sso_status_enum NOT NULL DEFAULT 'disabled',
  issuer_url text,
  client_id text,
  metadata_url text,
  enforcement_mode text NOT NULL DEFAULT 'optional' CHECK (enforcement_mode IN ('optional','required_for_admins','required_for_all')),
  jit_provisioning_enabled boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  PRIMARY KEY (id),
  CONSTRAINT uq_sso_configs_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_sso_configs_tenant_provider UNIQUE (tenant_id, provider),
  CONSTRAINT fk_sso_configs_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
);

CREATE TABLE tenant.sso_attribute_mappings (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  sso_config_id uuid NOT NULL,
  platform_attribute citext NOT NULL,
  provider_claim text NOT NULL,
  is_required boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_sso_attribute_mappings_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_sso_attribute_mappings_config_attr UNIQUE (tenant_id, sso_config_id, platform_attribute),
  CONSTRAINT fk_sso_attribute_mappings_config FOREIGN KEY (tenant_id, sso_config_id) REFERENCES tenant.sso_configs(tenant_id, id)
);

CREATE TABLE tenant.sso_group_role_mappings (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  sso_config_id uuid NOT NULL,
  provider_group text NOT NULL,
  role_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_sso_group_role_mappings_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_sso_group_role_mappings_config_group UNIQUE (tenant_id, sso_config_id, provider_group),
  CONSTRAINT fk_sso_group_role_mappings_config FOREIGN KEY (tenant_id, sso_config_id) REFERENCES tenant.sso_configs(tenant_id, id),
  CONSTRAINT fk_sso_group_role_mappings_role FOREIGN KEY (tenant_id, role_id) REFERENCES tenant.roles(tenant_id, id)
);

CREATE TABLE tenant.security_events (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  event_type security_event_type_enum NOT NULL,
  outcome security_event_outcome_enum NOT NULL,
  severity security_event_severity_enum NOT NULL DEFAULT 'info',
  ip_address inet,
  user_agent text,
  request_id text,
  provider_event_id text,
  raw_event_snapshot jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id, occurred_at),
  CONSTRAINT uq_security_events_tenant_id UNIQUE (tenant_id, id, occurred_at),
  CONSTRAINT fk_security_events_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_security_events_user FOREIGN KEY (tenant_id, user_id) REFERENCES tenant.users(tenant_id, id)
) PARTITION BY RANGE (occurred_at);
CREATE TABLE tenant.security_events_default PARTITION OF tenant.security_events DEFAULT;
COMMENT ON TABLE tenant.security_events IS 'Append-only security event stream. raw_event_snapshot is allowed JSONB for immutable provider/security payload capture.';

CREATE TABLE tenant.tenant_branding (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  brand_name text NOT NULL,
  primary_color text CHECK (primary_color IS NULL OR primary_color ~ '^#[0-9A-Fa-f]{6}$'),
  secondary_color text CHECK (secondary_color IS NULL OR secondary_color ~ '^#[0-9A-Fa-f]{6}$'),
  logo_asset_ref text,
  favicon_asset_ref text,
  default_locale text NOT NULL DEFAULT 'en',
  is_default boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  PRIMARY KEY (id),
  CONSTRAINT uq_tenant_branding_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_tenant_branding_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
);
CREATE UNIQUE INDEX uq_tenant_branding_default ON tenant.tenant_branding(tenant_id) WHERE is_default AND deleted_at IS NULL;

CREATE TABLE tenant.white_label_domains (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  branding_id uuid NOT NULL,
  domain citext NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','verified','active','failed','disabled')),
  verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_white_label_domains_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_white_label_domains_domain UNIQUE (domain),
  CONSTRAINT fk_white_label_domains_branding FOREIGN KEY (tenant_id, branding_id) REFERENCES tenant.tenant_branding(tenant_id, id)
);

CREATE TABLE platform.config_definitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  config_key citext NOT NULL,
  name text NOT NULL,
  description text,
  value_type config_value_type_enum NOT NULL,
  default_bool boolean,
  default_text text,
  default_number numeric(18,6),
  default_integer bigint,
  validation_regex text,
  min_number numeric(18,6),
  max_number numeric(18,6),
  is_secret boolean NOT NULL DEFAULT false,
  is_versioned boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_config_definitions_key UNIQUE (config_key),
  CONSTRAINT chk_config_definitions_one_default CHECK (
    (CASE WHEN default_bool IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN default_text IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN default_number IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN default_integer IS NULL THEN 0 ELSE 1 END) <= 1
  )
);

CREATE TABLE platform.config_scope_levels (
  config_definition_id uuid NOT NULL,
  scope_level config_scope_enum NOT NULL,
  PRIMARY KEY (config_definition_id, scope_level),
  CONSTRAINT fk_config_scope_levels_definition FOREIGN KEY (config_definition_id) REFERENCES platform.config_definitions(id)
);

CREATE TABLE platform.config_allowed_values (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  config_definition_id uuid NOT NULL,
  allowed_value text NOT NULL,
  display_order integer NOT NULL DEFAULT 0,
  CONSTRAINT fk_config_allowed_values_definition FOREIGN KEY (config_definition_id) REFERENCES platform.config_definitions(id),
  CONSTRAINT uq_config_allowed_values_definition_value UNIQUE (config_definition_id, allowed_value)
);

CREATE TABLE tenant.config_values (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  config_definition_id uuid NOT NULL,
  scope_level config_scope_enum NOT NULL,
  business_unit_id uuid,
  team_id uuid,
  user_id uuid,
  value_bool boolean,
  value_text text,
  value_number numeric(18,6),
  value_integer bigint,
  secret_ref text,
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  is_active boolean NOT NULL DEFAULT true,
  created_by_user_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_config_values_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_config_values_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_config_values_definition FOREIGN KEY (config_definition_id) REFERENCES platform.config_definitions(id),
  CONSTRAINT fk_config_values_business_unit FOREIGN KEY (tenant_id, business_unit_id) REFERENCES tenant.business_units(tenant_id, id),
  CONSTRAINT fk_config_values_user FOREIGN KEY (tenant_id, user_id) REFERENCES tenant.users(tenant_id, id),
  CONSTRAINT fk_config_values_created_by FOREIGN KEY (tenant_id, created_by_user_id) REFERENCES tenant.users(tenant_id, id),
  CONSTRAINT chk_config_values_one_value CHECK (
    (CASE WHEN value_bool IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN value_text IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN value_number IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN value_integer IS NULL THEN 0 ELSE 1 END) +
    (CASE WHEN secret_ref IS NULL THEN 0 ELSE 1 END) = 1
  ),
  CONSTRAINT chk_config_values_scope CHECK (
    (scope_level = 'tenant' AND business_unit_id IS NULL AND team_id IS NULL AND user_id IS NULL) OR
    (scope_level = 'business_unit' AND business_unit_id IS NOT NULL AND team_id IS NULL AND user_id IS NULL) OR
    (scope_level = 'team' AND team_id IS NOT NULL AND user_id IS NULL) OR
    (scope_level = 'user' AND user_id IS NOT NULL)
  )
);
CREATE UNIQUE INDEX uq_config_values_active_scope ON tenant.config_values(tenant_id, config_definition_id, scope_level, COALESCE(business_unit_id, '00000000-0000-0000-0000-000000000000'::uuid), COALESCE(team_id, '00000000-0000-0000-0000-000000000000'::uuid), COALESCE(user_id, '00000000-0000-0000-0000-000000000000'::uuid)) WHERE is_active;

CREATE TABLE tenant.config_change_log (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  config_value_id uuid NOT NULL,
  old_value_text text,
  new_value_text text NOT NULL,
  changed_by_user_id uuid,
  change_reason text NOT NULL,
  changed_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_config_change_log_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_config_change_log_config_value FOREIGN KEY (tenant_id, config_value_id) REFERENCES tenant.config_values(tenant_id, id),
  CONSTRAINT fk_config_change_log_changed_by FOREIGN KEY (tenant_id, changed_by_user_id) REFERENCES tenant.users(tenant_id, id)
);

CREATE TABLE tenant.working_calendars (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  timezone text NOT NULL,
  is_default boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  PRIMARY KEY (id),
  CONSTRAINT uq_working_calendars_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_working_calendars_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
);
CREATE UNIQUE INDEX uq_working_calendars_default ON tenant.working_calendars(tenant_id) WHERE is_default AND deleted_at IS NULL;

CREATE TABLE tenant.working_calendar_days (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  working_calendar_id uuid NOT NULL,
  day_of_week smallint NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
  start_time time NOT NULL,
  end_time time NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_working_calendar_days_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_working_calendar_days_calendar_day UNIQUE (tenant_id, working_calendar_id, day_of_week),
  CONSTRAINT fk_working_calendar_days_calendar FOREIGN KEY (tenant_id, working_calendar_id) REFERENCES tenant.working_calendars(tenant_id, id),
  CONSTRAINT chk_working_calendar_days_time CHECK (end_time > start_time)
);

CREATE TABLE tenant.calendar_holidays (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  working_calendar_id uuid NOT NULL,
  holiday_date date NOT NULL,
  name text NOT NULL,
  is_working_day_override boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_calendar_holidays_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_calendar_holidays_calendar_date UNIQUE (tenant_id, working_calendar_id, holiday_date),
  CONSTRAINT fk_calendar_holidays_calendar FOREIGN KEY (tenant_id, working_calendar_id) REFERENCES tenant.working_calendars(tenant_id, id)
);

CREATE TABLE tenant.localization_resources (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  locale text NOT NULL,
  resource_key citext NOT NULL,
  resource_value text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_localization_resources_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_localization_resources_locale_key UNIQUE (tenant_id, locale, resource_key),
  CONSTRAINT fk_localization_resources_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
);

CREATE TABLE tenant.teams (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  business_unit_id uuid,
  name text NOT NULL,
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  PRIMARY KEY (id),
  CONSTRAINT uq_teams_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_teams_tenant_name UNIQUE (tenant_id, name),
  CONSTRAINT fk_teams_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_teams_business_unit FOREIGN KEY (tenant_id, business_unit_id) REFERENCES tenant.business_units(tenant_id, id)
);

ALTER TABLE tenant.config_values
  ADD CONSTRAINT fk_config_values_team FOREIGN KEY (tenant_id, team_id) REFERENCES tenant.teams(tenant_id, id);

CREATE TABLE tenant.team_members (
  tenant_id uuid NOT NULL,
  team_id uuid NOT NULL,
  user_id uuid NOT NULL,
  role_label text,
  joined_at timestamptz NOT NULL DEFAULT now(),
  left_at timestamptz,
  PRIMARY KEY (tenant_id, team_id, user_id),
  CONSTRAINT fk_team_members_team FOREIGN KEY (tenant_id, team_id) REFERENCES tenant.teams(tenant_id, id),
  CONSTRAINT fk_team_members_user FOREIGN KEY (tenant_id, user_id) REFERENCES tenant.users(tenant_id, id),
  CONSTRAINT chk_team_members_left_after_joined CHECK (left_at IS NULL OR left_at > joined_at)
);

CREATE TABLE tenant.api_keys (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  key_prefix text NOT NULL,
  key_hash text NOT NULL,
  rate_limit_tier text NOT NULL DEFAULT 'standard',
  created_by_user_id uuid NOT NULL,
  last_used_at timestamptz,
  revoked_at timestamptz,
  expires_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_api_keys_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_api_keys_hash UNIQUE (key_hash),
  CONSTRAINT fk_api_keys_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_api_keys_created_by FOREIGN KEY (tenant_id, created_by_user_id) REFERENCES tenant.users(tenant_id, id)
);

CREATE TABLE tenant.api_key_scopes (
  tenant_id uuid NOT NULL,
  api_key_id uuid NOT NULL,
  permission_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, api_key_id, permission_id),
  CONSTRAINT fk_api_key_scopes_api_key FOREIGN KEY (tenant_id, api_key_id) REFERENCES tenant.api_keys(tenant_id, id),
  CONSTRAINT fk_api_key_scopes_permission FOREIGN KEY (tenant_id, permission_id) REFERENCES tenant.permissions(tenant_id, id)
);

CREATE TABLE tenant.mobile_device_registrations (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  device_fingerprint_hash text NOT NULL,
  push_token_hash text,
  platform text NOT NULL CHECK (platform IN ('ios','android','web')),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','revoked','lost')),
  last_seen_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_mobile_device_registrations_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_mobile_device_registrations_device UNIQUE (tenant_id, user_id, device_fingerprint_hash),
  CONSTRAINT fk_mobile_device_registrations_user FOREIGN KEY (tenant_id, user_id) REFERENCES tenant.users(tenant_id, id)
);

CREATE TABLE tenant.domain_verifications (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  domain citext NOT NULL,
  verification_token_hash text NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','verified','failed','revoked')),
  verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_domain_verifications_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_domain_verifications_tenant_domain UNIQUE (tenant_id, domain),
  CONSTRAINT fk_domain_verifications_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
);

INSERT INTO platform.allowed_jsonb_columns(schema_name, table_name, column_name, allowed_reason) VALUES
('tenant','security_events','raw_event_snapshot','Immutable raw security/provider event snapshot')
ON CONFLICT DO NOTHING;
-- ============================================================
-- File 03: Candidate domain, consent, talent pools, privacy, EEO, dedupe
-- ============================================================

CREATE TABLE tenant.candidates (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  candidate_number text NOT NULL,
  full_name text NOT NULL,
  primary_email citext,
  primary_phone_e164 text,
  current_title text,
  current_company text,
  current_location text,
  source text,
  profile_summary text,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','archived','merged','erasure_pending','erased')),
  merged_into_candidate_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  CONSTRAINT uq_candidates_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_candidates_tenant_number UNIQUE (tenant_id, candidate_number),
  CONSTRAINT fk_candidates_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_candidates_merged_into FOREIGN KEY (tenant_id, merged_into_candidate_id) REFERENCES tenant.candidates(tenant_id, id)
);
COMMENT ON TABLE tenant.candidates IS 'Tenant-owned canonical candidate profile. Sensitive contact/EEO/docs live in separate protected child tables.';
CREATE UNIQUE INDEX uq_candidates_tenant_primary_email_active ON tenant.candidates(tenant_id, primary_email) WHERE primary_email IS NOT NULL AND deleted_at IS NULL;

CREATE TABLE tenant.candidate_contacts (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  candidate_id uuid NOT NULL,
  contact_type text NOT NULL CHECK (contact_type IN ('email','phone','linkedin','github','website','other')),
  contact_value text NOT NULL,
  normalized_value citext,
  is_primary boolean NOT NULL DEFAULT false,
  is_verified boolean NOT NULL DEFAULT false,
  verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  PRIMARY KEY (id),
  CONSTRAINT uq_candidate_contacts_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_candidate_contacts_candidate FOREIGN KEY (tenant_id, candidate_id) REFERENCES tenant.candidates(tenant_id, id),
  CONSTRAINT uq_candidate_contacts_unique_value UNIQUE (tenant_id, contact_type, normalized_value)
);
CREATE UNIQUE INDEX uq_candidate_contacts_primary ON tenant.candidate_contacts(tenant_id, candidate_id, contact_type) WHERE is_primary AND deleted_at IS NULL;

CREATE TABLE tenant.candidate_documents (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  candidate_id uuid NOT NULL,
  document_type text NOT NULL CHECK (document_type IN ('resume','cover_letter','portfolio','assessment','offer','background_check','other')),
  file_name text NOT NULL,
  storage_uri text NOT NULL,
  mime_type text NOT NULL,
  size_bytes bigint NOT NULL CHECK (size_bytes >= 0),
  checksum_sha256 text,
  is_current boolean NOT NULL DEFAULT false,
  uploaded_by_user_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  PRIMARY KEY (id),
  CONSTRAINT uq_candidate_documents_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_candidate_documents_candidate FOREIGN KEY (tenant_id, candidate_id) REFERENCES tenant.candidates(tenant_id, id),
  CONSTRAINT fk_candidate_documents_uploaded_by FOREIGN KEY (tenant_id, uploaded_by_user_id) REFERENCES tenant.users(tenant_id, id)
);
CREATE UNIQUE INDEX uq_candidate_documents_current_type ON tenant.candidate_documents(tenant_id, candidate_id, document_type) WHERE is_current AND deleted_at IS NULL;

CREATE TABLE tenant.consent_records (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  candidate_id uuid NOT NULL,
  consent_type consent_type_enum NOT NULL,
  status text NOT NULL CHECK (status IN ('granted','withdrawn','expired','not_required')),
  source text NOT NULL,
  granted_at timestamptz,
  withdrawn_at timestamptz,
  expires_at timestamptz,
  locale text,
  policy_version text,
  evidence_uri text,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_consent_records_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_consent_records_candidate FOREIGN KEY (tenant_id, candidate_id) REFERENCES tenant.candidates(tenant_id, id),
  CONSTRAINT chk_consent_records_status_dates CHECK ((status <> 'granted' OR granted_at IS NOT NULL) AND (status <> 'withdrawn' OR withdrawn_at IS NOT NULL))
);
CREATE UNIQUE INDEX uq_consent_records_active ON tenant.consent_records(tenant_id, candidate_id, consent_type) WHERE status = 'granted';

CREATE TABLE tenant.data_subject_requests (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  candidate_id uuid,
  request_type dsr_type_enum NOT NULL,
  status dsr_status_enum NOT NULL DEFAULT 'submitted',
  requester_email citext NOT NULL,
  jurisdiction text NOT NULL,
  submitted_at timestamptz NOT NULL DEFAULT now(),
  due_at timestamptz NOT NULL,
  completed_at timestamptz,
  rejection_reason text,
  completion_certificate_uri text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_data_subject_requests_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_data_subject_requests_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_data_subject_requests_candidate FOREIGN KEY (tenant_id, candidate_id) REFERENCES tenant.candidates(tenant_id, id),
  CONSTRAINT chk_data_subject_requests_due CHECK (due_at > submitted_at)
);

CREATE TABLE tenant.data_subject_request_tasks (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  dsr_id uuid NOT NULL,
  subsystem_key text NOT NULL,
  status sync_status_enum NOT NULL DEFAULT 'pending',
  completed_at timestamptz,
  error_message text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_data_subject_request_tasks_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_data_subject_request_tasks_subsystem UNIQUE (tenant_id, dsr_id, subsystem_key),
  CONSTRAINT fk_data_subject_request_tasks_dsr FOREIGN KEY (tenant_id, dsr_id) REFERENCES tenant.data_subject_requests(tenant_id, id)
);

CREATE TABLE tenant.talent_pools (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text,
  owner_user_id uuid,
  is_shared boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  PRIMARY KEY (id),
  CONSTRAINT uq_talent_pools_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_talent_pools_tenant_name UNIQUE (tenant_id, name),
  CONSTRAINT fk_talent_pools_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_talent_pools_owner FOREIGN KEY (tenant_id, owner_user_id) REFERENCES tenant.users(tenant_id, id)
);

CREATE TABLE tenant.talent_pool_entries (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  talent_pool_id uuid NOT NULL,
  candidate_id uuid NOT NULL,
  added_by_user_id uuid,
  added_at timestamptz NOT NULL DEFAULT now(),
  removed_at timestamptz,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_talent_pool_entries_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_talent_pool_entries_active UNIQUE (tenant_id, talent_pool_id, candidate_id, removed_at),
  CONSTRAINT fk_talent_pool_entries_pool FOREIGN KEY (tenant_id, talent_pool_id) REFERENCES tenant.talent_pools(tenant_id, id),
  CONSTRAINT fk_talent_pool_entries_candidate FOREIGN KEY (tenant_id, candidate_id) REFERENCES tenant.candidates(tenant_id, id),
  CONSTRAINT fk_talent_pool_entries_added_by FOREIGN KEY (tenant_id, added_by_user_id) REFERENCES tenant.users(tenant_id, id)
);

CREATE TABLE tenant.talent_pool_entry_mandates (
  tenant_id uuid NOT NULL,
  talent_pool_entry_id uuid NOT NULL,
  mandate_id uuid NOT NULL,
  associated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, talent_pool_entry_id, mandate_id),
  CONSTRAINT fk_talent_pool_entry_mandates_entry FOREIGN KEY (tenant_id, talent_pool_entry_id) REFERENCES tenant.talent_pool_entries(tenant_id, id)
);

CREATE TABLE tenant.candidate_suppressions (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  candidate_id uuid NOT NULL,
  suppression_reason suppression_reason_enum NOT NULL,
  client_id uuid,
  starts_at timestamptz NOT NULL DEFAULT now(),
  ends_at timestamptz,
  source text NOT NULL,
  comment text,
  created_by_user_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_candidate_suppressions_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_candidate_suppressions_candidate FOREIGN KEY (tenant_id, candidate_id) REFERENCES tenant.candidates(tenant_id, id),
  CONSTRAINT fk_candidate_suppressions_created_by FOREIGN KEY (tenant_id, created_by_user_id) REFERENCES tenant.users(tenant_id, id),
  CONSTRAINT chk_candidate_suppressions_period CHECK (ends_at IS NULL OR ends_at > starts_at)
);

CREATE TABLE tenant.candidate_work_history (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  candidate_id uuid NOT NULL,
  company_name text NOT NULL,
  title text NOT NULL,
  start_date date,
  end_date date,
  is_current boolean NOT NULL DEFAULT false,
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_candidate_work_history_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_candidate_work_history_candidate FOREIGN KEY (tenant_id, candidate_id) REFERENCES tenant.candidates(tenant_id, id),
  CONSTRAINT chk_candidate_work_history_dates CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

CREATE TABLE tenant.skill_taxonomy (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  skill_key citext NOT NULL,
  display_name text NOT NULL,
  category text,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_skill_taxonomy_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT uq_skill_taxonomy_tenant_key UNIQUE (tenant_id, skill_key),
  CONSTRAINT fk_skill_taxonomy_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
);

CREATE TABLE tenant.candidate_work_history_skills (
  tenant_id uuid NOT NULL,
  work_history_id uuid NOT NULL,
  skill_id uuid NOT NULL,
  PRIMARY KEY (tenant_id, work_history_id, skill_id),
  CONSTRAINT fk_candidate_work_history_skills_work FOREIGN KEY (tenant_id, work_history_id) REFERENCES tenant.candidate_work_history(tenant_id, id),
  CONSTRAINT fk_candidate_work_history_skills_skill FOREIGN KEY (tenant_id, skill_id) REFERENCES tenant.skill_taxonomy(tenant_id, id)
);

CREATE TABLE tenant.candidate_education (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  candidate_id uuid NOT NULL,
  institution text NOT NULL,
  degree text,
  field_of_study text,
  start_date date,
  end_date date,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_candidate_education_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_candidate_education_candidate FOREIGN KEY (tenant_id, candidate_id) REFERENCES tenant.candidates(tenant_id, id),
  CONSTRAINT chk_candidate_education_dates CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

CREATE TABLE tenant.candidate_skills (
  tenant_id uuid NOT NULL,
  candidate_id uuid NOT NULL,
  skill_id uuid NOT NULL,
  proficiency text CHECK (proficiency IN ('beginner','intermediate','advanced','expert')),
  years_experience numeric(4,1) CHECK (years_experience IS NULL OR years_experience >= 0),
  source text,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, candidate_id, skill_id),
  CONSTRAINT fk_candidate_skills_candidate FOREIGN KEY (tenant_id, candidate_id) REFERENCES tenant.candidates(tenant_id, id),
  CONSTRAINT fk_candidate_skills_skill FOREIGN KEY (tenant_id, skill_id) REFERENCES tenant.skill_taxonomy(tenant_id, id)
);

CREATE TABLE tenant.candidate_eeo_data (
  tenant_id uuid NOT NULL,
  candidate_id uuid NOT NULL,
  collected_at timestamptz NOT NULL DEFAULT now(),
  gender text,
  ethnicity text,
  disability_status text,
  veteran_status text,
  consent_record_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, candidate_id),
  CONSTRAINT fk_candidate_eeo_data_candidate FOREIGN KEY (tenant_id, candidate_id) REFERENCES tenant.candidates(tenant_id, id),
  CONSTRAINT fk_candidate_eeo_data_consent FOREIGN KEY (tenant_id, consent_record_id) REFERENCES tenant.consent_records(tenant_id, id)
);

CREATE TABLE tenant.candidate_duplicate_flags (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  candidate_id uuid NOT NULL,
  possible_duplicate_candidate_id uuid NOT NULL,
  score confidence_score NOT NULL,
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','confirmed_duplicate','dismissed','merged')),
  detected_at timestamptz NOT NULL DEFAULT now(),
  resolved_by_user_id uuid,
  resolved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id),
  CONSTRAINT uq_candidate_duplicate_flags_tenant_id UNIQUE (tenant_id, id),
  CONSTRAINT fk_candidate_duplicate_flags_candidate FOREIGN KEY (tenant_id, candidate_id) REFERENCES tenant.candidates(tenant_id, id),
  CONSTRAINT fk_candidate_duplicate_flags_duplicate FOREIGN KEY (tenant_id, possible_duplicate_candidate_id) REFERENCES tenant.candidates(tenant_id, id),
  CONSTRAINT fk_candidate_duplicate_flags_resolved_by FOREIGN KEY (tenant_id, resolved_by_user_id) REFERENCES tenant.users(tenant_id, id),
  CONSTRAINT chk_candidate_duplicate_flags_not_self CHECK (candidate_id <> possible_duplicate_candidate_id)
);

CREATE TABLE tenant.candidate_duplicate_flag_reasons (
  tenant_id uuid NOT NULL,
  duplicate_flag_id uuid NOT NULL,
  reason_key text NOT NULL,
  reason_detail text,
  PRIMARY KEY (tenant_id, duplicate_flag_id, reason_key),
  CONSTRAINT fk_candidate_duplicate_flag_reasons_flag FOREIGN KEY (tenant_id, duplicate_flag_id) REFERENCES tenant.candidate_duplicate_flags(tenant_id, id)
);
-- ============================================================
-- File 04: Corporate ATS - headcount, requisitions, JD, pipeline, interviews, offers, onboarding
-- ============================================================

CREATE TABLE tenant.headcount_plans (
  tenant_id uuid NOT NULL,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  business_unit_id uuid NOT NULL,
  role_family text NOT NULL,
  fiscal_period text NOT NULL,
  approved_count integer NOT NULL CHECK (approved_count >= 0),
  filled_count integer NOT NULL DEFAULT 0 CHECK (filled_count >= 0),
  budget_amount positive_money,
  currency currency_code NOT NULL DEFAULT 'USD',
  cost_center text,
  status text NOT NULL DEFAULT 'approved' CHECK (status IN ('draft','pending_approval','approved','closed','cancelled')),
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz, lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY (id), CONSTRAINT uq_headcount_plans_tenant_id UNIQUE (tenant_id,id),
  CONSTRAINT uq_headcount_plans_natural UNIQUE (tenant_id,business_unit_id,role_family,fiscal_period),
  CONSTRAINT fk_headcount_plans_bu FOREIGN KEY (tenant_id,business_unit_id) REFERENCES tenant.business_units(tenant_id,id),
  CONSTRAINT chk_headcount_plans_filled_lte_approved CHECK (filled_count <= approved_count)
);

CREATE TABLE tenant.salary_benchmarks (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), role_title text NOT NULL, level_code text NOT NULL, location text NOT NULL,
  currency currency_code NOT NULL, p25 positive_money NOT NULL, p50 positive_money NOT NULL, p75 positive_money NOT NULL, p90 positive_money NOT NULL,
  data_source text NOT NULL, as_of_date date NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id), CONSTRAINT uq_salary_benchmarks_tenant_id UNIQUE (tenant_id,id),
  CONSTRAINT uq_salary_benchmarks_natural UNIQUE (tenant_id, role_title, level_code, location, currency, as_of_date),
  CONSTRAINT fk_salary_benchmarks_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT chk_salary_benchmarks_order CHECK (p25 <= p50 AND p50 <= p75 AND p75 <= p90)
);

CREATE TABLE tenant.requisitions (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), requisition_number text NOT NULL,
  title text NOT NULL, business_unit_id uuid NOT NULL, headcount_plan_id uuid, hiring_manager_id uuid NOT NULL, recruiter_owner_id uuid,
  employment_type employment_type_enum NOT NULL, headcount_type headcount_type_enum NOT NULL DEFAULT 'new', headcount_requested integer NOT NULL CHECK (headcount_requested > 0),
  status requisition_status_enum NOT NULL DEFAULT 'draft', priority text NOT NULL DEFAULT 'normal' CHECK (priority IN ('low','normal','high','critical')),
  target_start_date date, salary_min positive_money, salary_max positive_money, salary_currency currency_code, level_code text, grade_code text,
  justification text, is_off_plan_exception boolean NOT NULL DEFAULT false, approved_at timestamptz, closed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz, lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY(id), CONSTRAINT uq_requisitions_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_requisitions_number UNIQUE(tenant_id,requisition_number),
  CONSTRAINT fk_requisitions_bu FOREIGN KEY(tenant_id,business_unit_id) REFERENCES tenant.business_units(tenant_id,id),
  CONSTRAINT fk_requisitions_headcount FOREIGN KEY(tenant_id,headcount_plan_id) REFERENCES tenant.headcount_plans(tenant_id,id),
  CONSTRAINT fk_requisitions_hiring_manager FOREIGN KEY(tenant_id,hiring_manager_id) REFERENCES tenant.users(tenant_id,id),
  CONSTRAINT fk_requisitions_recruiter FOREIGN KEY(tenant_id,recruiter_owner_id) REFERENCES tenant.users(tenant_id,id),
  CONSTRAINT chk_requisitions_salary CHECK ((salary_min IS NULL AND salary_max IS NULL AND salary_currency IS NULL) OR (salary_min IS NOT NULL AND salary_max IS NOT NULL AND salary_currency IS NOT NULL AND salary_min <= salary_max)),
  CONSTRAINT chk_requisitions_approved_at CHECK (status <> 'approved' OR approved_at IS NOT NULL)
);
COMMENT ON TABLE tenant.requisitions IS 'Structured request to hire. Locations, openings, approvals, validation issues, and JDs are normalized child rows.';

CREATE TABLE tenant.requisition_locations (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), requisition_id uuid NOT NULL,
  location_name text NOT NULL, country_code char(2), region text, city text, work_mode text NOT NULL DEFAULT 'onsite' CHECK (work_mode IN ('onsite','hybrid','remote')),
  created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_requisition_locations_tenant_id UNIQUE(tenant_id,id),
  CONSTRAINT fk_requisition_locations_req FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id)
);

CREATE TABLE tenant.requisition_openings (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), requisition_id uuid NOT NULL, opening_number integer NOT NULL CHECK(opening_number > 0),
  status text NOT NULL DEFAULT 'open' CHECK(status IN ('open','filled','cancelled')), hired_candidate_id uuid, filled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_requisition_openings_tenant_id UNIQUE(tenant_id,id),
  CONSTRAINT uq_requisition_openings_number UNIQUE(tenant_id,requisition_id,opening_number),
  CONSTRAINT fk_requisition_openings_req FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id),
  CONSTRAINT fk_requisition_openings_candidate FOREIGN KEY(tenant_id,hired_candidate_id) REFERENCES tenant.candidates(tenant_id,id)
);

CREATE TABLE tenant.competency_taxonomy (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), competency_key citext NOT NULL, display_name text NOT NULL, description text, is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_competency_taxonomy_tenant_id UNIQUE(tenant_id,id),
  CONSTRAINT uq_competency_taxonomy_key UNIQUE(tenant_id,competency_key), CONSTRAINT fk_competency_taxonomy_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id)
);

CREATE TABLE tenant.job_descriptions (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), requisition_id uuid NOT NULL,
  status job_description_status_enum NOT NULL DEFAULT 'draft', draft_text text NOT NULL, final_text text,
  generated_by text NOT NULL CHECK(generated_by IN ('ai','human','hybrid')), inclusive_language_score percent_0_100, approved_by_user_id uuid, approved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz, lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY(id), CONSTRAINT uq_job_descriptions_tenant_id UNIQUE(tenant_id,id),
  CONSTRAINT fk_job_descriptions_req FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id),
  CONSTRAINT fk_job_descriptions_approved_by FOREIGN KEY(tenant_id,approved_by_user_id) REFERENCES tenant.users(tenant_id,id),
  CONSTRAINT chk_job_descriptions_approval CHECK (status <> 'approved' OR (final_text IS NOT NULL AND approved_by_user_id IS NOT NULL AND approved_at IS NOT NULL))
);

CREATE TABLE tenant.job_description_competencies (
  tenant_id uuid NOT NULL, job_description_id uuid NOT NULL, competency_id uuid NOT NULL, competency_level competency_level_enum NOT NULL, sort_order integer NOT NULL DEFAULT 0,
  PRIMARY KEY(tenant_id,job_description_id,competency_id),
  CONSTRAINT fk_job_description_competencies_jd FOREIGN KEY(tenant_id,job_description_id) REFERENCES tenant.job_descriptions(tenant_id,id),
  CONSTRAINT fk_job_description_competencies_comp FOREIGN KEY(tenant_id,competency_id) REFERENCES tenant.competency_taxonomy(tenant_id,id)
);

CREATE TABLE tenant.inclusive_language_findings (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), job_description_id uuid NOT NULL, field_name text NOT NULL, issue_text text NOT NULL, severity text NOT NULL CHECK(severity IN ('low','medium','high')), suggestion text,
  created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_inclusive_language_findings_tenant_id UNIQUE(tenant_id,id),
  CONSTRAINT fk_inclusive_language_findings_jd FOREIGN KEY(tenant_id,job_description_id) REFERENCES tenant.job_descriptions(tenant_id,id)
);

CREATE TABLE tenant.requisition_validation_results (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), requisition_id uuid NOT NULL, validated_at timestamptz NOT NULL DEFAULT now(), model_name text, overall_status text NOT NULL CHECK(overall_status IN ('pass','warning','fail')),
  created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_requisition_validation_results_tenant_id UNIQUE(tenant_id,id),
  CONSTRAINT fk_requisition_validation_results_req FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id)
);
CREATE TABLE tenant.requisition_validation_issues (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), validation_result_id uuid NOT NULL, field_name text NOT NULL, severity text NOT NULL CHECK(severity IN ('info','warning','error')), suggestion text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_requisition_validation_issues_tenant_id UNIQUE(tenant_id,id),
  CONSTRAINT fk_requisition_validation_issues_result FOREIGN KEY(tenant_id,validation_result_id) REFERENCES tenant.requisition_validation_results(tenant_id,id)
);

CREATE TABLE tenant.pipeline_stage_definitions (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), requisition_id uuid, stage_key citext NOT NULL, name text NOT NULL, sort_order integer NOT NULL,
  is_terminal boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz,
  PRIMARY KEY(id), CONSTRAINT uq_pipeline_stage_definitions_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_pipeline_stage_definitions_key UNIQUE(tenant_id,COALESCE(requisition_id,'00000000-0000-0000-0000-000000000000'::uuid),stage_key),
  CONSTRAINT fk_pipeline_stage_definitions_req FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id)
);
CREATE TABLE tenant.pipeline_stage_auto_actions (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), stage_definition_id uuid NOT NULL, action_type text NOT NULL CHECK(action_type IN ('notify','ai_screen','schedule','webhook','create_task')), action_key text NOT NULL, is_enabled boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_pipeline_stage_auto_actions_tenant_id UNIQUE(tenant_id,id),
  CONSTRAINT fk_pipeline_stage_auto_actions_stage FOREIGN KEY(tenant_id,stage_definition_id) REFERENCES tenant.pipeline_stage_definitions(tenant_id,id)
);

CREATE TABLE tenant.applications (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), requisition_id uuid NOT NULL, candidate_id uuid NOT NULL, current_stage_id uuid,
  source text NOT NULL, status application_status_enum NOT NULL DEFAULT 'applied', applied_at timestamptz NOT NULL DEFAULT now(), rejected_reason text, withdrawn_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz, lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY(id), CONSTRAINT uq_applications_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_applications_candidate_req UNIQUE(tenant_id,candidate_id,requisition_id),
  CONSTRAINT fk_applications_req FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id),
  CONSTRAINT fk_applications_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id),
  CONSTRAINT fk_applications_stage FOREIGN KEY(tenant_id,current_stage_id) REFERENCES tenant.pipeline_stage_definitions(tenant_id,id)
);

CREATE TABLE tenant.application_questions (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), requisition_id uuid NOT NULL, question_text text NOT NULL, answer_type text NOT NULL CHECK(answer_type IN ('text','number','boolean','date','single_select','multi_select')), is_required boolean NOT NULL DEFAULT false, sort_order integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_application_questions_tenant_id UNIQUE(tenant_id,id),
  CONSTRAINT fk_application_questions_req FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id)
);
CREATE TABLE tenant.application_answers (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), application_id uuid NOT NULL, question_id uuid NOT NULL,
  answer_text text, answer_number numeric(18,6), answer_bool boolean, answer_date date, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(id), CONSTRAINT uq_application_answers_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_application_answers_question UNIQUE(tenant_id,application_id,question_id),
  CONSTRAINT fk_application_answers_application FOREIGN KEY(tenant_id,application_id) REFERENCES tenant.applications(tenant_id,id),
  CONSTRAINT fk_application_answers_question FOREIGN KEY(tenant_id,question_id) REFERENCES tenant.application_questions(tenant_id,id),
  CONSTRAINT chk_application_answers_one_value CHECK((CASE WHEN answer_text IS NULL THEN 0 ELSE 1 END)+(CASE WHEN answer_number IS NULL THEN 0 ELSE 1 END)+(CASE WHEN answer_bool IS NULL THEN 0 ELSE 1 END)+(CASE WHEN answer_date IS NULL THEN 0 ELSE 1 END)=1)
);

CREATE TABLE tenant.application_stage_history (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), application_id uuid NOT NULL, from_stage_id uuid, to_stage_id uuid NOT NULL, direction stage_direction_enum NOT NULL, changed_by_user_id uuid, changed_at timestamptz NOT NULL DEFAULT now(), reason text,
  created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_application_stage_history_tenant_id UNIQUE(tenant_id,id),
  CONSTRAINT fk_application_stage_history_application FOREIGN KEY(tenant_id,application_id) REFERENCES tenant.applications(tenant_id,id),
  CONSTRAINT fk_application_stage_history_from_stage FOREIGN KEY(tenant_id,from_stage_id) REFERENCES tenant.pipeline_stage_definitions(tenant_id,id),
  CONSTRAINT fk_application_stage_history_to_stage FOREIGN KEY(tenant_id,to_stage_id) REFERENCES tenant.pipeline_stage_definitions(tenant_id,id),
  CONSTRAINT fk_application_stage_history_user FOREIGN KEY(tenant_id,changed_by_user_id) REFERENCES tenant.users(tenant_id,id)
);

CREATE TABLE tenant.interviews (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), application_id uuid NOT NULL, interview_type interview_type_enum NOT NULL, status interview_status_enum NOT NULL DEFAULT 'scheduled', title text NOT NULL,
  scheduled_start_at timestamptz NOT NULL, scheduled_end_at timestamptz NOT NULL, timezone text NOT NULL, location text, meeting_url text,
  created_by_user_id uuid, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz, lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY(id), CONSTRAINT uq_interviews_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_interviews_application FOREIGN KEY(tenant_id,application_id) REFERENCES tenant.applications(tenant_id,id),
  CONSTRAINT fk_interviews_created_by FOREIGN KEY(tenant_id,created_by_user_id) REFERENCES tenant.users(tenant_id,id), CONSTRAINT chk_interviews_schedule CHECK(scheduled_end_at > scheduled_start_at)
);
CREATE TABLE tenant.interview_panelists (
  tenant_id uuid NOT NULL, interview_id uuid NOT NULL, user_id uuid NOT NULL, role_label text NOT NULL DEFAULT 'interviewer', is_required boolean NOT NULL DEFAULT true, response_status approval_status_enum NOT NULL DEFAULT 'pending',
  PRIMARY KEY(tenant_id,interview_id,user_id), CONSTRAINT fk_interview_panelists_interview FOREIGN KEY(tenant_id,interview_id) REFERENCES tenant.interviews(tenant_id,id), CONSTRAINT fk_interview_panelists_user FOREIGN KEY(tenant_id,user_id) REFERENCES tenant.users(tenant_id,id)
);

CREATE TABLE tenant.scorecards (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), interview_id uuid NOT NULL, submitted_by_user_id uuid NOT NULL, recommendation text NOT NULL CHECK(recommendation IN ('strong_yes','yes','no','strong_no','hold')), overall_rating numeric(3,2) CHECK(overall_rating BETWEEN 1 AND 5), comments text,
  submitted_at timestamptz NOT NULL DEFAULT now(), created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_scorecards_tenant_id UNIQUE(tenant_id,id),
  CONSTRAINT uq_scorecards_interview_user UNIQUE(tenant_id,interview_id,submitted_by_user_id),
  CONSTRAINT fk_scorecards_interview FOREIGN KEY(tenant_id,interview_id) REFERENCES tenant.interviews(tenant_id,id), CONSTRAINT fk_scorecards_user FOREIGN KEY(tenant_id,submitted_by_user_id) REFERENCES tenant.users(tenant_id,id)
);
CREATE TABLE tenant.scorecard_criteria (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), requisition_id uuid NOT NULL, competency_id uuid, criterion_name text NOT NULL, weight numeric(6,3) NOT NULL DEFAULT 1 CHECK(weight > 0), sort_order integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_scorecard_criteria_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_scorecard_criteria_req FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id), CONSTRAINT fk_scorecard_criteria_comp FOREIGN KEY(tenant_id,competency_id) REFERENCES tenant.competency_taxonomy(tenant_id,id)
);
CREATE TABLE tenant.scorecard_ratings (
  tenant_id uuid NOT NULL, scorecard_id uuid NOT NULL, criterion_id uuid NOT NULL, rating numeric(3,2) NOT NULL CHECK(rating BETWEEN 1 AND 5), comment text,
  PRIMARY KEY(tenant_id,scorecard_id,criterion_id), CONSTRAINT fk_scorecard_ratings_scorecard FOREIGN KEY(tenant_id,scorecard_id) REFERENCES tenant.scorecards(tenant_id,id), CONSTRAINT fk_scorecard_ratings_criterion FOREIGN KEY(tenant_id,criterion_id) REFERENCES tenant.scorecard_criteria(tenant_id,id)
);

CREATE TABLE tenant.offers (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), application_id uuid NOT NULL, candidate_id uuid NOT NULL, status offer_status_enum NOT NULL DEFAULT 'draft', currency currency_code NOT NULL, base_salary positive_money NOT NULL, bonus_amount positive_money, equity_text text, start_date date, expires_at timestamptz,
  sent_at timestamptz, accepted_at timestamptz, created_by_user_id uuid, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz, lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY(id), CONSTRAINT uq_offers_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_offers_application FOREIGN KEY(tenant_id,application_id) REFERENCES tenant.applications(tenant_id,id), CONSTRAINT fk_offers_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id), CONSTRAINT fk_offers_created_by FOREIGN KEY(tenant_id,created_by_user_id) REFERENCES tenant.users(tenant_id,id),
  CONSTRAINT chk_offers_accepted CHECK(status <> 'accepted' OR accepted_at IS NOT NULL)
);
CREATE TABLE tenant.offer_approval_steps (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), offer_id uuid NOT NULL, step_order integer NOT NULL CHECK(step_order>0), approver_user_id uuid NOT NULL, status approval_status_enum NOT NULL DEFAULT 'pending', decided_at timestamptz, comments text,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_offer_approval_steps_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_offer_approval_steps_order UNIQUE(tenant_id,offer_id,step_order), CONSTRAINT fk_offer_approval_steps_offer FOREIGN KEY(tenant_id,offer_id) REFERENCES tenant.offers(tenant_id,id), CONSTRAINT fk_offer_approval_steps_user FOREIGN KEY(tenant_id,approver_user_id) REFERENCES tenant.users(tenant_id,id)
);

CREATE TABLE tenant.pre_joining_engagements (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), offer_id uuid NOT NULL, candidate_id uuid NOT NULL, start_date date NOT NULL, owner_user_id uuid, status text NOT NULL DEFAULT 'active' CHECK(status IN ('active','completed','cancelled')), created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_pre_joining_engagements_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_pre_joining_engagements_offer FOREIGN KEY(tenant_id,offer_id) REFERENCES tenant.offers(tenant_id,id), CONSTRAINT fk_pre_joining_engagements_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id), CONSTRAINT fk_pre_joining_engagements_owner FOREIGN KEY(tenant_id,owner_user_id) REFERENCES tenant.users(tenant_id,id)
);
CREATE TABLE tenant.pre_joining_touchpoints (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), engagement_id uuid NOT NULL, touchpoint_type text NOT NULL, scheduled_at timestamptz NOT NULL, channel notif_channel_enum NOT NULL, status text NOT NULL DEFAULT 'scheduled' CHECK(status IN ('scheduled','sent','completed','cancelled','failed')), created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_pre_joining_touchpoints_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_pre_joining_touchpoints_engagement FOREIGN KEY(tenant_id,engagement_id) REFERENCES tenant.pre_joining_engagements(tenant_id,id)
);
CREATE TABLE tenant.pre_joining_document_requirements (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), engagement_id uuid NOT NULL, document_type text NOT NULL, is_required boolean NOT NULL DEFAULT true, due_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_pre_joining_document_requirements_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_pre_joining_document_requirements_type UNIQUE(tenant_id,engagement_id,document_type), CONSTRAINT fk_pre_joining_document_requirements_engagement FOREIGN KEY(tenant_id,engagement_id) REFERENCES tenant.pre_joining_engagements(tenant_id,id)
);
CREATE TABLE tenant.pre_joining_document_statuses (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), document_requirement_id uuid NOT NULL, candidate_document_id uuid, status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','submitted','verified','rejected','waived')), verified_by_user_id uuid, verified_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_pre_joining_document_statuses_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_pre_joining_document_statuses_requirement FOREIGN KEY(tenant_id,document_requirement_id) REFERENCES tenant.pre_joining_document_requirements(tenant_id,id), CONSTRAINT fk_pre_joining_document_statuses_document FOREIGN KEY(tenant_id,candidate_document_id) REFERENCES tenant.candidate_documents(tenant_id,id), CONSTRAINT fk_pre_joining_document_statuses_verified_by FOREIGN KEY(tenant_id,verified_by_user_id) REFERENCES tenant.users(tenant_id,id)
);

CREATE TABLE tenant.onboarding_tasks (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), offer_id uuid NOT NULL, task_key text NOT NULL, title text NOT NULL, owner_user_id uuid, due_at timestamptz, status text NOT NULL DEFAULT 'open' CHECK(status IN ('open','in_progress','completed','cancelled')), completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_onboarding_tasks_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_onboarding_tasks_offer FOREIGN KEY(tenant_id,offer_id) REFERENCES tenant.offers(tenant_id,id), CONSTRAINT fk_onboarding_tasks_owner FOREIGN KEY(tenant_id,owner_user_id) REFERENCES tenant.users(tenant_id,id)
);

CREATE TABLE tenant.job_board_postings (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), requisition_id uuid NOT NULL, connector_instance_id uuid, job_board text NOT NULL, external_posting_id text, status posting_status_enum NOT NULL DEFAULT 'pending', posted_at timestamptz, closed_at timestamptz, view_count integer NOT NULL DEFAULT 0 CHECK(view_count>=0), application_count integer NOT NULL DEFAULT 0 CHECK(application_count>=0), created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_job_board_postings_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_job_board_postings_external UNIQUE(tenant_id, job_board, external_posting_id), CONSTRAINT fk_job_board_postings_req FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id)
);
-- ============================================================
-- File 05: Agency ATS - clients, mandates, submittals, placements, fee terms
-- ============================================================

CREATE TABLE agency.clients (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), name text NOT NULL, industry text, contract_type contract_type_enum NOT NULL, status client_status_enum NOT NULL DEFAULT 'active', billing_terms text, default_branding_id uuid, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz, lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY(id), CONSTRAINT uq_clients_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_clients_tenant_name UNIQUE(tenant_id,name), CONSTRAINT fk_clients_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id), CONSTRAINT fk_clients_branding FOREIGN KEY(tenant_id,default_branding_id) REFERENCES tenant.tenant_branding(tenant_id,id)
);
CREATE TABLE agency.client_domains (tenant_id uuid NOT NULL, client_id uuid NOT NULL, domain citext NOT NULL, is_primary boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(tenant_id,client_id,domain), CONSTRAINT fk_client_domains_client FOREIGN KEY(tenant_id,client_id) REFERENCES agency.clients(tenant_id,id));
CREATE UNIQUE INDEX uq_client_domains_one_primary ON agency.client_domains(tenant_id,client_id) WHERE is_primary;
CREATE TABLE agency.client_contacts (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), client_id uuid NOT NULL, name text NOT NULL, email citext NOT NULL, phone_e164 text, role_title text, portal_access_enabled boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz,
  PRIMARY KEY(id), CONSTRAINT uq_client_contacts_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_client_contacts_email UNIQUE(tenant_id,client_id,email), CONSTRAINT fk_client_contacts_client FOREIGN KEY(tenant_id,client_id) REFERENCES agency.clients(tenant_id,id)
);
CREATE TABLE agency.client_portal_users (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), client_id uuid NOT NULL, contact_id uuid NOT NULL, email citext NOT NULL, access_scope text NOT NULL CHECK(access_scope IN ('specific_mandates','all_active_mandates')), status tenant_user_status_enum NOT NULL DEFAULT 'invited', last_login_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz,
  PRIMARY KEY(id), CONSTRAINT uq_client_portal_users_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_client_portal_users_contact UNIQUE(tenant_id,contact_id), CONSTRAINT fk_client_portal_users_client FOREIGN KEY(tenant_id,client_id) REFERENCES agency.clients(tenant_id,id), CONSTRAINT fk_client_portal_users_contact FOREIGN KEY(tenant_id,contact_id) REFERENCES agency.client_contacts(tenant_id,id)
);
CREATE TABLE agency.external_competing_agencies (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), name text NOT NULL, domain citext, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_external_competing_agencies_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_external_competing_agencies_name UNIQUE(tenant_id,name), CONSTRAINT fk_external_competing_agencies_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id));
CREATE TABLE agency.competitor_conflicts (tenant_id uuid NOT NULL, client_a_id uuid NOT NULL, client_b_id uuid NOT NULL, reason text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(tenant_id,client_a_id,client_b_id), CONSTRAINT fk_competitor_conflicts_a FOREIGN KEY(tenant_id,client_a_id) REFERENCES agency.clients(tenant_id,id), CONSTRAINT fk_competitor_conflicts_b FOREIGN KEY(tenant_id,client_b_id) REFERENCES agency.clients(tenant_id,id), CONSTRAINT chk_competitor_conflicts_order CHECK(client_a_id < client_b_id));

CREATE TABLE agency.mandates (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), client_id uuid NOT NULL, mandate_number text NOT NULL, title text NOT NULL, headcount integer NOT NULL CHECK(headcount > 0), fee_structure fee_structure_enum NOT NULL, exclusivity exclusivity_enum NOT NULL, target_fill_date date, status mandate_status_enum NOT NULL DEFAULT 'draft', owner_user_id uuid, opened_at timestamptz, closed_at timestamptz, cancellation_reason text,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz, lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY(id), CONSTRAINT uq_mandates_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_mandates_number UNIQUE(tenant_id,mandate_number), CONSTRAINT fk_mandates_client FOREIGN KEY(tenant_id,client_id) REFERENCES agency.clients(tenant_id,id), CONSTRAINT fk_mandates_owner FOREIGN KEY(tenant_id,owner_user_id) REFERENCES tenant.users(tenant_id,id)
);
ALTER TABLE tenant.talent_pool_entry_mandates ADD CONSTRAINT fk_talent_pool_entry_mandates_mandate FOREIGN KEY (tenant_id, mandate_id) REFERENCES agency.mandates(tenant_id,id);
CREATE TABLE agency.mandate_competing_agencies (tenant_id uuid NOT NULL, mandate_id uuid NOT NULL, external_competing_agency_id uuid NOT NULL, risk_note text, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(tenant_id,mandate_id,external_competing_agency_id), CONSTRAINT fk_mandate_competing_agencies_mandate FOREIGN KEY(tenant_id,mandate_id) REFERENCES agency.mandates(tenant_id,id), CONSTRAINT fk_mandate_competing_agencies_agency FOREIGN KEY(tenant_id,external_competing_agency_id) REFERENCES agency.external_competing_agencies(tenant_id,id));
CREATE TABLE agency.mandate_fee_terms (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), mandate_id uuid NOT NULL, term_type fee_structure_enum NOT NULL, percentage percent_0_100, flat_amount positive_money, currency currency_code NOT NULL DEFAULT 'USD', milestone_name text, milestone_order integer, due_event text CHECK(due_event IS NULL OR due_event IN ('signing','shortlist','interview','placement','start_date','guarantee_clear')), created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_mandate_fee_terms_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_mandate_fee_terms_mandate FOREIGN KEY(tenant_id,mandate_id) REFERENCES agency.mandates(tenant_id,id), CONSTRAINT chk_mandate_fee_terms_amount CHECK((term_type='percentage_of_salary' AND percentage IS NOT NULL AND flat_amount IS NULL) OR (term_type IN ('flat_fee','retainer','time_and_materials') AND flat_amount IS NOT NULL)));
CREATE TABLE agency.retainer_milestones (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), mandate_id uuid NOT NULL, fee_term_id uuid, milestone_order integer NOT NULL CHECK(milestone_order>0), name text NOT NULL, trigger_event text NOT NULL, amount positive_money NOT NULL, currency currency_code NOT NULL DEFAULT 'USD', status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','invoiced','paid','waived')), triggered_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_retainer_milestones_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_retainer_milestones_order UNIQUE(tenant_id,mandate_id,milestone_order), CONSTRAINT fk_retainer_milestones_mandate FOREIGN KEY(tenant_id,mandate_id) REFERENCES agency.mandates(tenant_id,id), CONSTRAINT fk_retainer_milestones_fee_term FOREIGN KEY(tenant_id,fee_term_id) REFERENCES agency.mandate_fee_terms(tenant_id,id));
CREATE TABLE agency.client_portal_user_mandates (tenant_id uuid NOT NULL, portal_user_id uuid NOT NULL, mandate_id uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(tenant_id,portal_user_id,mandate_id), CONSTRAINT fk_client_portal_user_mandates_user FOREIGN KEY(tenant_id,portal_user_id) REFERENCES agency.client_portal_users(tenant_id,id), CONSTRAINT fk_client_portal_user_mandates_mandate FOREIGN KEY(tenant_id,mandate_id) REFERENCES agency.mandates(tenant_id,id));

CREATE TABLE agency.submittals (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), mandate_id uuid NOT NULL, candidate_id uuid NOT NULL, submitted_by_user_id uuid NOT NULL, submitted_at timestamptz, status submittal_status_enum NOT NULL DEFAULT 'draft', direct_apply_attestation text, competitor_conflict_overridden boolean NOT NULL DEFAULT false, competitor_conflict_override_reason text, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz, lock_version bigint NOT NULL DEFAULT 0,
  PRIMARY KEY(id), CONSTRAINT uq_submittals_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_submittals_candidate_mandate UNIQUE(tenant_id,candidate_id,mandate_id), CONSTRAINT fk_submittals_mandate FOREIGN KEY(tenant_id,mandate_id) REFERENCES agency.mandates(tenant_id,id), CONSTRAINT fk_submittals_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id), CONSTRAINT fk_submittals_submitted_by FOREIGN KEY(tenant_id,submitted_by_user_id) REFERENCES tenant.users(tenant_id,id), CONSTRAINT chk_submittals_conflict_override CHECK (competitor_conflict_overridden = false OR competitor_conflict_override_reason IS NOT NULL)
);
CREATE TABLE agency.submittal_profile_snapshots (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), submittal_id uuid NOT NULL, snapshot_version integer NOT NULL CHECK(snapshot_version>0), resume_document_id uuid, rendered_profile_uri text, created_by_user_id uuid, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_submittal_profile_snapshots_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_submittal_profile_snapshots_version UNIQUE(tenant_id,submittal_id,snapshot_version), CONSTRAINT fk_submittal_profile_snapshots_submittal FOREIGN KEY(tenant_id,submittal_id) REFERENCES agency.submittals(tenant_id,id), CONSTRAINT fk_submittal_profile_snapshots_resume FOREIGN KEY(tenant_id,resume_document_id) REFERENCES tenant.candidate_documents(tenant_id,id), CONSTRAINT fk_submittal_profile_snapshots_created_by FOREIGN KEY(tenant_id,created_by_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE agency.submittal_profile_fields (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), snapshot_id uuid NOT NULL, field_key text NOT NULL, field_value text, is_redacted boolean NOT NULL DEFAULT false, redaction_reason text, sort_order integer NOT NULL DEFAULT 0, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_submittal_profile_fields_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_submittal_profile_fields_key UNIQUE(tenant_id,snapshot_id,field_key), CONSTRAINT fk_submittal_profile_fields_snapshot FOREIGN KEY(tenant_id,snapshot_id) REFERENCES agency.submittal_profile_snapshots(tenant_id,id));
CREATE TABLE agency.submittal_feedback (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), submittal_id uuid NOT NULL, client_contact_id uuid NOT NULL, rating numeric(3,2) CHECK(rating BETWEEN 1 AND 5), decision text NOT NULL CHECK(decision IN ('advance','reject','hold','needs_more_info')), comments text, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_submittal_feedback_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_submittal_feedback_submittal FOREIGN KEY(tenant_id,submittal_id) REFERENCES agency.submittals(tenant_id,id), CONSTRAINT fk_submittal_feedback_contact FOREIGN KEY(tenant_id,client_contact_id) REFERENCES agency.client_contacts(tenant_id,id));

CREATE TABLE agency.placements (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), submittal_id uuid NOT NULL, candidate_id uuid NOT NULL, mandate_id uuid NOT NULL, placed_at timestamptz NOT NULL DEFAULT now(), start_date date, final_salary positive_money, currency currency_code NOT NULL DEFAULT 'USD', fee_amount positive_money NOT NULL, guarantee_status guarantee_status_enum NOT NULL DEFAULT 'active', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_placements_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_placements_submittal UNIQUE(tenant_id,submittal_id), CONSTRAINT fk_placements_submittal FOREIGN KEY(tenant_id,submittal_id) REFERENCES agency.submittals(tenant_id,id), CONSTRAINT fk_placements_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id), CONSTRAINT fk_placements_mandate FOREIGN KEY(tenant_id,mandate_id) REFERENCES agency.mandates(tenant_id,id));
CREATE TABLE agency.placement_fee_term_snapshots (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), placement_id uuid NOT NULL, source_fee_term_id uuid, term_type fee_structure_enum NOT NULL, percentage percent_0_100, flat_amount positive_money, currency currency_code NOT NULL, snapshot_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_placement_fee_term_snapshots_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_placement_fee_term_snapshots_placement FOREIGN KEY(tenant_id,placement_id) REFERENCES agency.placements(tenant_id,id), CONSTRAINT fk_placement_fee_term_snapshots_source FOREIGN KEY(tenant_id,source_fee_term_id) REFERENCES agency.mandate_fee_terms(tenant_id,id));
CREATE TABLE agency.placement_guarantees (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), placement_id uuid NOT NULL, guarantee_days integer NOT NULL CHECK(guarantee_days>=0), starts_at date NOT NULL, ends_at date NOT NULL, status guarantee_status_enum NOT NULL DEFAULT 'active', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_placement_guarantees_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_placement_guarantees_placement FOREIGN KEY(tenant_id,placement_id) REFERENCES agency.placements(tenant_id,id), CONSTRAINT chk_placement_guarantees_period CHECK(ends_at >= starts_at));
-- ============================================================
-- File 06: Workflow engine and strict entity reference registry
-- ============================================================

CREATE TABLE tenant.entity_references (
  tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), display_label text,
  candidate_id uuid, requisition_id uuid, application_id uuid, interview_id uuid, offer_id uuid, client_id uuid, mandate_id uuid, submittal_id uuid, placement_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_entity_references_tenant_id UNIQUE(tenant_id,id),
  CONSTRAINT fk_entity_references_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),
  CONSTRAINT fk_entity_references_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id),
  CONSTRAINT fk_entity_references_requisition FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id),
  CONSTRAINT fk_entity_references_application FOREIGN KEY(tenant_id,application_id) REFERENCES tenant.applications(tenant_id,id),
  CONSTRAINT fk_entity_references_interview FOREIGN KEY(tenant_id,interview_id) REFERENCES tenant.interviews(tenant_id,id),
  CONSTRAINT fk_entity_references_offer FOREIGN KEY(tenant_id,offer_id) REFERENCES tenant.offers(tenant_id,id),
  CONSTRAINT fk_entity_references_client FOREIGN KEY(tenant_id,client_id) REFERENCES agency.clients(tenant_id,id),
  CONSTRAINT fk_entity_references_mandate FOREIGN KEY(tenant_id,mandate_id) REFERENCES agency.mandates(tenant_id,id),
  CONSTRAINT fk_entity_references_submittal FOREIGN KEY(tenant_id,submittal_id) REFERENCES agency.submittals(tenant_id,id),
  CONSTRAINT fk_entity_references_placement FOREIGN KEY(tenant_id,placement_id) REFERENCES agency.placements(tenant_id,id)
);
CREATE TRIGGER trg_entity_references_one_of BEFORE INSERT OR UPDATE ON tenant.entity_references FOR EACH ROW EXECUTE FUNCTION app.validate_one_of_refs();

CREATE TABLE tenant.workflow_templates (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), template_key citext NOT NULL, name text NOT NULL, status wf_template_status_enum NOT NULL DEFAULT 'draft', version integer NOT NULL DEFAULT 1 CHECK(version>0), owner_user_id uuid, published_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz, lock_version bigint NOT NULL DEFAULT 0, PRIMARY KEY(id), CONSTRAINT uq_workflow_templates_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_workflow_templates_key_version UNIQUE(tenant_id,template_key,version), CONSTRAINT fk_workflow_templates_owner FOREIGN KEY(tenant_id,owner_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.workflow_template_validation_errors (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_template_id uuid NOT NULL, step_key text, error_code text NOT NULL, error_message text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_workflow_template_validation_errors_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_workflow_template_validation_errors_template FOREIGN KEY(tenant_id,workflow_template_id) REFERENCES tenant.workflow_templates(tenant_id,id));
CREATE TABLE tenant.workflow_canvas_nodes (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_template_id uuid NOT NULL, node_key text NOT NULL, step_type wf_step_type_enum NOT NULL, position_x numeric(10,2) NOT NULL, position_y numeric(10,2) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_workflow_canvas_nodes_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_workflow_canvas_nodes_key UNIQUE(tenant_id,workflow_template_id,node_key), CONSTRAINT fk_workflow_canvas_nodes_template FOREIGN KEY(tenant_id,workflow_template_id) REFERENCES tenant.workflow_templates(tenant_id,id));
CREATE TABLE tenant.workflow_canvas_edges (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_template_id uuid NOT NULL, from_node_id uuid NOT NULL, to_node_id uuid NOT NULL, label text, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_workflow_canvas_edges_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_workflow_canvas_edges_template FOREIGN KEY(tenant_id,workflow_template_id) REFERENCES tenant.workflow_templates(tenant_id,id), CONSTRAINT fk_workflow_canvas_edges_from FOREIGN KEY(tenant_id,from_node_id) REFERENCES tenant.workflow_canvas_nodes(tenant_id,id), CONSTRAINT fk_workflow_canvas_edges_to FOREIGN KEY(tenant_id,to_node_id) REFERENCES tenant.workflow_canvas_nodes(tenant_id,id), CONSTRAINT chk_workflow_canvas_edges_not_self CHECK(from_node_id <> to_node_id));
CREATE TABLE tenant.workflow_steps (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_template_id uuid NOT NULL, step_key citext NOT NULL, name text NOT NULL, step_type wf_step_type_enum NOT NULL, sort_order integer NOT NULL DEFAULT 0, sla_minutes integer CHECK(sla_minutes IS NULL OR sla_minutes>0), created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz, PRIMARY KEY(id), CONSTRAINT uq_workflow_steps_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_workflow_steps_key UNIQUE(tenant_id,workflow_template_id,step_key), CONSTRAINT fk_workflow_steps_template FOREIGN KEY(tenant_id,workflow_template_id) REFERENCES tenant.workflow_templates(tenant_id,id));
CREATE TABLE tenant.workflow_step_settings (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_step_id uuid NOT NULL, setting_key citext NOT NULL, value_text text, value_number numeric(18,6), value_bool boolean, value_integer bigint, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_workflow_step_settings_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_workflow_step_settings_key UNIQUE(tenant_id,workflow_step_id,setting_key), CONSTRAINT fk_workflow_step_settings_step FOREIGN KEY(tenant_id,workflow_step_id) REFERENCES tenant.workflow_steps(tenant_id,id), CONSTRAINT chk_workflow_step_settings_one_value CHECK((CASE WHEN value_text IS NULL THEN 0 ELSE 1 END)+(CASE WHEN value_number IS NULL THEN 0 ELSE 1 END)+(CASE WHEN value_bool IS NULL THEN 0 ELSE 1 END)+(CASE WHEN value_integer IS NULL THEN 0 ELSE 1 END)=1));
CREATE TABLE tenant.workflow_step_approval_configs (tenant_id uuid NOT NULL, workflow_step_id uuid NOT NULL, resolution_mode approver_resolution_enum NOT NULL, approver_role_id uuid, approver_user_id uuid, org_hierarchy_levels integer CHECK(org_hierarchy_levels IS NULL OR org_hierarchy_levels>0), allow_delegation boolean NOT NULL DEFAULT true, PRIMARY KEY(tenant_id,workflow_step_id), CONSTRAINT fk_workflow_step_approval_configs_step FOREIGN KEY(tenant_id,workflow_step_id) REFERENCES tenant.workflow_steps(tenant_id,id), CONSTRAINT fk_workflow_step_approval_configs_role FOREIGN KEY(tenant_id,approver_role_id) REFERENCES tenant.roles(tenant_id,id), CONSTRAINT fk_workflow_step_approval_configs_user FOREIGN KEY(tenant_id,approver_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.workflow_step_ai_action_configs (tenant_id uuid NOT NULL, workflow_step_id uuid NOT NULL, action_type ai_action_type_enum NOT NULL, autonomy_mode ai_autonomy_mode_enum NOT NULL, confidence_threshold confidence_score, PRIMARY KEY(tenant_id,workflow_step_id), CONSTRAINT fk_workflow_step_ai_action_configs_step FOREIGN KEY(tenant_id,workflow_step_id) REFERENCES tenant.workflow_steps(tenant_id,id));
CREATE TABLE tenant.workflow_escalation_rules (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_step_id uuid NOT NULL, trigger_after_minutes integer NOT NULL CHECK(trigger_after_minutes>0), escalate_to_role_id uuid, escalate_to_user_id uuid, notification_template_key text, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_workflow_escalation_rules_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_workflow_escalation_rules_step FOREIGN KEY(tenant_id,workflow_step_id) REFERENCES tenant.workflow_steps(tenant_id,id), CONSTRAINT fk_workflow_escalation_rules_role FOREIGN KEY(tenant_id,escalate_to_role_id) REFERENCES tenant.roles(tenant_id,id), CONSTRAINT fk_workflow_escalation_rules_user FOREIGN KEY(tenant_id,escalate_to_user_id) REFERENCES tenant.users(tenant_id,id), CONSTRAINT chk_workflow_escalation_rules_target CHECK(escalate_to_role_id IS NOT NULL OR escalate_to_user_id IS NOT NULL));
CREATE TABLE tenant.workflow_transitions (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_template_id uuid NOT NULL, from_step_id uuid NOT NULL, to_step_id uuid NOT NULL, sort_order integer NOT NULL DEFAULT 0, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_workflow_transitions_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_workflow_transitions_template FOREIGN KEY(tenant_id,workflow_template_id) REFERENCES tenant.workflow_templates(tenant_id,id), CONSTRAINT fk_workflow_transitions_from FOREIGN KEY(tenant_id,from_step_id) REFERENCES tenant.workflow_steps(tenant_id,id), CONSTRAINT fk_workflow_transitions_to FOREIGN KEY(tenant_id,to_step_id) REFERENCES tenant.workflow_steps(tenant_id,id), CONSTRAINT chk_workflow_transitions_not_self CHECK(from_step_id<>to_step_id));
CREATE TABLE tenant.workflow_transition_condition_groups (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), transition_id uuid NOT NULL, group_operator text NOT NULL CHECK(group_operator IN('AND','OR')), created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_workflow_transition_condition_groups_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_workflow_transition_condition_groups_transition FOREIGN KEY(tenant_id,transition_id) REFERENCES tenant.workflow_transitions(tenant_id,id));
CREATE TABLE tenant.workflow_transition_conditions (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), condition_group_id uuid NOT NULL, field_key citext NOT NULL, operator condition_operator_enum NOT NULL, value_text text, value_number numeric(18,6), value_bool boolean, value_date date, PRIMARY KEY(id), CONSTRAINT uq_workflow_transition_conditions_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_workflow_transition_conditions_group FOREIGN KEY(tenant_id,condition_group_id) REFERENCES tenant.workflow_transition_condition_groups(tenant_id,id));
CREATE TABLE tenant.workflow_template_change_log (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_template_id uuid NOT NULL, changed_by_user_id uuid, change_reason text NOT NULL, diff_summary jsonb, changed_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_workflow_template_change_log_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_workflow_template_change_log_template FOREIGN KEY(tenant_id,workflow_template_id) REFERENCES tenant.workflow_templates(tenant_id,id), CONSTRAINT fk_workflow_template_change_log_user FOREIGN KEY(tenant_id,changed_by_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.workflow_simulation_runs (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_template_id uuid NOT NULL, entity_reference_id uuid NOT NULL, status sync_status_enum NOT NULL DEFAULT 'pending', started_by_user_id uuid, created_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz, PRIMARY KEY(id), CONSTRAINT uq_workflow_simulation_runs_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_workflow_simulation_runs_template FOREIGN KEY(tenant_id,workflow_template_id) REFERENCES tenant.workflow_templates(tenant_id,id), CONSTRAINT fk_workflow_simulation_runs_entity FOREIGN KEY(tenant_id,entity_reference_id) REFERENCES tenant.entity_references(tenant_id,id), CONSTRAINT fk_workflow_simulation_runs_user FOREIGN KEY(tenant_id,started_by_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.workflow_simulation_steps (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), simulation_run_id uuid NOT NULL, step_id uuid NOT NULL, outcome text NOT NULL, sort_order integer NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_workflow_simulation_steps_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_workflow_simulation_steps_run FOREIGN KEY(tenant_id,simulation_run_id) REFERENCES tenant.workflow_simulation_runs(tenant_id,id), CONSTRAINT fk_workflow_simulation_steps_step FOREIGN KEY(tenant_id,step_id) REFERENCES tenant.workflow_steps(tenant_id,id));
CREATE TABLE tenant.workflow_instances (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_template_id uuid NOT NULL, entity_reference_id uuid NOT NULL, status wf_instance_status_enum NOT NULL DEFAULT 'running', current_step_id uuid, started_by_user_id uuid, started_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), lock_version bigint NOT NULL DEFAULT 0, PRIMARY KEY(id), CONSTRAINT uq_workflow_instances_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_workflow_instances_template FOREIGN KEY(tenant_id,workflow_template_id) REFERENCES tenant.workflow_templates(tenant_id,id), CONSTRAINT fk_workflow_instances_entity FOREIGN KEY(tenant_id,entity_reference_id) REFERENCES tenant.entity_references(tenant_id,id), CONSTRAINT fk_workflow_instances_current_step FOREIGN KEY(tenant_id,current_step_id) REFERENCES tenant.workflow_steps(tenant_id,id), CONSTRAINT fk_workflow_instances_started_by FOREIGN KEY(tenant_id,started_by_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.workflow_instance_context_values (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_instance_id uuid NOT NULL, context_key citext NOT NULL, value_text text, value_number numeric(18,6), value_bool boolean, value_date date, captured_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_workflow_instance_context_values_tenant_id UNIQUE(tenant_id,id), CONSTRAINT uq_workflow_instance_context_values_key UNIQUE(tenant_id,workflow_instance_id,context_key), CONSTRAINT fk_workflow_instance_context_values_instance FOREIGN KEY(tenant_id,workflow_instance_id) REFERENCES tenant.workflow_instances(tenant_id,id));
CREATE TABLE tenant.workflow_instance_history (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_instance_id uuid NOT NULL, from_step_id uuid, to_step_id uuid, action_key text NOT NULL, actor_user_id uuid, occurred_at timestamptz NOT NULL DEFAULT now(), comments text, PRIMARY KEY(id), CONSTRAINT uq_workflow_instance_history_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_workflow_instance_history_instance FOREIGN KEY(tenant_id,workflow_instance_id) REFERENCES tenant.workflow_instances(tenant_id,id), CONSTRAINT fk_workflow_instance_history_from FOREIGN KEY(tenant_id,from_step_id) REFERENCES tenant.workflow_steps(tenant_id,id), CONSTRAINT fk_workflow_instance_history_to FOREIGN KEY(tenant_id,to_step_id) REFERENCES tenant.workflow_steps(tenant_id,id), CONSTRAINT fk_workflow_instance_history_actor FOREIGN KEY(tenant_id,actor_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.workflow_condition_evaluations (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_history_id uuid NOT NULL, condition_id uuid, result boolean NOT NULL, actual_value text, evaluated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_workflow_condition_evaluations_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_workflow_condition_evaluations_history FOREIGN KEY(tenant_id,workflow_history_id) REFERENCES tenant.workflow_instance_history(tenant_id,id), CONSTRAINT fk_workflow_condition_evaluations_condition FOREIGN KEY(tenant_id,condition_id) REFERENCES tenant.workflow_transition_conditions(tenant_id,id));
CREATE TABLE tenant.approval_tasks (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), workflow_instance_id uuid, entity_reference_id uuid NOT NULL, approver_user_id uuid NOT NULL, delegated_from_user_id uuid, status approval_status_enum NOT NULL DEFAULT 'pending', due_at timestamptz, decided_at timestamptz, decision_comment text, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), lock_version bigint NOT NULL DEFAULT 0, PRIMARY KEY(id), CONSTRAINT uq_approval_tasks_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_approval_tasks_instance FOREIGN KEY(tenant_id,workflow_instance_id) REFERENCES tenant.workflow_instances(tenant_id,id), CONSTRAINT fk_approval_tasks_entity FOREIGN KEY(tenant_id,entity_reference_id) REFERENCES tenant.entity_references(tenant_id,id), CONSTRAINT fk_approval_tasks_approver FOREIGN KEY(tenant_id,approver_user_id) REFERENCES tenant.users(tenant_id,id), CONSTRAINT fk_approval_tasks_delegated_from FOREIGN KEY(tenant_id,delegated_from_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.ai_action_autonomy_configs (tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), action_type ai_action_type_enum NOT NULL, scope_level config_scope_enum NOT NULL DEFAULT 'tenant', business_unit_id uuid, autonomy_mode ai_autonomy_mode_enum NOT NULL, confidence_threshold confidence_score, effective_from timestamptz NOT NULL DEFAULT now(), effective_to timestamptz, created_by_user_id uuid, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(id), CONSTRAINT uq_ai_action_autonomy_configs_tenant_id UNIQUE(tenant_id,id), CONSTRAINT fk_ai_action_autonomy_configs_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id), CONSTRAINT fk_ai_action_autonomy_configs_bu FOREIGN KEY(tenant_id,business_unit_id) REFERENCES tenant.business_units(tenant_id,id), CONSTRAINT fk_ai_action_autonomy_configs_user FOREIGN KEY(tenant_id,created_by_user_id) REFERENCES tenant.users(tenant_id,id), CONSTRAINT chk_ai_action_autonomy_configs_period CHECK(effective_to IS NULL OR effective_to > effective_from));

INSERT INTO platform.allowed_jsonb_columns(schema_name, table_name, column_name, allowed_reason) VALUES
('tenant','workflow_template_change_log','diff_summary','Immutable workflow template change diff snapshot')
ON CONFLICT DO NOTHING;
-- ============================================================
-- File 07: AI recruiter, interview bot, telephony, governance, usage
-- ============================================================

CREATE TABLE ai.recruiter_personas (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),name text NOT NULL,description text,default_tone text,autonomy_mode ai_autonomy_mode_enum NOT NULL DEFAULT 'human_approval_required',is_default boolean NOT NULL DEFAULT false,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),deleted_at timestamptz,PRIMARY KEY(id),CONSTRAINT uq_recruiter_personas_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_recruiter_personas_name UNIQUE(tenant_id,name),CONSTRAINT fk_recruiter_personas_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id));
CREATE UNIQUE INDEX uq_recruiter_personas_default ON ai.recruiter_personas(tenant_id) WHERE is_default AND deleted_at IS NULL;
CREATE TABLE ai.persona_languages (tenant_id uuid NOT NULL,persona_id uuid NOT NULL,locale text NOT NULL,PRIMARY KEY(tenant_id,persona_id,locale),CONSTRAINT fk_persona_languages_persona FOREIGN KEY(tenant_id,persona_id) REFERENCES ai.recruiter_personas(tenant_id,id));
CREATE TABLE ai.persona_banned_topics (tenant_id uuid NOT NULL,persona_id uuid NOT NULL,topic_key text NOT NULL,PRIMARY KEY(tenant_id,persona_id,topic_key),CONSTRAINT fk_persona_banned_topics_persona FOREIGN KEY(tenant_id,persona_id) REFERENCES ai.recruiter_personas(tenant_id,id));
CREATE TABLE ai.persona_required_disclosures (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),persona_id uuid NOT NULL,disclosure_key text NOT NULL,disclosure_text text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_persona_required_disclosures_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_persona_required_disclosures_persona FOREIGN KEY(tenant_id,persona_id) REFERENCES ai.recruiter_personas(tenant_id,id));
CREATE TABLE ai.persona_escalation_rules (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),persona_id uuid NOT NULL,trigger_key text NOT NULL,condition_key text NOT NULL,action_key text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_persona_escalation_rules_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_persona_escalation_rules_persona FOREIGN KEY(tenant_id,persona_id) REFERENCES ai.recruiter_personas(tenant_id,id));
CREATE TABLE ai.persona_jurisdiction_disclosures (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),persona_id uuid NOT NULL,region region_enum NOT NULL,disclosure_text text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_persona_jurisdiction_disclosures_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_persona_jurisdiction_disclosures_region UNIQUE(tenant_id,persona_id,region),CONSTRAINT fk_persona_jurisdiction_disclosures_persona FOREIGN KEY(tenant_id,persona_id) REFERENCES ai.recruiter_personas(tenant_id,id));

CREATE TABLE ai.agent_identities (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),persona_id uuid,agent_key citext NOT NULL,display_name text NOT NULL,status text NOT NULL DEFAULT 'active' CHECK(status IN('active','disabled','deleted')),created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_agent_identities_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_agent_identities_key UNIQUE(tenant_id,agent_key),CONSTRAINT fk_agent_identities_persona FOREIGN KEY(tenant_id,persona_id) REFERENCES ai.recruiter_personas(tenant_id,id));
CREATE TABLE ai.agent_permissions (tenant_id uuid NOT NULL,agent_id uuid NOT NULL,permission_id uuid NOT NULL,PRIMARY KEY(tenant_id,agent_id,permission_id),CONSTRAINT fk_agent_permissions_agent FOREIGN KEY(tenant_id,agent_id) REFERENCES ai.agent_identities(tenant_id,id),CONSTRAINT fk_agent_permissions_permission FOREIGN KEY(tenant_id,permission_id) REFERENCES tenant.permissions(tenant_id,id));
CREATE TABLE ai.agent_business_units (tenant_id uuid NOT NULL,agent_id uuid NOT NULL,business_unit_id uuid NOT NULL,PRIMARY KEY(tenant_id,agent_id,business_unit_id),CONSTRAINT fk_agent_business_units_agent FOREIGN KEY(tenant_id,agent_id) REFERENCES ai.agent_identities(tenant_id,id),CONSTRAINT fk_agent_business_units_bu FOREIGN KEY(tenant_id,business_unit_id) REFERENCES tenant.business_units(tenant_id,id));

CREATE TABLE ai.prompt_templates (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),template_key citext NOT NULL,action_type ai_action_type_enum NOT NULL,version integer NOT NULL DEFAULT 1,template_text text NOT NULL,status wf_template_status_enum NOT NULL DEFAULT 'draft',model_definition_id uuid,created_by_user_id uuid,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_prompt_templates_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_prompt_templates_key_version UNIQUE(tenant_id,template_key,version),CONSTRAINT fk_prompt_templates_model FOREIGN KEY(model_definition_id) REFERENCES platform.ai_model_definitions(id),CONSTRAINT fk_prompt_templates_user FOREIGN KEY(tenant_id,created_by_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE ai.prompt_template_variables (tenant_id uuid NOT NULL,prompt_template_id uuid NOT NULL,variable_key citext NOT NULL,is_required boolean NOT NULL DEFAULT true,PRIMARY KEY(tenant_id,prompt_template_id,variable_key),CONSTRAINT fk_prompt_template_variables_template FOREIGN KEY(tenant_id,prompt_template_id) REFERENCES ai.prompt_templates(tenant_id,id));
CREATE TABLE ai.prompt_template_policy_flags (tenant_id uuid NOT NULL,prompt_template_id uuid NOT NULL,policy_key text NOT NULL,severity text NOT NULL CHECK(severity IN('low','medium','high','critical')),PRIMARY KEY(tenant_id,prompt_template_id,policy_key),CONSTRAINT fk_prompt_template_policy_flags_template FOREIGN KEY(tenant_id,prompt_template_id) REFERENCES ai.prompt_templates(tenant_id,id));

CREATE TABLE ai.sourcing_runs (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),requisition_id uuid,mandate_id uuid,persona_id uuid,started_by_user_id uuid,status sync_status_enum NOT NULL DEFAULT 'pending',started_at timestamptz NOT NULL DEFAULT now(),completed_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_sourcing_runs_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_sourcing_runs_requisition FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id),CONSTRAINT fk_sourcing_runs_mandate FOREIGN KEY(tenant_id,mandate_id) REFERENCES agency.mandates(tenant_id,id),CONSTRAINT fk_sourcing_runs_persona FOREIGN KEY(tenant_id,persona_id) REFERENCES ai.recruiter_personas(tenant_id,id),CONSTRAINT fk_sourcing_runs_user FOREIGN KEY(tenant_id,started_by_user_id) REFERENCES tenant.users(tenant_id,id),CONSTRAINT chk_sourcing_runs_subject CHECK((requisition_id IS NOT NULL)::int + (mandate_id IS NOT NULL)::int = 1));
CREATE TABLE ai.sourcing_criteria (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),sourcing_run_id uuid NOT NULL,criterion_key text NOT NULL,operator condition_operator_enum NOT NULL,value_text text,value_number numeric(18,6),value_bool boolean,weight numeric(6,3) NOT NULL DEFAULT 1 CHECK(weight>0),PRIMARY KEY(id),CONSTRAINT uq_sourcing_criteria_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_sourcing_criteria_run FOREIGN KEY(tenant_id,sourcing_run_id) REFERENCES ai.sourcing_runs(tenant_id,id));
CREATE TABLE ai.sourcing_sources (tenant_id uuid NOT NULL,sourcing_run_id uuid NOT NULL,source_key text NOT NULL,PRIMARY KEY(tenant_id,sourcing_run_id,source_key),CONSTRAINT fk_sourcing_sources_run FOREIGN KEY(tenant_id,sourcing_run_id) REFERENCES ai.sourcing_runs(tenant_id,id));

CREATE TABLE ai.match_scores (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),sourcing_run_id uuid,candidate_id uuid NOT NULL,requisition_id uuid,mandate_id uuid,score confidence_score NOT NULL,explanation text,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_match_scores_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_match_scores_run FOREIGN KEY(tenant_id,sourcing_run_id) REFERENCES ai.sourcing_runs(tenant_id,id),CONSTRAINT fk_match_scores_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id),CONSTRAINT fk_match_scores_requisition FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id),CONSTRAINT fk_match_scores_mandate FOREIGN KEY(tenant_id,mandate_id) REFERENCES agency.mandates(tenant_id,id));
CREATE TABLE ai.match_score_criteria (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),match_score_id uuid NOT NULL,criterion_key text NOT NULL,criterion_score confidence_score NOT NULL,evidence_text text,PRIMARY KEY(id),CONSTRAINT uq_match_score_criteria_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_match_score_criteria_score FOREIGN KEY(tenant_id,match_score_id) REFERENCES ai.match_scores(tenant_id,id));
CREATE TABLE ai.screening_results (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),application_id uuid,submittal_id uuid,candidate_id uuid NOT NULL,overall_score confidence_score NOT NULL,recommendation text NOT NULL CHECK(recommendation IN('advance','reject','hold','human_review')),confidence confidence_score NOT NULL,reasoning_summary text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_screening_results_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_screening_results_application FOREIGN KEY(tenant_id,application_id) REFERENCES tenant.applications(tenant_id,id),CONSTRAINT fk_screening_results_submittal FOREIGN KEY(tenant_id,submittal_id) REFERENCES agency.submittals(tenant_id,id),CONSTRAINT fk_screening_results_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id),CONSTRAINT chk_screening_results_subject CHECK((application_id IS NOT NULL)::int + (submittal_id IS NOT NULL)::int <= 1));
CREATE TABLE ai.screening_criteria_results (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),screening_result_id uuid NOT NULL,criterion_key text NOT NULL,met boolean NOT NULL,score confidence_score,evidence_text text,PRIMARY KEY(id),CONSTRAINT uq_screening_criteria_results_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_screening_criteria_results_screening FOREIGN KEY(tenant_id,screening_result_id) REFERENCES ai.screening_results(tenant_id,id));
CREATE TABLE ai.ai_bias_flags (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),match_score_id uuid,screening_result_id uuid,interview_evaluation_id uuid,flag_key text NOT NULL,severity text NOT NULL CHECK(severity IN('low','medium','high','critical')),description text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_ai_bias_flags_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_ai_bias_flags_match FOREIGN KEY(tenant_id,match_score_id) REFERENCES ai.match_scores(tenant_id,id),CONSTRAINT fk_ai_bias_flags_screening FOREIGN KEY(tenant_id,screening_result_id) REFERENCES ai.screening_results(tenant_id,id),CONSTRAINT chk_ai_bias_flags_one_subject CHECK((match_score_id IS NOT NULL)::int+(screening_result_id IS NOT NULL)::int+(interview_evaluation_id IS NOT NULL)::int=1));

CREATE TABLE ai.ai_conversations (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),candidate_id uuid,application_id uuid,submittal_id uuid,persona_id uuid,channel notif_channel_enum NOT NULL,status text NOT NULL DEFAULT 'open' CHECK(status IN('open','closed','escalated')),started_at timestamptz NOT NULL DEFAULT now(),ended_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_ai_conversations_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_ai_conversations_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id),CONSTRAINT fk_ai_conversations_application FOREIGN KEY(tenant_id,application_id) REFERENCES tenant.applications(tenant_id,id),CONSTRAINT fk_ai_conversations_submittal FOREIGN KEY(tenant_id,submittal_id) REFERENCES agency.submittals(tenant_id,id),CONSTRAINT fk_ai_conversations_persona FOREIGN KEY(tenant_id,persona_id) REFERENCES ai.recruiter_personas(tenant_id,id));
CREATE TABLE ai.conversation_messages (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),conversation_id uuid NOT NULL,sender_type audit_actor_type_enum NOT NULL,sender_user_id uuid,message_text text NOT NULL,model_definition_id uuid,raw_model_response jsonb,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_conversation_messages_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_conversation_messages_conversation FOREIGN KEY(tenant_id,conversation_id) REFERENCES ai.ai_conversations(tenant_id,id),CONSTRAINT fk_conversation_messages_user FOREIGN KEY(tenant_id,sender_user_id) REFERENCES tenant.users(tenant_id,id),CONSTRAINT fk_conversation_messages_model FOREIGN KEY(model_definition_id) REFERENCES platform.ai_model_definitions(id));
CREATE TABLE ai.conversation_escalation_flags (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),conversation_id uuid NOT NULL,flag_key text NOT NULL,status text NOT NULL DEFAULT 'open' CHECK(status IN('open','resolved','dismissed')),created_at timestamptz NOT NULL DEFAULT now(),resolved_at timestamptz,PRIMARY KEY(id),CONSTRAINT uq_conversation_escalation_flags_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_conversation_escalation_flags_conversation FOREIGN KEY(tenant_id,conversation_id) REFERENCES ai.ai_conversations(tenant_id,id));

CREATE TABLE ai.scheduling_requests (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),application_id uuid,submittal_id uuid,requested_by_user_id uuid,status text NOT NULL DEFAULT 'pending' CHECK(status IN('pending','proposed','confirmed','cancelled','failed')),created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_scheduling_requests_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_scheduling_requests_application FOREIGN KEY(tenant_id,application_id) REFERENCES tenant.applications(tenant_id,id),CONSTRAINT fk_scheduling_requests_submittal FOREIGN KEY(tenant_id,submittal_id) REFERENCES agency.submittals(tenant_id,id),CONSTRAINT fk_scheduling_requests_user FOREIGN KEY(tenant_id,requested_by_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE ai.scheduling_participants (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),scheduling_request_id uuid NOT NULL,user_id uuid,candidate_id uuid,client_contact_id uuid,participant_role text NOT NULL,required boolean NOT NULL DEFAULT true,PRIMARY KEY(id),CONSTRAINT uq_scheduling_participants_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_scheduling_participants_request FOREIGN KEY(tenant_id,scheduling_request_id) REFERENCES ai.scheduling_requests(tenant_id,id),CONSTRAINT fk_scheduling_participants_user FOREIGN KEY(tenant_id,user_id) REFERENCES tenant.users(tenant_id,id),CONSTRAINT fk_scheduling_participants_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id),CONSTRAINT fk_scheduling_participants_contact FOREIGN KEY(tenant_id,client_contact_id) REFERENCES agency.client_contacts(tenant_id,id),CONSTRAINT chk_scheduling_participants_one_party CHECK((user_id IS NOT NULL)::int+(candidate_id IS NOT NULL)::int+(client_contact_id IS NOT NULL)::int=1));
CREATE TABLE ai.scheduling_proposed_slots (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),scheduling_request_id uuid NOT NULL,start_at timestamptz NOT NULL,end_at timestamptz NOT NULL,timezone text NOT NULL,is_confirmed boolean NOT NULL DEFAULT false,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_scheduling_proposed_slots_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_scheduling_proposed_slots_request FOREIGN KEY(tenant_id,scheduling_request_id) REFERENCES ai.scheduling_requests(tenant_id,id),CONSTRAINT chk_scheduling_proposed_slots_time CHECK(end_at>start_at));
CREATE TABLE ai.scheduling_calendar_sync_statuses (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),scheduling_request_id uuid NOT NULL,participant_id uuid NOT NULL,connector_instance_id uuid,status sync_status_enum NOT NULL DEFAULT 'pending',external_event_id text,error_message text,updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_scheduling_calendar_sync_statuses_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_scheduling_calendar_sync_statuses_participant UNIQUE(tenant_id,scheduling_request_id,participant_id),CONSTRAINT fk_scheduling_calendar_sync_statuses_request FOREIGN KEY(tenant_id,scheduling_request_id) REFERENCES ai.scheduling_requests(tenant_id,id),CONSTRAINT fk_scheduling_calendar_sync_statuses_participant FOREIGN KEY(tenant_id,participant_id) REFERENCES ai.scheduling_participants(tenant_id,id));

CREATE TABLE ai.interview_sessions (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),interview_id uuid,candidate_id uuid NOT NULL,mode interview_type_enum NOT NULL,status ai_session_status_enum NOT NULL DEFAULT 'not_started',consent_record_id uuid,started_at timestamptz,completed_at timestamptz,recording_uri text,transcript_uri text,accommodation_notes text,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_interview_sessions_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_interview_sessions_interview FOREIGN KEY(tenant_id,interview_id) REFERENCES tenant.interviews(tenant_id,id),CONSTRAINT fk_interview_sessions_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id),CONSTRAINT fk_interview_sessions_consent FOREIGN KEY(tenant_id,consent_record_id) REFERENCES tenant.consent_records(tenant_id,id));
CREATE TABLE ai.interview_question_sets (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),requisition_id uuid,mandate_id uuid,name text NOT NULL,version integer NOT NULL DEFAULT 1,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_interview_question_sets_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_interview_question_sets_req FOREIGN KEY(tenant_id,requisition_id) REFERENCES tenant.requisitions(tenant_id,id),CONSTRAINT fk_interview_question_sets_mandate FOREIGN KEY(tenant_id,mandate_id) REFERENCES agency.mandates(tenant_id,id));
CREATE TABLE ai.interview_questions (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),question_set_id uuid NOT NULL,question_text text NOT NULL,expected_answer_guide text,sort_order integer NOT NULL DEFAULT 0,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_interview_questions_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_interview_questions_set FOREIGN KEY(tenant_id,question_set_id) REFERENCES ai.interview_question_sets(tenant_id,id));
CREATE TABLE ai.interview_question_competencies (tenant_id uuid NOT NULL,question_id uuid NOT NULL,competency_id uuid NOT NULL,PRIMARY KEY(tenant_id,question_id,competency_id),CONSTRAINT fk_interview_question_competencies_question FOREIGN KEY(tenant_id,question_id) REFERENCES ai.interview_questions(tenant_id,id),CONSTRAINT fk_interview_question_competencies_comp FOREIGN KEY(tenant_id,competency_id) REFERENCES tenant.competency_taxonomy(tenant_id,id));
CREATE TABLE ai.interview_responses (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),interview_session_id uuid NOT NULL,question_id uuid,answer_text text,started_at timestamptz,ended_at timestamptz,confidence confidence_score,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_interview_responses_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_interview_responses_session FOREIGN KEY(tenant_id,interview_session_id) REFERENCES ai.interview_sessions(tenant_id,id),CONSTRAINT fk_interview_responses_question FOREIGN KEY(tenant_id,question_id) REFERENCES ai.interview_questions(tenant_id,id));
CREATE TABLE ai.interview_response_media (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),interview_response_id uuid NOT NULL,media_type text NOT NULL CHECK(media_type IN('audio','video','image','transcript')),storage_uri text NOT NULL,duration_ms integer CHECK(duration_ms IS NULL OR duration_ms>=0),created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_interview_response_media_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_interview_response_media_response FOREIGN KEY(tenant_id,interview_response_id) REFERENCES ai.interview_responses(tenant_id,id));
CREATE TABLE ai.interview_evaluations (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),interview_session_id uuid NOT NULL,overall_score confidence_score NOT NULL,recommendation text NOT NULL CHECK(recommendation IN('advance','reject','hold','human_review')),reasoning_summary text NOT NULL,raw_model_response jsonb,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_interview_evaluations_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_interview_evaluations_session FOREIGN KEY(tenant_id,interview_session_id) REFERENCES ai.interview_sessions(tenant_id,id));
ALTER TABLE ai.ai_bias_flags ADD CONSTRAINT fk_ai_bias_flags_evaluation FOREIGN KEY(tenant_id,interview_evaluation_id) REFERENCES ai.interview_evaluations(tenant_id,id);
CREATE TABLE ai.interview_evaluation_competency_scores (tenant_id uuid NOT NULL,interview_evaluation_id uuid NOT NULL,competency_id uuid NOT NULL,score confidence_score NOT NULL,evidence_text text,PRIMARY KEY(tenant_id,interview_evaluation_id,competency_id),CONSTRAINT fk_interview_evaluation_competency_scores_eval FOREIGN KEY(tenant_id,interview_evaluation_id) REFERENCES ai.interview_evaluations(tenant_id,id),CONSTRAINT fk_interview_evaluation_competency_scores_comp FOREIGN KEY(tenant_id,competency_id) REFERENCES tenant.competency_taxonomy(tenant_id,id));
CREATE TABLE ai.interview_evaluation_flags (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),interview_evaluation_id uuid NOT NULL,flag_key text NOT NULL,severity text NOT NULL CHECK(severity IN('low','medium','high','critical')),details text,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_interview_evaluation_flags_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_interview_evaluation_flags_eval FOREIGN KEY(tenant_id,interview_evaluation_id) REFERENCES ai.interview_evaluations(tenant_id,id));
CREATE TABLE ai.interview_low_confidence_segments (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),interview_evaluation_id uuid NOT NULL,start_ms integer NOT NULL CHECK(start_ms>=0),end_ms integer NOT NULL CHECK(end_ms>start_ms),reason text NOT NULL,excluded_from_score boolean NOT NULL DEFAULT false,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_interview_low_confidence_segments_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_interview_low_confidence_segments_eval FOREIGN KEY(tenant_id,interview_evaluation_id) REFERENCES ai.interview_evaluations(tenant_id,id));

CREATE TABLE ai.tenant_telephony_configs (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),provider text NOT NULL,default_region region_enum NOT NULL,recording_enabled boolean NOT NULL DEFAULT true,transcription_enabled boolean NOT NULL DEFAULT true,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_tenant_telephony_configs_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_tenant_telephony_configs_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id));
CREATE TABLE ai.telephony_numbers (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),telephony_config_id uuid NOT NULL,phone_number_e164 text NOT NULL,region region_enum NOT NULL,is_default boolean NOT NULL DEFAULT false,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_telephony_numbers_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_telephony_numbers_number UNIQUE(phone_number_e164),CONSTRAINT fk_telephony_numbers_config FOREIGN KEY(tenant_id,telephony_config_id) REFERENCES ai.tenant_telephony_configs(tenant_id,id));
CREATE TABLE ai.telephony_region_routes (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),telephony_config_id uuid NOT NULL,region region_enum NOT NULL,infrastructure_endpoint text NOT NULL,priority integer NOT NULL DEFAULT 1 CHECK(priority>0),created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_telephony_region_routes_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_telephony_region_routes_config FOREIGN KEY(tenant_id,telephony_config_id) REFERENCES ai.tenant_telephony_configs(tenant_id,id));
CREATE TABLE ai.call_records (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),interview_session_id uuid,conversation_id uuid,direction call_direction_enum NOT NULL,from_number text,to_number text,provider_call_id text,status text NOT NULL,started_at timestamptz,ended_at timestamptz,duration_seconds integer CHECK(duration_seconds IS NULL OR duration_seconds>=0),recording_uri text,transcript_uri text,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_call_records_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_call_records_session FOREIGN KEY(tenant_id,interview_session_id) REFERENCES ai.interview_sessions(tenant_id,id),CONSTRAINT fk_call_records_conversation FOREIGN KEY(tenant_id,conversation_id) REFERENCES ai.ai_conversations(tenant_id,id));
CREATE TABLE ai.call_real_time_flags (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),call_record_id uuid NOT NULL,flag_key text NOT NULL,timestamp_ms integer NOT NULL CHECK(timestamp_ms>=0),details text,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_call_real_time_flags_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_call_real_time_flags_call FOREIGN KEY(tenant_id,call_record_id) REFERENCES ai.call_records(tenant_id,id));
CREATE TABLE ai.call_quality_metrics (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),call_record_id uuid NOT NULL,metric_key text NOT NULL,metric_value numeric(18,6) NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_call_quality_metrics_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_call_quality_metrics_key UNIQUE(tenant_id,call_record_id,metric_key),CONSTRAINT fk_call_quality_metrics_call FOREIGN KEY(tenant_id,call_record_id) REFERENCES ai.call_records(tenant_id,id));
CREATE TABLE ai.live_interview_calls (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),call_record_id uuid NOT NULL,interviewer_user_id uuid,status interview_status_enum NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_live_interview_calls_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_live_interview_calls_call FOREIGN KEY(tenant_id,call_record_id) REFERENCES ai.call_records(tenant_id,id),CONSTRAINT fk_live_interview_calls_interviewer FOREIGN KEY(tenant_id,interviewer_user_id) REFERENCES tenant.users(tenant_id,id));

CREATE TABLE ai.ai_usage_events (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),model_definition_id uuid,action_type ai_action_type_enum NOT NULL,source usage_source_enum NOT NULL,input_tokens integer NOT NULL DEFAULT 0 CHECK(input_tokens>=0),output_tokens integer NOT NULL DEFAULT 0 CHECK(output_tokens>=0),audio_seconds integer NOT NULL DEFAULT 0 CHECK(audio_seconds>=0),cost_amount positive_money,currency currency_code DEFAULT 'USD',occurred_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id,occurred_at),CONSTRAINT uq_ai_usage_events_tenant_id UNIQUE(tenant_id,id,occurred_at),CONSTRAINT fk_ai_usage_events_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_ai_usage_events_model FOREIGN KEY(model_definition_id) REFERENCES platform.ai_model_definitions(id)) PARTITION BY RANGE(occurred_at);
CREATE TABLE ai.ai_usage_events_default PARTITION OF ai.ai_usage_events DEFAULT;
CREATE TABLE ai.joining_risk_scores (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),engagement_id uuid NOT NULL,candidate_id uuid NOT NULL,risk_score confidence_score NOT NULL,risk_level text NOT NULL CHECK(risk_level IN('low','medium','high','critical')),created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_joining_risk_scores_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_joining_risk_scores_engagement FOREIGN KEY(tenant_id,engagement_id) REFERENCES tenant.pre_joining_engagements(tenant_id,id),CONSTRAINT fk_joining_risk_scores_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id));
CREATE TABLE ai.joining_risk_factors (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),joining_risk_score_id uuid NOT NULL,factor_key text NOT NULL,weight numeric(6,3) NOT NULL CHECK(weight>=0),signal_value text,evidence_text text,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_joining_risk_factors_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_joining_risk_factors_score FOREIGN KEY(tenant_id,joining_risk_score_id) REFERENCES ai.joining_risk_scores(tenant_id,id));

INSERT INTO platform.allowed_jsonb_columns(schema_name, table_name, column_name, allowed_reason) VALUES
('ai','conversation_messages','raw_model_response','Immutable raw model response snapshot'),
('ai','interview_evaluations','raw_model_response','Immutable raw model response snapshot')
ON CONFLICT DO NOTHING;
-- ============================================================
-- File 08: Integration framework, events, webhook delivery, notification framework, HITL
-- ============================================================

CREATE TABLE platform.connector_definitions (id uuid PRIMARY KEY DEFAULT gen_random_uuid(),provider_key citext NOT NULL,display_name text NOT NULL,category connector_category_enum NOT NULL,auth_type connector_auth_type_enum NOT NULL,status plan_status_enum NOT NULL DEFAULT 'active',created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),CONSTRAINT uq_connector_definitions_provider UNIQUE(provider_key));
CREATE TABLE platform.connector_operations (connector_definition_id uuid NOT NULL,operation_key citext NOT NULL,description text,PRIMARY KEY(connector_definition_id,operation_key),CONSTRAINT fk_connector_operations_definition FOREIGN KEY(connector_definition_id) REFERENCES platform.connector_definitions(id));
CREATE TABLE platform.connector_versions (id uuid PRIMARY KEY DEFAULT gen_random_uuid(),connector_definition_id uuid NOT NULL,version_label text NOT NULL,released_at timestamptz NOT NULL DEFAULT now(),deprecated_at timestamptz,sunset_at timestamptz,CONSTRAINT fk_connector_versions_definition FOREIGN KEY(connector_definition_id) REFERENCES platform.connector_definitions(id),CONSTRAINT uq_connector_versions_definition_version UNIQUE(connector_definition_id,version_label));
CREATE TABLE tenant.connector_instances (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),connector_definition_id uuid NOT NULL,connector_version_id uuid,status connector_status_enum NOT NULL DEFAULT 'pending_setup',credentials_ref text,created_by_user_id uuid,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),deleted_at timestamptz,PRIMARY KEY(id),CONSTRAINT uq_connector_instances_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_connector_instances_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_connector_instances_definition FOREIGN KEY(connector_definition_id) REFERENCES platform.connector_definitions(id),CONSTRAINT fk_connector_instances_version FOREIGN KEY(connector_version_id) REFERENCES platform.connector_versions(id),CONSTRAINT fk_connector_instances_created_by FOREIGN KEY(tenant_id,created_by_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.connector_instance_settings (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),connector_instance_id uuid NOT NULL,setting_key citext NOT NULL,value_text text,value_number numeric(18,6),value_bool boolean,secret_ref text,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_connector_instance_settings_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_connector_instance_settings_key UNIQUE(tenant_id,connector_instance_id,setting_key),CONSTRAINT fk_connector_instance_settings_instance FOREIGN KEY(tenant_id,connector_instance_id) REFERENCES tenant.connector_instances(tenant_id,id),CONSTRAINT chk_connector_instance_settings_one_value CHECK((value_text IS NOT NULL)::int+(value_number IS NOT NULL)::int+(value_bool IS NOT NULL)::int+(secret_ref IS NOT NULL)::int=1));
ALTER TABLE tenant.job_board_postings ADD CONSTRAINT fk_job_board_postings_connector FOREIGN KEY(tenant_id,connector_instance_id) REFERENCES tenant.connector_instances(tenant_id,id);

CREATE TABLE tenant.sync_jobs (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),connector_instance_id uuid NOT NULL,sync_type sync_type_enum NOT NULL,status sync_status_enum NOT NULL DEFAULT 'pending',external_cursor text,last_sync_at timestamptz,records_processed integer NOT NULL DEFAULT 0 CHECK(records_processed>=0),records_failed integer NOT NULL DEFAULT 0 CHECK(records_failed>=0),started_at timestamptz,completed_at timestamptz,error_message text,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_sync_jobs_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_sync_jobs_instance FOREIGN KEY(tenant_id,connector_instance_id) REFERENCES tenant.connector_instances(tenant_id,id));
CREATE TABLE tenant.sync_job_records (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),sync_job_id uuid NOT NULL,external_record_id text NOT NULL,record_status sync_status_enum NOT NULL,platform_table text,platform_record_id uuid,error_message text,processed_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_sync_job_records_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_sync_job_records_external UNIQUE(tenant_id,sync_job_id,external_record_id),CONSTRAINT fk_sync_job_records_job FOREIGN KEY(tenant_id,sync_job_id) REFERENCES tenant.sync_jobs(tenant_id,id));
CREATE TABLE tenant.webhook_events (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),connector_instance_id uuid,provider_event_id text NOT NULL,event_type text NOT NULL,signature_valid boolean NOT NULL DEFAULT false,payload jsonb NOT NULL,received_at timestamptz NOT NULL DEFAULT now(),processed_at timestamptz,status sync_status_enum NOT NULL DEFAULT 'pending',PRIMARY KEY(id),CONSTRAINT uq_webhook_events_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_webhook_events_provider UNIQUE(tenant_id,provider_event_id),CONSTRAINT fk_webhook_events_instance FOREIGN KEY(tenant_id,connector_instance_id) REFERENCES tenant.connector_instances(tenant_id,id));
CREATE TABLE tenant.webhook_subscriptions (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),name text NOT NULL,target_url text NOT NULL,signing_secret_ref text NOT NULL,status connector_status_enum NOT NULL DEFAULT 'connected',created_by_user_id uuid,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),deleted_at timestamptz,PRIMARY KEY(id),CONSTRAINT uq_webhook_subscriptions_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_webhook_subscriptions_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_webhook_subscriptions_user FOREIGN KEY(tenant_id,created_by_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.webhook_subscription_event_types (tenant_id uuid NOT NULL,webhook_subscription_id uuid NOT NULL,event_type text NOT NULL,PRIMARY KEY(tenant_id,webhook_subscription_id,event_type),CONSTRAINT fk_webhook_subscription_event_types_subscription FOREIGN KEY(tenant_id,webhook_subscription_id) REFERENCES tenant.webhook_subscriptions(tenant_id,id));
CREATE TABLE tenant.calendar_events (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),connector_instance_id uuid,external_event_id text,title text NOT NULL,start_at timestamptz NOT NULL,end_at timestamptz NOT NULL,timezone text NOT NULL,location text,meeting_url text,status text NOT NULL DEFAULT 'confirmed' CHECK(status IN('tentative','confirmed','cancelled')),created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_calendar_events_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_calendar_events_connector FOREIGN KEY(tenant_id,connector_instance_id) REFERENCES tenant.connector_instances(tenant_id,id),CONSTRAINT chk_calendar_events_time CHECK(end_at>start_at));
CREATE TABLE tenant.calendar_event_attendees (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),calendar_event_id uuid NOT NULL,email citext NOT NULL,user_id uuid,candidate_id uuid,client_contact_id uuid,response_status approval_status_enum NOT NULL DEFAULT 'pending',is_required boolean NOT NULL DEFAULT true,PRIMARY KEY(id),CONSTRAINT uq_calendar_event_attendees_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_calendar_event_attendees_event FOREIGN KEY(tenant_id,calendar_event_id) REFERENCES tenant.calendar_events(tenant_id,id),CONSTRAINT fk_calendar_event_attendees_user FOREIGN KEY(tenant_id,user_id) REFERENCES tenant.users(tenant_id,id),CONSTRAINT fk_calendar_event_attendees_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id),CONSTRAINT fk_calendar_event_attendees_contact FOREIGN KEY(tenant_id,client_contact_id) REFERENCES agency.client_contacts(tenant_id,id));
CREATE TABLE tenant.hrms_field_mappings (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),connector_instance_id uuid NOT NULL,platform_field text NOT NULL,external_field text NOT NULL,transformation_rule_key text,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_hrms_field_mappings_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_hrms_field_mappings_field UNIQUE(tenant_id,connector_instance_id,platform_field),CONSTRAINT fk_hrms_field_mappings_instance FOREIGN KEY(tenant_id,connector_instance_id) REFERENCES tenant.connector_instances(tenant_id,id));
CREATE TABLE tenant.hrms_sync_records (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),connector_instance_id uuid NOT NULL,candidate_id uuid,offer_id uuid,employee_external_id text,sync_status sync_status_enum NOT NULL DEFAULT 'pending',error_detail text,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_hrms_sync_records_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_hrms_sync_records_instance FOREIGN KEY(tenant_id,connector_instance_id) REFERENCES tenant.connector_instances(tenant_id,id),CONSTRAINT fk_hrms_sync_records_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id),CONSTRAINT fk_hrms_sync_records_offer FOREIGN KEY(tenant_id,offer_id) REFERENCES tenant.offers(tenant_id,id));

CREATE TABLE events.event_outbox (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),aggregate_reference_id uuid, event_type text NOT NULL,payload jsonb NOT NULL,status sync_status_enum NOT NULL DEFAULT 'pending',occurred_at timestamptz NOT NULL DEFAULT now(),published_at timestamptz,retry_count integer NOT NULL DEFAULT 0 CHECK(retry_count>=0),PRIMARY KEY(id),CONSTRAINT uq_event_outbox_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_event_outbox_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id));
CREATE TABLE events.domain_events (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),event_type text NOT NULL,entity_reference_id uuid,source_service text NOT NULL,payload jsonb NOT NULL,occurred_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id,occurred_at),CONSTRAINT uq_domain_events_tenant_id UNIQUE(tenant_id,id,occurred_at),CONSTRAINT fk_domain_events_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_domain_events_entity FOREIGN KEY(tenant_id,entity_reference_id) REFERENCES tenant.entity_references(tenant_id,id)) PARTITION BY RANGE(occurred_at);
CREATE TABLE events.domain_events_default PARTITION OF events.domain_events DEFAULT;
CREATE TABLE events.event_subscriptions (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),name text NOT NULL,target_url text NOT NULL,signing_secret_ref text NOT NULL,status connector_status_enum NOT NULL DEFAULT 'connected',created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_event_subscriptions_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_event_subscriptions_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id));
CREATE TABLE events.event_subscription_event_types (tenant_id uuid NOT NULL,event_subscription_id uuid NOT NULL,event_type text NOT NULL,PRIMARY KEY(tenant_id,event_subscription_id,event_type),CONSTRAINT fk_event_subscription_event_types_subscription FOREIGN KEY(tenant_id,event_subscription_id) REFERENCES events.event_subscriptions(tenant_id,id));
CREATE TABLE events.event_delivery_attempts (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),event_subscription_id uuid NOT NULL,domain_event_id uuid,attempt_number integer NOT NULL CHECK(attempt_number>0),status sync_status_enum NOT NULL,response_status integer,response_body text,attempted_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_event_delivery_attempts_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_event_delivery_attempts_subscription FOREIGN KEY(tenant_id,event_subscription_id) REFERENCES events.event_subscriptions(tenant_id,id));
CREATE TABLE events.idempotency_records (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),idempotency_key text NOT NULL,request_hash text NOT NULL,status text NOT NULL CHECK(status IN('in_progress','completed','failed')),result_payload jsonb,created_at timestamptz NOT NULL DEFAULT now(),expires_at timestamptz NOT NULL,PRIMARY KEY(id),CONSTRAINT uq_idempotency_records_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_idempotency_records_key UNIQUE(tenant_id,idempotency_key),CONSTRAINT fk_idempotency_records_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT chk_idempotency_records_expires CHECK(expires_at>created_at));

CREATE TABLE tenant.review_items (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),source_module text NOT NULL,source_action_type ai_action_type_enum NOT NULL,entity_reference_id uuid NOT NULL,ai_output_text text NOT NULL,ai_output_raw_snapshot jsonb,ai_confidence confidence_score NOT NULL,ai_reasoning_summary text NOT NULL,status review_item_status_enum NOT NULL DEFAULT 'pending',assigned_to_user_id uuid,assigned_to_role_id uuid,sla_due_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),lock_version bigint NOT NULL DEFAULT 0,PRIMARY KEY(id),CONSTRAINT uq_review_items_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_review_items_entity FOREIGN KEY(tenant_id,entity_reference_id) REFERENCES tenant.entity_references(tenant_id,id),CONSTRAINT fk_review_items_user FOREIGN KEY(tenant_id,assigned_to_user_id) REFERENCES tenant.users(tenant_id,id),CONSTRAINT fk_review_items_role FOREIGN KEY(tenant_id,assigned_to_role_id) REFERENCES tenant.roles(tenant_id,id),CONSTRAINT chk_review_items_assignee CHECK(assigned_to_user_id IS NOT NULL OR assigned_to_role_id IS NOT NULL));
CREATE TABLE tenant.review_item_relations (tenant_id uuid NOT NULL,review_item_id uuid NOT NULL,related_review_item_id uuid NOT NULL,relation_key text NOT NULL,PRIMARY KEY(tenant_id,review_item_id,related_review_item_id),CONSTRAINT fk_review_item_relations_item FOREIGN KEY(tenant_id,review_item_id) REFERENCES tenant.review_items(tenant_id,id),CONSTRAINT fk_review_item_relations_related FOREIGN KEY(tenant_id,related_review_item_id) REFERENCES tenant.review_items(tenant_id,id));
CREATE TABLE tenant.human_decisions (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),review_item_id uuid NOT NULL,decision review_item_status_enum NOT NULL,original_ai_output_text text NOT NULL,modified_output_text text,reason_code text,free_text_comment text,decided_by_user_id uuid NOT NULL,decided_at timestamptz NOT NULL DEFAULT now(),created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_human_decisions_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_human_decisions_item FOREIGN KEY(tenant_id,review_item_id) REFERENCES tenant.review_items(tenant_id,id),CONSTRAINT fk_human_decisions_user FOREIGN KEY(tenant_id,decided_by_user_id) REFERENCES tenant.users(tenant_id,id));

CREATE TABLE notif.notification_templates (id uuid PRIMARY KEY DEFAULT gen_random_uuid(),template_key citext NOT NULL,category notif_category_enum NOT NULL,name text NOT NULL,is_system boolean NOT NULL DEFAULT true,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),CONSTRAINT uq_notification_templates_key UNIQUE(template_key));
CREATE TABLE notif.notification_template_channels (template_id uuid NOT NULL,channel notif_channel_enum NOT NULL,PRIMARY KEY(template_id,channel),CONSTRAINT fk_notification_template_channels_template FOREIGN KEY(template_id) REFERENCES notif.notification_templates(id));
CREATE TABLE notif.notification_template_variables (template_id uuid NOT NULL,variable_key citext NOT NULL,is_required boolean NOT NULL DEFAULT true,PRIMARY KEY(template_id,variable_key),CONSTRAINT fk_notification_template_variables_template FOREIGN KEY(template_id) REFERENCES notif.notification_templates(id));
CREATE TABLE notif.notification_template_contents (id uuid PRIMARY KEY DEFAULT gen_random_uuid(),template_id uuid NOT NULL,channel notif_channel_enum NOT NULL,locale text NOT NULL DEFAULT 'en',subject text,body_text text NOT NULL,body_html text,created_at timestamptz NOT NULL DEFAULT now(),CONSTRAINT fk_notification_template_contents_template FOREIGN KEY(template_id) REFERENCES notif.notification_templates(id),CONSTRAINT uq_notification_template_contents_template_channel_locale UNIQUE(template_id,channel,locale));
CREATE TABLE tenant.notification_template_overrides (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),template_id uuid NOT NULL,is_active boolean NOT NULL DEFAULT true,created_by_user_id uuid,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_notification_template_overrides_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_notification_template_overrides_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_notification_template_overrides_template FOREIGN KEY(template_id) REFERENCES notif.notification_templates(id),CONSTRAINT fk_notification_template_overrides_user FOREIGN KEY(tenant_id,created_by_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.notification_template_override_contents (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),override_id uuid NOT NULL,channel notif_channel_enum NOT NULL,locale text NOT NULL DEFAULT 'en',subject text,body_text text NOT NULL,body_html text,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_notification_template_override_contents_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_notification_template_override_contents_locale UNIQUE(tenant_id,override_id,channel,locale),CONSTRAINT fk_notification_template_override_contents_override FOREIGN KEY(tenant_id,override_id) REFERENCES tenant.notification_template_overrides(tenant_id,id));
CREATE TABLE notif.notification_events (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),template_id uuid,category notif_category_enum NOT NULL,recipient_type notif_recipient_type_enum NOT NULL,user_id uuid,candidate_id uuid,client_contact_id uuid,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_notification_events_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_notification_events_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_notification_events_template FOREIGN KEY(template_id) REFERENCES notif.notification_templates(id),CONSTRAINT fk_notification_events_user FOREIGN KEY(tenant_id,user_id) REFERENCES tenant.users(tenant_id,id),CONSTRAINT fk_notification_events_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id),CONSTRAINT fk_notification_events_contact FOREIGN KEY(tenant_id,client_contact_id) REFERENCES agency.client_contacts(tenant_id,id));
CREATE TABLE notif.notification_event_variables (tenant_id uuid NOT NULL,notification_event_id uuid NOT NULL,variable_key citext NOT NULL,variable_value text NOT NULL,PRIMARY KEY(tenant_id,notification_event_id,variable_key),CONSTRAINT fk_notification_event_variables_event FOREIGN KEY(tenant_id,notification_event_id) REFERENCES notif.notification_events(tenant_id,id));
CREATE TABLE notif.notification_deliveries (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),notification_event_id uuid NOT NULL,channel notif_channel_enum NOT NULL,status notif_delivery_status_enum NOT NULL DEFAULT 'queued',provider_message_id text,queued_at timestamptz NOT NULL DEFAULT now(),sent_at timestamptz,delivered_at timestamptz,failed_at timestamptz,error_message text,PRIMARY KEY(id),CONSTRAINT uq_notification_deliveries_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_notification_deliveries_event FOREIGN KEY(tenant_id,notification_event_id) REFERENCES notif.notification_events(tenant_id,id));
CREATE TABLE notif.notification_delivery_attempts (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),notification_delivery_id uuid NOT NULL,attempt_number integer NOT NULL CHECK(attempt_number>0),status notif_delivery_status_enum NOT NULL,response_status integer,response_body text,attempted_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_notification_delivery_attempts_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_notification_delivery_attempts_delivery FOREIGN KEY(tenant_id,notification_delivery_id) REFERENCES notif.notification_deliveries(tenant_id,id));
CREATE TABLE tenant.notification_preferences (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),user_id uuid,candidate_id uuid,client_contact_id uuid,category notif_category_enum NOT NULL,enabled boolean NOT NULL DEFAULT true,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_notification_preferences_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_notification_preferences_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_notification_preferences_user FOREIGN KEY(tenant_id,user_id) REFERENCES tenant.users(tenant_id,id),CONSTRAINT fk_notification_preferences_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id),CONSTRAINT fk_notification_preferences_contact FOREIGN KEY(tenant_id,client_contact_id) REFERENCES agency.client_contacts(tenant_id,id),CONSTRAINT chk_notification_preferences_one_subject CHECK((user_id IS NOT NULL)::int+(candidate_id IS NOT NULL)::int+(client_contact_id IS NOT NULL)::int=1));
CREATE TABLE tenant.notification_preference_channels (tenant_id uuid NOT NULL,notification_preference_id uuid NOT NULL,channel notif_channel_enum NOT NULL,enabled boolean NOT NULL DEFAULT true,PRIMARY KEY(tenant_id,notification_preference_id,channel),CONSTRAINT fk_notification_preference_channels_pref FOREIGN KEY(tenant_id,notification_preference_id) REFERENCES tenant.notification_preferences(tenant_id,id));
CREATE TABLE notif.suppression_list (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),recipient_email citext,recipient_phone_e164 text,channel notif_channel_enum NOT NULL,reason suppression_reason_enum NOT NULL,starts_at timestamptz NOT NULL DEFAULT now(),ends_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_suppression_list_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_suppression_list_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT chk_suppression_list_recipient CHECK(recipient_email IS NOT NULL OR recipient_phone_e164 IS NOT NULL));

INSERT INTO platform.allowed_jsonb_columns(schema_name, table_name, column_name, allowed_reason) VALUES
('tenant','webhook_events','payload','Immutable raw inbound webhook payload'),
('events','event_outbox','payload','Immutable raw outbound event payload'),
('events','domain_events','payload','Immutable raw domain event payload'),
('events','idempotency_records','result_payload','Immutable response snapshot for idempotency replay'),
('tenant','review_items','ai_output_raw_snapshot','Immutable raw AI output snapshot')
ON CONFLICT DO NOTHING;
-- ============================================================
-- File 09: Billing, subscription, metering, invoices, payments, credits
-- ============================================================
CREATE TABLE billing.subscriptions (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),plan_id uuid NOT NULL,status text NOT NULL DEFAULT 'active' CHECK(status IN('trialing','active','past_due','suspended','cancelled','churned')),billing_interval billing_interval_enum NOT NULL,current_period_start date NOT NULL,current_period_end date NOT NULL,trial_ends_at timestamptz,cancelled_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),lock_version bigint NOT NULL DEFAULT 0,PRIMARY KEY(id),CONSTRAINT uq_subscriptions_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_subscriptions_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_subscriptions_plan FOREIGN KEY(plan_id) REFERENCES platform.plans(id),CONSTRAINT chk_subscriptions_period CHECK(current_period_end>=current_period_start));
CREATE UNIQUE INDEX uq_subscriptions_active_tenant ON billing.subscriptions(tenant_id) WHERE status IN('trialing','active','past_due','suspended');
CREATE TABLE billing.subscription_items (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),subscription_id uuid NOT NULL,addon_id uuid,quantity integer NOT NULL DEFAULT 1 CHECK(quantity>0),unit_price positive_money NOT NULL DEFAULT 0,currency currency_code NOT NULL DEFAULT 'USD',created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_subscription_items_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_subscription_items_subscription FOREIGN KEY(tenant_id,subscription_id) REFERENCES billing.subscriptions(tenant_id,id),CONSTRAINT fk_subscription_items_addon FOREIGN KEY(addon_id) REFERENCES platform.plan_addons(id));
CREATE TABLE billing.tenant_addon_subscriptions (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),subscription_id uuid NOT NULL,addon_id uuid NOT NULL,status text NOT NULL DEFAULT 'active' CHECK(status IN('active','cancelled','expired')),starts_at timestamptz NOT NULL DEFAULT now(),ends_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_tenant_addon_subscriptions_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_tenant_addon_subscriptions_subscription FOREIGN KEY(tenant_id,subscription_id) REFERENCES billing.subscriptions(tenant_id,id),CONSTRAINT fk_tenant_addon_subscriptions_addon FOREIGN KEY(addon_id) REFERENCES platform.plan_addons(id));
CREATE TABLE billing.tenant_quota_overrides (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),quota_definition_id uuid NOT NULL,override_limit numeric(18,4) NOT NULL CHECK(override_limit>=0),reason text NOT NULL,created_by_platform_user_id uuid,starts_at timestamptz NOT NULL DEFAULT now(),ends_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_tenant_quota_overrides_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_tenant_quota_overrides_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_tenant_quota_overrides_quota FOREIGN KEY(quota_definition_id) REFERENCES platform.quota_definitions(id),CONSTRAINT fk_tenant_quota_overrides_user FOREIGN KEY(created_by_platform_user_id) REFERENCES platform.platform_users(id));
CREATE TABLE billing.usage_events (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),quota_definition_id uuid NOT NULL,source usage_source_enum NOT NULL,quantity numeric(18,4) NOT NULL CHECK(quantity>=0),unit text NOT NULL,entity_reference_id uuid,occurred_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id,occurred_at),CONSTRAINT uq_usage_events_tenant_id UNIQUE(tenant_id,id,occurred_at),CONSTRAINT fk_usage_events_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_usage_events_quota FOREIGN KEY(quota_definition_id) REFERENCES platform.quota_definitions(id),CONSTRAINT fk_usage_events_entity FOREIGN KEY(tenant_id,entity_reference_id) REFERENCES tenant.entity_references(tenant_id,id)) PARTITION BY RANGE(occurred_at);
CREATE TABLE billing.usage_events_default PARTITION OF billing.usage_events DEFAULT;
CREATE TABLE billing.usage_aggregations (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),quota_definition_id uuid NOT NULL,period_start date NOT NULL,period_end date NOT NULL,quantity numeric(18,4) NOT NULL CHECK(quantity>=0),created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_usage_aggregations_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_usage_aggregations_key UNIQUE(tenant_id,quota_definition_id,period_start,period_end),CONSTRAINT fk_usage_aggregations_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_usage_aggregations_quota FOREIGN KEY(quota_definition_id) REFERENCES platform.quota_definitions(id),CONSTRAINT chk_usage_aggregations_period CHECK(period_end>=period_start));
CREATE TABLE billing.billing_addresses (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),line1 text NOT NULL,line2 text,city text NOT NULL,state_region text,postal_code text,country_code char(2) NOT NULL,tax_id text,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_billing_addresses_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_billing_addresses_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id));
CREATE TABLE billing.payment_methods (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),billing_address_id uuid,provider text NOT NULL,provider_payment_method_id text NOT NULL,method_type text NOT NULL CHECK(method_type IN('card','bank_transfer','upi','wire','manual')),brand text,last4 text,expiry_month smallint CHECK(expiry_month BETWEEN 1 AND 12),expiry_year smallint,is_default boolean NOT NULL DEFAULT false,revoked_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_payment_methods_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_payment_methods_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_payment_methods_address FOREIGN KEY(tenant_id,billing_address_id) REFERENCES billing.billing_addresses(tenant_id,id),CONSTRAINT uq_payment_methods_provider UNIQUE(provider,provider_payment_method_id));
CREATE UNIQUE INDEX uq_payment_methods_default ON billing.payment_methods(tenant_id) WHERE is_default AND revoked_at IS NULL;
CREATE TABLE billing.invoices (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),subscription_id uuid,invoice_number text NOT NULL,status invoice_status_enum NOT NULL DEFAULT 'draft',currency currency_code NOT NULL,total_amount positive_money NOT NULL DEFAULT 0,subtotal_amount positive_money NOT NULL DEFAULT 0,tax_amount positive_money NOT NULL DEFAULT 0,discount_amount positive_money NOT NULL DEFAULT 0,due_date date,issued_at timestamptz,paid_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_invoices_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_invoices_number UNIQUE(tenant_id,invoice_number),CONSTRAINT fk_invoices_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_invoices_subscription FOREIGN KEY(tenant_id,subscription_id) REFERENCES billing.subscriptions(tenant_id,id),CONSTRAINT chk_invoices_total CHECK(total_amount = subtotal_amount + tax_amount - discount_amount));
CREATE TABLE billing.invoice_line_items (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),invoice_id uuid NOT NULL,line_number integer NOT NULL CHECK(line_number>0),description text NOT NULL,quantity numeric(18,4) NOT NULL CHECK(quantity>0),unit_price positive_money NOT NULL,line_amount positive_money NOT NULL,quota_definition_id uuid,addon_id uuid,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_invoice_line_items_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_invoice_line_items_line UNIQUE(tenant_id,invoice_id,line_number),CONSTRAINT fk_invoice_line_items_invoice FOREIGN KEY(tenant_id,invoice_id) REFERENCES billing.invoices(tenant_id,id),CONSTRAINT fk_invoice_line_items_quota FOREIGN KEY(quota_definition_id) REFERENCES platform.quota_definitions(id),CONSTRAINT fk_invoice_line_items_addon FOREIGN KEY(addon_id) REFERENCES platform.plan_addons(id));
CREATE TABLE billing.invoice_taxes (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),invoice_id uuid NOT NULL,tax_type text NOT NULL,jurisdiction text NOT NULL,tax_rate percent_0_100 NOT NULL,tax_amount positive_money NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_invoice_taxes_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_invoice_taxes_invoice FOREIGN KEY(tenant_id,invoice_id) REFERENCES billing.invoices(tenant_id,id));
CREATE TABLE billing.payment_attempts (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),invoice_id uuid NOT NULL,payment_method_id uuid,provider text NOT NULL,provider_payment_id text,status payment_status_enum NOT NULL DEFAULT 'pending',amount positive_money NOT NULL,currency currency_code NOT NULL,attempted_at timestamptz NOT NULL DEFAULT now(),settled_at timestamptz,error_message text,PRIMARY KEY(id),CONSTRAINT uq_payment_attempts_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_payment_attempts_invoice FOREIGN KEY(tenant_id,invoice_id) REFERENCES billing.invoices(tenant_id,id),CONSTRAINT fk_payment_attempts_method FOREIGN KEY(tenant_id,payment_method_id) REFERENCES billing.payment_methods(tenant_id,id));
CREATE TABLE billing.credits (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),invoice_id uuid,amount positive_money NOT NULL,currency currency_code NOT NULL,reason text NOT NULL,issued_by_platform_user_id uuid,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_credits_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_credits_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_credits_invoice FOREIGN KEY(tenant_id,invoice_id) REFERENCES billing.invoices(tenant_id,id),CONSTRAINT fk_credits_user FOREIGN KEY(issued_by_platform_user_id) REFERENCES platform.platform_users(id));
-- ============================================================
-- File 10: Reporting, analytics, compliance, retention, evidence
-- ============================================================
CREATE TABLE tenant.dashboards (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),name text NOT NULL,owner_user_id uuid,is_default boolean NOT NULL DEFAULT false,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),deleted_at timestamptz,PRIMARY KEY(id),CONSTRAINT uq_dashboards_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_dashboards_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_dashboards_owner FOREIGN KEY(tenant_id,owner_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.dashboard_widgets (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),dashboard_id uuid NOT NULL,widget_key text NOT NULL,widget_type text NOT NULL,report_definition_id uuid,position_x integer NOT NULL DEFAULT 0,position_y integer NOT NULL DEFAULT 0,width integer NOT NULL CHECK(width>0),height integer NOT NULL CHECK(height>0),created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_dashboard_widgets_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_dashboard_widgets_dashboard FOREIGN KEY(tenant_id,dashboard_id) REFERENCES tenant.dashboards(tenant_id,id));
CREATE TABLE tenant.dashboard_shares (tenant_id uuid NOT NULL,dashboard_id uuid NOT NULL,user_id uuid NOT NULL,can_edit boolean NOT NULL DEFAULT false,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(tenant_id,dashboard_id,user_id),CONSTRAINT fk_dashboard_shares_dashboard FOREIGN KEY(tenant_id,dashboard_id) REFERENCES tenant.dashboards(tenant_id,id),CONSTRAINT fk_dashboard_shares_user FOREIGN KEY(tenant_id,user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.report_definitions (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),report_key citext NOT NULL,name text NOT NULL,owner_user_id uuid,base_view text NOT NULL,default_format report_format_enum NOT NULL DEFAULT 'csv',schedule_cron text,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),deleted_at timestamptz,PRIMARY KEY(id),CONSTRAINT uq_report_definitions_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_report_definitions_key UNIQUE(tenant_id,report_key),CONSTRAINT fk_report_definitions_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_report_definitions_owner FOREIGN KEY(tenant_id,owner_user_id) REFERENCES tenant.users(tenant_id,id));
ALTER TABLE tenant.dashboard_widgets ADD CONSTRAINT fk_dashboard_widgets_report FOREIGN KEY(tenant_id,report_definition_id) REFERENCES tenant.report_definitions(tenant_id,id);
CREATE TABLE tenant.report_filters (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),report_definition_id uuid NOT NULL,field_key text NOT NULL,operator condition_operator_enum NOT NULL,value_text text,value_number numeric(18,6),value_bool boolean,value_date date,PRIMARY KEY(id),CONSTRAINT uq_report_filters_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_report_filters_report FOREIGN KEY(tenant_id,report_definition_id) REFERENCES tenant.report_definitions(tenant_id,id));
CREATE TABLE tenant.report_columns (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),report_definition_id uuid NOT NULL,column_key text NOT NULL,label text NOT NULL,sort_order integer NOT NULL DEFAULT 0,is_group_by boolean NOT NULL DEFAULT false,PRIMARY KEY(id),CONSTRAINT uq_report_columns_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_report_columns_key UNIQUE(tenant_id,report_definition_id,column_key),CONSTRAINT fk_report_columns_report FOREIGN KEY(tenant_id,report_definition_id) REFERENCES tenant.report_definitions(tenant_id,id));
CREATE TABLE tenant.report_schedule_recipients (tenant_id uuid NOT NULL,report_definition_id uuid NOT NULL,user_id uuid NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(tenant_id,report_definition_id,user_id),CONSTRAINT fk_report_schedule_recipients_report FOREIGN KEY(tenant_id,report_definition_id) REFERENCES tenant.report_definitions(tenant_id,id),CONSTRAINT fk_report_schedule_recipients_user FOREIGN KEY(tenant_id,user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE tenant.export_jobs (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),report_definition_id uuid,requested_by_user_id uuid NOT NULL,format report_format_enum NOT NULL,status sync_status_enum NOT NULL DEFAULT 'pending',result_uri text,created_at timestamptz NOT NULL DEFAULT now(),completed_at timestamptz,PRIMARY KEY(id),CONSTRAINT uq_export_jobs_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_export_jobs_report FOREIGN KEY(tenant_id,report_definition_id) REFERENCES tenant.report_definitions(tenant_id,id),CONSTRAINT fk_export_jobs_user FOREIGN KEY(tenant_id,requested_by_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE analytics.metric_definitions (id uuid PRIMARY KEY DEFAULT gen_random_uuid(),metric_key citext NOT NULL,display_name text NOT NULL,unit text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),CONSTRAINT uq_metric_definitions_key UNIQUE(metric_key));
CREATE TABLE analytics.dimension_definitions (id uuid PRIMARY KEY DEFAULT gen_random_uuid(),dimension_key citext NOT NULL,display_name text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),CONSTRAINT uq_dimension_definitions_key UNIQUE(dimension_key));
CREATE TABLE analytics.analytics_events (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),event_key text NOT NULL,entity_reference_id uuid,occurred_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id,occurred_at),CONSTRAINT uq_analytics_events_tenant_id UNIQUE(tenant_id,id,occurred_at),CONSTRAINT fk_analytics_events_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_analytics_events_entity FOREIGN KEY(tenant_id,entity_reference_id) REFERENCES tenant.entity_references(tenant_id,id)) PARTITION BY RANGE(occurred_at);
CREATE TABLE analytics.analytics_events_default PARTITION OF analytics.analytics_events DEFAULT;
CREATE TABLE analytics.analytics_event_metric_values (tenant_id uuid NOT NULL,analytics_event_id uuid NOT NULL,metric_definition_id uuid NOT NULL,metric_value numeric(18,6) NOT NULL,occurred_at timestamptz NOT NULL,PRIMARY KEY(tenant_id,analytics_event_id,metric_definition_id),CONSTRAINT fk_analytics_event_metric_values_metric FOREIGN KEY(metric_definition_id) REFERENCES analytics.metric_definitions(id));
CREATE TABLE analytics.analytics_event_dimension_values (tenant_id uuid NOT NULL,analytics_event_id uuid NOT NULL,dimension_definition_id uuid NOT NULL,dimension_value text NOT NULL,occurred_at timestamptz NOT NULL,PRIMARY KEY(tenant_id,analytics_event_id,dimension_definition_id),CONSTRAINT fk_analytics_event_dimension_values_dimension FOREIGN KEY(dimension_definition_id) REFERENCES analytics.dimension_definitions(id));
CREATE TABLE analytics.daily_metric_facts (tenant_id uuid NOT NULL,metric_definition_id uuid NOT NULL,fact_date date NOT NULL,dimension_hash text NOT NULL DEFAULT 'all',metric_value numeric(18,6) NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(tenant_id,metric_definition_id,fact_date,dimension_hash),CONSTRAINT fk_daily_metric_facts_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_daily_metric_facts_metric FOREIGN KEY(metric_definition_id) REFERENCES analytics.metric_definitions(id));
CREATE TABLE compliance.retention_policies (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),resource_key text NOT NULL,retention_days integer NOT NULL CHECK(retention_days>0),archive_after_days integer CHECK(archive_after_days IS NULL OR archive_after_days>0),is_active boolean NOT NULL DEFAULT true,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_retention_policies_tenant_id UNIQUE(tenant_id,id),CONSTRAINT uq_retention_policies_resource UNIQUE(tenant_id,resource_key),CONSTRAINT fk_retention_policies_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id));
CREATE TABLE compliance.legal_holds (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),candidate_id uuid,entity_reference_id uuid,reason text NOT NULL,status text NOT NULL DEFAULT 'active' CHECK(status IN('active','released')),placed_by_user_id uuid,placed_at timestamptz NOT NULL DEFAULT now(),released_at timestamptz,PRIMARY KEY(id),CONSTRAINT uq_legal_holds_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_legal_holds_candidate FOREIGN KEY(tenant_id,candidate_id) REFERENCES tenant.candidates(tenant_id,id),CONSTRAINT fk_legal_holds_entity FOREIGN KEY(tenant_id,entity_reference_id) REFERENCES tenant.entity_references(tenant_id,id),CONSTRAINT fk_legal_holds_user FOREIGN KEY(tenant_id,placed_by_user_id) REFERENCES tenant.users(tenant_id,id));
CREATE TABLE compliance.evidence_packages (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),framework compliance_framework_enum NOT NULL,period_start date NOT NULL,period_end date NOT NULL,status text NOT NULL DEFAULT 'draft' CHECK(status IN('draft','collecting','ready','submitted','accepted')),created_by_user_id uuid,storage_uri text,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_evidence_packages_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_evidence_packages_tenant FOREIGN KEY(tenant_id) REFERENCES platform.tenants(id),CONSTRAINT fk_evidence_packages_user FOREIGN KEY(tenant_id,created_by_user_id) REFERENCES tenant.users(tenant_id,id),CONSTRAINT chk_evidence_packages_period CHECK(period_end>=period_start));
CREATE TABLE compliance.evidence_items (tenant_id uuid NOT NULL,id uuid NOT NULL DEFAULT gen_random_uuid(),evidence_package_id uuid NOT NULL,evidence_key text NOT NULL,source_table text,source_id uuid,storage_uri text,status sync_status_enum NOT NULL DEFAULT 'pending',created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(id),CONSTRAINT uq_evidence_items_tenant_id UNIQUE(tenant_id,id),CONSTRAINT fk_evidence_items_package FOREIGN KEY(tenant_id,evidence_package_id) REFERENCES compliance.evidence_packages(tenant_id,id));
-- ============================================================
-- File 11: Row-level security enablement and policies
-- Uses app.current_tenant_id(), app.is_platform_admin(), app.has_permission().
-- ============================================================
DO $$
DECLARE
  r record;
BEGIN
  FOR r IN
    SELECT n.nspname AS schema_name, c.relname AS table_name
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'tenant_id' AND NOT a.attisdropped
    WHERE c.relkind IN ('r','p')
      AND n.nspname IN ('tenant','agency','ai','events','integrations','notif','billing','analytics','compliance')
  LOOP
    EXECUTE format('ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY', r.schema_name, r.table_name);
    EXECUTE format('ALTER TABLE %I.%I FORCE ROW LEVEL SECURITY', r.schema_name, r.table_name);
    EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I.%I', r.schema_name, r.table_name);
    EXECUTE format('CREATE POLICY tenant_isolation ON %I.%I USING (tenant_id = app.current_tenant_id() OR app.is_platform_admin()) WITH CHECK (tenant_id = app.current_tenant_id() OR app.is_platform_admin())', r.schema_name, r.table_name);
  END LOOP;
END $$;

-- Sensitive data requires explicit permission in addition to tenant isolation.
DROP POLICY IF EXISTS candidate_contacts_sensitive_read ON tenant.candidate_contacts;
CREATE POLICY candidate_contacts_sensitive_read ON tenant.candidate_contacts AS RESTRICTIVE FOR SELECT USING (app.has_permission('candidate.contact.read'));
DROP POLICY IF EXISTS candidate_documents_sensitive_read ON tenant.candidate_documents;
CREATE POLICY candidate_documents_sensitive_read ON tenant.candidate_documents AS RESTRICTIVE FOR SELECT USING (app.has_permission('candidate.document.read'));
DROP POLICY IF EXISTS candidate_eeo_sensitive_read ON tenant.candidate_eeo_data;
CREATE POLICY candidate_eeo_sensitive_read ON tenant.candidate_eeo_data AS RESTRICTIVE FOR SELECT USING (app.has_permission('candidate.eeo.read'));
DROP POLICY IF EXISTS offers_compensation_sensitive_read ON tenant.offers;
CREATE POLICY offers_compensation_sensitive_read ON tenant.offers AS RESTRICTIVE FOR SELECT USING (app.has_permission('offer.read'));
DROP POLICY IF EXISTS billing_sensitive_read ON billing.invoices;
CREATE POLICY billing_sensitive_read ON billing.invoices AS RESTRICTIVE FOR SELECT USING (app.has_permission('billing.invoice.read'));
DROP POLICY IF EXISTS ai_evaluation_sensitive_read ON ai.interview_evaluations;
CREATE POLICY ai_evaluation_sensitive_read ON ai.interview_evaluations AS RESTRICTIVE FOR SELECT USING (app.has_permission('ai.evaluation.read'));

-- Platform admin tables are not tenant-facing; access is controlled by database grants/application service layer.
-- ============================================================
-- File 12: Cross-cutting indexes, triggers, audit/immutability, views
-- ============================================================

-- updated_at and optimistic lock triggers on all mutable tables.
DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT n.nspname AS schema_name, c.relname AS table_name
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    JOIN pg_attribute a ON a.attrelid=c.oid AND a.attname='updated_at' AND NOT a.attisdropped
    WHERE c.relkind='r' AND n.nspname IN ('platform','tenant','agency','ai','events','integrations','notif','billing','analytics','compliance')
  LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS trg_%I_set_updated_at ON %I.%I', r.table_name, r.schema_name, r.table_name);
    EXECUTE format('CREATE TRIGGER trg_%I_set_updated_at BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION app.set_updated_at()', r.table_name, r.schema_name, r.table_name);
  END LOOP;

  FOR r IN
    SELECT n.nspname AS schema_name, c.relname AS table_name
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    JOIN pg_attribute a ON a.attrelid=c.oid AND a.attname='lock_version' AND NOT a.attisdropped
    WHERE c.relkind='r' AND n.nspname IN ('platform','tenant','agency','ai','billing')
  LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS trg_%I_bump_lock_version ON %I.%I', r.table_name, r.schema_name, r.table_name);
    EXECUTE format('CREATE TRIGGER trg_%I_bump_lock_version BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION app.bump_lock_version()', r.table_name, r.schema_name, r.table_name);
  END LOOP;
END $$;

-- Append-only protection.
DO $$
DECLARE tbl text;
BEGIN
  FOREACH tbl IN ARRAY ARRAY[
    'platform.audit_logs','tenant.security_events','events.domain_events','billing.usage_events','ai.ai_usage_events','analytics.analytics_events'
  ] LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS trg_append_only_guard ON %s', tbl);
    EXECUTE format('CREATE TRIGGER trg_append_only_guard BEFORE UPDATE OR DELETE ON %s FOR EACH ROW EXECUTE FUNCTION app.deny_update_delete()', tbl);
  END LOOP;
END $$;

-- Lightweight audit trigger for mutable tenant tables.
CREATE OR REPLACE FUNCTION app.audit_row_change()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  v_tenant_id uuid;
  v_object_id uuid;
BEGIN
  v_tenant_id := COALESCE((to_jsonb(NEW)->>'tenant_id')::uuid, (to_jsonb(OLD)->>'tenant_id')::uuid);
  v_object_id := COALESCE((to_jsonb(NEW)->>'id')::uuid, (to_jsonb(OLD)->>'id')::uuid);
  INSERT INTO platform.audit_logs(tenant_id, actor_type, actor_tenant_user_id, action_key, object_schema, object_table, object_id, before_state, after_state, occurred_at)
  VALUES (v_tenant_id, 'tenant_user', app.current_user_id(), TG_OP, TG_TABLE_SCHEMA, TG_TABLE_NAME, v_object_id, CASE WHEN TG_OP IN ('UPDATE','DELETE') THEN to_jsonb(OLD) END, CASE WHEN TG_OP IN ('INSERT','UPDATE') THEN to_jsonb(NEW) END, now());
  RETURN COALESCE(NEW, OLD);
END;
$$;

DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT n.nspname AS schema_name, c.relname AS table_name
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    JOIN pg_attribute a ON a.attrelid=c.oid AND a.attname='tenant_id' AND NOT a.attisdropped
    WHERE c.relkind='r' AND n.nspname IN ('tenant','agency','ai','billing')
      AND c.relname NOT LIKE '%events%'
  LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS trg_%I_audit ON %I.%I', r.table_name, r.schema_name, r.table_name);
    EXECUTE format('CREATE TRIGGER trg_%I_audit AFTER INSERT OR UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION app.audit_row_change()', r.table_name, r.schema_name, r.table_name);
  END LOOP;
END $$;

-- High-value lookup and tenant-aware indexes.
CREATE INDEX idx_candidates_tenant_name_trgm ON tenant.candidates USING gin (tenant_id, full_name gin_trgm_ops);
CREATE INDEX idx_candidates_tenant_email ON tenant.candidates(tenant_id, primary_email) WHERE deleted_at IS NULL;
CREATE INDEX idx_requisitions_tenant_status ON tenant.requisitions(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_applications_tenant_req_status ON tenant.applications(tenant_id, requisition_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_submittals_tenant_mandate_status ON agency.submittals(tenant_id, mandate_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_review_items_queue ON tenant.review_items(tenant_id, status, assigned_to_user_id, sla_due_at);
CREATE INDEX idx_notification_deliveries_status ON notif.notification_deliveries(tenant_id, status, queued_at);
CREATE INDEX idx_usage_aggregations_period ON billing.usage_aggregations(tenant_id, period_start, period_end);
CREATE INDEX idx_ai_usage_events_tenant_time ON ai.ai_usage_events(tenant_id, occurred_at DESC);
CREATE INDEX idx_domain_events_tenant_type_time ON events.domain_events(tenant_id, event_type, occurred_at DESC);
CREATE INDEX idx_analytics_events_tenant_time ON analytics.analytics_events(tenant_id, occurred_at DESC);

CREATE OR REPLACE VIEW tenant.v_requisition_summary AS
SELECT r.tenant_id, r.id AS requisition_id, r.requisition_number, r.title, r.status,
       COUNT(a.id) AS application_count,
       COUNT(a.id) FILTER (WHERE a.status = 'hired') AS hired_count
FROM tenant.requisitions r
LEFT JOIN tenant.applications a ON a.tenant_id = r.tenant_id AND a.requisition_id = r.id
GROUP BY r.tenant_id, r.id, r.requisition_number, r.title, r.status;

CREATE OR REPLACE VIEW agency.v_client_mandate_summary AS
SELECT c.tenant_id, c.id AS client_id, c.name AS client_name, COUNT(m.id) AS mandate_count,
       COUNT(m.id) FILTER (WHERE m.status = 'active') AS active_mandate_count
FROM agency.clients c
LEFT JOIN agency.mandates m ON m.tenant_id = c.tenant_id AND m.client_id = c.id
GROUP BY c.tenant_id, c.id, c.name;

CREATE OR REPLACE VIEW ai.v_ai_review_queue AS
SELECT ri.tenant_id, ri.id AS review_item_id, ri.source_action_type, ri.status, ri.ai_confidence, ri.sla_due_at,
       er.display_label, u.display_name AS assigned_user
FROM tenant.review_items ri
JOIN tenant.entity_references er ON er.tenant_id = ri.tenant_id AND er.id = ri.entity_reference_id
LEFT JOIN tenant.users u ON u.tenant_id = ri.tenant_id AND u.id = ri.assigned_to_user_id;
-- ============================================================
-- File 13: Seed data for plans, quotas, features, config definitions, platform roles
-- ============================================================
INSERT INTO platform.quota_definitions(quota_key, display_name, unit, reset_period, is_metered) VALUES
('seats','Seats','seat','monthly',true),
('ai_tokens_monthly','AI tokens per month','token','monthly',true),
('voice_minutes_monthly','Voice minutes per month','minute','monthly',true),
('job_postings_monthly','Job postings per month','posting','monthly',true),
('api_calls_monthly','API calls per month','call','monthly',true)
ON CONFLICT (quota_key) DO NOTHING;

INSERT INTO platform.feature_definitions(feature_key, name, category, default_enabled, requires_human_governance) VALUES
('corporate_ats','Corporate ATS','ats',true,false),
('agency_ats','Agency ATS','ats',false,false),
('ai_recruiter','AI Recruiter','ai',false,true),
('ai_interviewer','AI Interviewer','ai',false,true),
('client_portal','Client Portal','agency',false,false),
('public_partner_api','Public Partner API','platform',false,false),
('white_labeling','White Labeling','platform',false,false),
('advanced_analytics','Advanced Analytics','analytics',false,false)
ON CONFLICT (feature_key) DO NOTHING;

INSERT INTO platform.plans(code, name, description, status, billing_interval, base_price, currency, min_seats, max_seats, trial_days) VALUES
('starter','Starter','Starter plan for small teams','active','monthly',0,'USD',1,10,14),
('professional','Professional','Professional ATS plan','active','monthly',299,'USD',5,100,14),
('enterprise','Enterprise','Enterprise contract-backed plan','active','custom',0,'USD',25,NULL,0)
ON CONFLICT (code) DO NOTHING;

INSERT INTO platform.platform_permissions(permission_key, description) VALUES
('platform.tenant.read','Read tenants'),
('platform.tenant.write','Modify tenants'),
('platform.support.impersonate','Start audited support session'),
('platform.billing.read','Read platform billing'),
('platform.governance.write','Manage AI governance')
ON CONFLICT (permission_key) DO NOTHING;
INSERT INTO platform.platform_roles(role_key, name, description) VALUES
('super_admin','Super Admin','Full platform administration'),
('support_admin','Support Admin','Audited support access'),
('ai_governance_admin','AI Governance Admin','Manage AI model/prompt governance')
ON CONFLICT (role_key) DO NOTHING;

INSERT INTO platform.config_definitions(config_key, name, value_type, default_bool, description) VALUES
('ai.human_review.required','Require human review for AI decisions','boolean',true,'Global default for AI decisions to require HITL'),
('security.mfa.required_for_admins','Require MFA for administrators','boolean',true,'MFA policy default'),
('notifications.email.enabled','Enable email notifications','boolean',true,'Controls email notification delivery')
ON CONFLICT (config_key) DO NOTHING;
INSERT INTO platform.config_scope_levels(config_definition_id, scope_level)
SELECT id, 'tenant'::config_scope_enum FROM platform.config_definitions
ON CONFLICT DO NOTHING;

INSERT INTO notif.notification_templates(template_key, category, name) VALUES
('approval_request','transactional','Approval Request'),
('interview_reminder','transactional','Interview Reminder'),
('ai_review_required','ai_alert','AI Review Required'),
('password_reset','transactional','Password Reset'),
('email_verification','transactional','Email Verification')
ON CONFLICT (template_key) DO NOTHING;
INSERT INTO notif.notification_template_channels(template_id, channel)
SELECT id, 'email'::notif_channel_enum FROM notif.notification_templates
ON CONFLICT DO NOTHING;
INSERT INTO analytics.metric_definitions(metric_key, display_name, unit) VALUES
('time_to_fill_days','Time to Fill','days'),
('application_count','Applications','count'),
('candidate_conversion_rate','Candidate Conversion Rate','percent'),
('ai_override_rate','AI Override Rate','percent'),
('placement_fee_revenue','Placement Fee Revenue','currency')
ON CONFLICT(metric_key) DO NOTHING;
INSERT INTO analytics.dimension_definitions(dimension_key, display_name) VALUES
('business_unit','Business Unit'),('requisition','Requisition'),('client','Client'),('source','Source'),('stage','Stage')
ON CONFLICT(dimension_key) DO NOTHING;
