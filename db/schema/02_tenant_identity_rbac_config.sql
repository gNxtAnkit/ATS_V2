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
