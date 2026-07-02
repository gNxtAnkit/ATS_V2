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
