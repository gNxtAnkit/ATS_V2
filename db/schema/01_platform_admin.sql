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
  password_hash text,
  email_verified_at timestamptz,
  mfa_required boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  CONSTRAINT uq_platform_users_email UNIQUE (email)
);
COMMENT ON TABLE platform.platform_users IS 'Platform-admin identities. Auth (password/session/MFA/reset-token) is stored in the platform_user_sessions/platform_password_reset_tokens/platform_email_verification_tokens/platform_user_mfa_factors tables below, owned by the Identity service, never mixed with tenant.users.';

CREATE TABLE platform.platform_user_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform_user_id uuid NOT NULL,
  session_token_hash text NOT NULL,
  ip_address inet,
  user_agent text,
  mfa_verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  CONSTRAINT uq_platform_user_sessions_token_hash UNIQUE (session_token_hash),
  CONSTRAINT fk_platform_user_sessions_user FOREIGN KEY (platform_user_id) REFERENCES platform.platform_users(id),
  CONSTRAINT chk_platform_user_sessions_expires_after_created CHECK (expires_at > created_at)
);
CREATE INDEX ix_platform_user_sessions_platform_user_id ON platform.platform_user_sessions(platform_user_id);

CREATE TABLE platform.platform_password_reset_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform_user_id uuid NOT NULL,
  token_hmac text NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','used','expired','revoked')),
  requested_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  used_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_platform_password_reset_tokens_hmac UNIQUE (token_hmac),
  CONSTRAINT fk_platform_password_reset_tokens_user FOREIGN KEY (platform_user_id) REFERENCES platform.platform_users(id),
  CONSTRAINT chk_platform_password_reset_tokens_expires_after_requested CHECK (expires_at > requested_at)
);
CREATE INDEX ix_platform_password_reset_tokens_platform_user_id ON platform.platform_password_reset_tokens(platform_user_id);
CREATE UNIQUE INDEX uq_platform_password_reset_tokens_one_active ON platform.platform_password_reset_tokens(platform_user_id) WHERE status = 'pending';

CREATE TABLE platform.platform_email_verification_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform_user_id uuid NOT NULL,
  token_hmac text NOT NULL,
  email citext NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','used','expired','revoked')),
  requested_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  used_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_platform_email_verification_tokens_hmac UNIQUE (token_hmac),
  CONSTRAINT fk_platform_email_verification_tokens_user FOREIGN KEY (platform_user_id) REFERENCES platform.platform_users(id),
  CONSTRAINT chk_platform_email_verification_tokens_expires_after_requested CHECK (expires_at > requested_at)
);
CREATE INDEX ix_platform_email_verification_tokens_platform_user_id ON platform.platform_email_verification_tokens(platform_user_id);

CREATE TABLE platform.platform_user_mfa_factors (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform_user_id uuid NOT NULL,
  method mfa_method_enum NOT NULL,
  secret_ref text,
  phone_e164 text,
  is_primary boolean NOT NULL DEFAULT false,
  enabled_at timestamptz NOT NULL DEFAULT now(),
  disabled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_platform_user_mfa_factors_user FOREIGN KEY (platform_user_id) REFERENCES platform.platform_users(id)
);
CREATE INDEX ix_platform_user_mfa_factors_platform_user_id ON platform.platform_user_mfa_factors(platform_user_id);
CREATE UNIQUE INDEX uq_platform_user_mfa_factors_primary ON platform.platform_user_mfa_factors(platform_user_id) WHERE is_primary AND disabled_at IS NULL;

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
