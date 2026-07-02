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
