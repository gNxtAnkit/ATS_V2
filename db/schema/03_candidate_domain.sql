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
