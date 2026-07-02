"""Initial schema from SQLAlchemy models plus PostgreSQL-specific objects.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-01

The downgrade is intended for local development and test databases. Production
rollback for this baseline should restore from backup or rebuild an environment.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from db.models import Base
from db.models.core import DataTierEnum


revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMAS = [
    "app",
    "platform",
    "tenant",
    "agency",
    "ai",
    "events",
    "integrations",
    "notif",
    "billing",
    "analytics",
    "compliance",
]

EXTENSIONS = [
    "pgcrypto",
    "citext",
    "pg_trgm",
    "btree_gin",
    "btree_gist",
    "vector",
]

DEFAULT_PARTITIONS = [
    ("platform", "audit_logs_default", "audit_logs"),
    ("tenant", "security_events_default", "security_events"),
    ("ai", "ai_usage_events_default", "ai_usage_events"),
    ("events", "domain_events_default", "domain_events"),
    ("billing", "usage_events_default", "usage_events"),
    ("analytics", "analytics_events_default", "analytics_events"),
]

APP_CONTEXT_FUNCTIONS_SQL = """
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
"""

RLS_POLICIES_SQL = """
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
    EXECUTE format('CREATE POLICY tenant_isolation ON %I.%I USING (tenant_id = app.current_tenant_id() OR app.is_platform_admin()) WITH CHECK (tenant_id = app.current_tenant_id() OR app.is_platform_admin())', r.schema_name, r.table_name);
  END LOOP;
END $$;

CREATE POLICY candidate_contacts_sensitive_read ON tenant.candidate_contacts AS RESTRICTIVE FOR SELECT USING (app.has_permission('candidate.contact.read'));
CREATE POLICY candidate_documents_sensitive_read ON tenant.candidate_documents AS RESTRICTIVE FOR SELECT USING (app.has_permission('candidate.document.read'));
CREATE POLICY candidate_eeo_sensitive_read ON tenant.candidate_eeo_data AS RESTRICTIVE FOR SELECT USING (app.has_permission('candidate.eeo.read'));
CREATE POLICY offers_compensation_sensitive_read ON tenant.offers AS RESTRICTIVE FOR SELECT USING (app.has_permission('offer.read'));
CREATE POLICY billing_sensitive_read ON billing.invoices AS RESTRICTIVE FOR SELECT USING (app.has_permission('billing.invoice.read'));
CREATE POLICY ai_evaluation_sensitive_read ON ai.interview_evaluations AS RESTRICTIVE FOR SELECT USING (app.has_permission('ai.evaluation.read'));
"""

TRIGGERS_SQL = """
CREATE TRIGGER trg_entity_references_one_of
BEFORE INSERT OR UPDATE ON tenant.entity_references
FOR EACH ROW EXECUTE FUNCTION app.validate_one_of_refs();

DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT n.nspname AS schema_name, c.relname AS table_name
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    JOIN pg_attribute a ON a.attrelid=c.oid AND a.attname='updated_at' AND NOT a.attisdropped
    WHERE c.relkind='r' AND n.nspname IN ('platform','tenant','agency','ai','events','integrations','notif','billing','analytics','compliance')
  LOOP
    EXECUTE format('CREATE TRIGGER trg_%I_set_updated_at BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION app.set_updated_at()', r.table_name, r.schema_name, r.table_name);
  END LOOP;

  FOR r IN
    SELECT n.nspname AS schema_name, c.relname AS table_name
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    JOIN pg_attribute a ON a.attrelid=c.oid AND a.attname='lock_version' AND NOT a.attisdropped
    WHERE c.relkind='r' AND n.nspname IN ('platform','tenant','agency','ai','billing')
  LOOP
    EXECUTE format('CREATE TRIGGER trg_%I_bump_lock_version BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION app.bump_lock_version()', r.table_name, r.schema_name, r.table_name);
  END LOOP;
END $$;

DO $$
DECLARE tbl text;
BEGIN
  FOREACH tbl IN ARRAY ARRAY[
    'platform.audit_logs','tenant.security_events','events.domain_events','billing.usage_events','ai.ai_usage_events','analytics.analytics_events'
  ] LOOP
    EXECUTE format('CREATE TRIGGER trg_append_only_guard BEFORE UPDATE OR DELETE ON %s FOR EACH ROW EXECUTE FUNCTION app.deny_update_delete()', tbl);
  END LOOP;
END $$;

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
    EXECUTE format('CREATE TRIGGER trg_%I_audit AFTER INSERT OR UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION app.audit_row_change()', r.table_name, r.schema_name, r.table_name);
  END LOOP;
END $$;
"""

VIEWS_SQL = """
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
"""

SCHEMA_COMMENTS_SQL = """
COMMENT ON SCHEMA platform IS 'Platform-admin owned metadata, tenants, plans, global governance, and audit.';
COMMENT ON SCHEMA tenant IS 'Tenant-scoped identity, corporate ATS, candidate, configuration, workflow, and tenant-facing operations.';
COMMENT ON SCHEMA agency IS 'Agency/RPO/executive-search domain tables scoped by tenant and client.';
COMMENT ON SCHEMA ai IS 'AI recruiter, AI interview, telephony, evaluation, usage, and governance records.';
COMMENT ON SCHEMA events IS 'Internal domain events, outbox, webhook delivery, and idempotency.';
COMMENT ON SCHEMA billing IS 'Subscription, invoice, payment, metering, and revenue tables.';
COMMENT ON SCHEMA analytics IS 'Reporting metrics, dimensions, event facts, and aggregate facts.';
COMMENT ON SCHEMA compliance IS 'Retention, legal hold, evidence package, and DSR audit support.';

COMMENT ON TABLE platform.plans IS 'Subscription plan catalogue. Feature and quota entitlements are normalized into child tables.';
COMMENT ON TABLE platform.tenants IS 'Global tenant registry; tenant-scoped tables reference this and enforce tenant isolation with RLS.';
COMMENT ON TABLE platform.audit_logs IS 'Append-only audit log. JSONB is allowed only for immutable before/after/diff snapshots.';
COMMENT ON TABLE tenant.security_events IS 'Append-only security event stream. raw_event_snapshot is allowed JSONB for immutable provider/security payload capture.';
COMMENT ON TABLE tenant.candidates IS 'Tenant-owned canonical candidate profile. Sensitive contact/EEO/docs live in separate protected child tables.';
COMMENT ON TABLE tenant.requisitions IS 'Structured request to hire. Locations, openings, approvals, validation issues, and JDs are normalized child rows.';
"""

ALLOWED_JSONB_SEED_SQL = """
INSERT INTO platform.allowed_jsonb_columns(schema_name, table_name, column_name, allowed_reason) VALUES
('platform','audit_logs','before_state','Immutable audit before snapshot'),
('platform','audit_logs','after_state','Immutable audit after snapshot'),
('platform','audit_logs','diff_state','Immutable audit diff snapshot'),
('tenant','security_events','raw_event_snapshot','Immutable raw security/provider event snapshot'),
('tenant','workflow_template_change_log','diff_summary','Immutable workflow template change diff snapshot'),
('ai','conversation_messages','raw_model_response','Immutable raw model response snapshot'),
('ai','interview_evaluations','raw_model_response','Immutable raw model response snapshot'),
('tenant','webhook_events','payload','Immutable raw inbound webhook payload'),
('events','event_outbox','payload','Immutable raw outbound event payload'),
('events','domain_events','payload','Immutable raw domain event payload'),
('events','domain_events_default','payload','Inherited immutable raw domain event payload partition'),
('events','idempotency_records','result_payload','Immutable response snapshot for idempotency replay'),
('tenant','review_items','ai_output_raw_snapshot','Immutable raw AI output snapshot'),
('platform','audit_logs_default','before_state','Inherited immutable audit before snapshot partition'),
('platform','audit_logs_default','after_state','Inherited immutable audit after snapshot partition'),
('platform','audit_logs_default','diff_state','Inherited immutable audit diff snapshot partition')
ON CONFLICT DO NOTHING;
"""

PLATFORM_SEED_SQL = """
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
"""


def execute(sql: str) -> None:
    op.execute(sql)


def create_extensions() -> None:
    for extension in EXTENSIONS:
        execute(f'CREATE EXTENSION IF NOT EXISTS "{extension}"')


def create_schemas() -> None:
    for schema in SCHEMAS:
        execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')


def create_default_partitions() -> None:
    for schema, partition, parent in DEFAULT_PARTITIONS:
        execute(f'CREATE TABLE {schema}.{partition} PARTITION OF {schema}.{parent} DEFAULT')


def create_unused_schema_types() -> None:
    DataTierEnum.create(op.get_bind(), checkfirst=True)


def upgrade() -> None:
    create_extensions()
    create_schemas()
    execute(APP_CONTEXT_FUNCTIONS_SQL)
    create_unused_schema_types()
    Base.metadata.create_all(bind=op.get_bind())
    create_default_partitions()
    execute(SCHEMA_COMMENTS_SQL)
    execute(ALLOWED_JSONB_SEED_SQL)
    execute(RLS_POLICIES_SQL)
    execute(TRIGGERS_SQL)
    execute(VIEWS_SQL)
    execute(PLATFORM_SEED_SQL)


def downgrade() -> None:
    bind = op.get_bind()
    execute("DROP VIEW IF EXISTS ai.v_ai_review_queue")
    execute("DROP VIEW IF EXISTS agency.v_client_mandate_summary")
    execute("DROP VIEW IF EXISTS tenant.v_requisition_summary")

    execute("DROP FUNCTION IF EXISTS app.audit_row_change() CASCADE")
    execute("DROP FUNCTION IF EXISTS app.validate_one_of_refs() CASCADE")
    execute("DROP FUNCTION IF EXISTS app.deny_update_delete() CASCADE")
    execute("DROP FUNCTION IF EXISTS app.bump_lock_version() CASCADE")
    execute("DROP FUNCTION IF EXISTS app.set_updated_at() CASCADE")
    execute("DROP FUNCTION IF EXISTS app.has_permission(text) CASCADE")
    execute("DROP FUNCTION IF EXISTS app.is_platform_admin() CASCADE")
    execute("DROP FUNCTION IF EXISTS app.current_user_id() CASCADE")
    execute("DROP FUNCTION IF EXISTS app.current_tenant_id() CASCADE")

    for schema, partition, _parent in reversed(DEFAULT_PARTITIONS):
        execute(f"DROP TABLE IF EXISTS {schema}.{partition} CASCADE")

    Base.metadata.drop_all(bind=bind)
    DataTierEnum.drop(bind, checkfirst=True)

    for schema in reversed(SCHEMAS):
        execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
