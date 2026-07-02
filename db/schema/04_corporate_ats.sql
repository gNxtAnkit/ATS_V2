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
