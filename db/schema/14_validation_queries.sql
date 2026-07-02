-- ============================================================
-- File 14: Validation queries for schema governance / CI checks
-- ============================================================

-- 1. Tenant-owned schemas/tables missing tenant_id.
SELECT n.nspname AS schema_name, c.relname AS table_name
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r','p')
  AND n.nspname IN ('tenant','agency','ai','events','integrations','notif','billing','analytics','compliance')
  AND NOT EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid AND a.attname = 'tenant_id' AND NOT a.attisdropped)
ORDER BY 1,2;

-- 2. Tenant-scoped tables without RLS enabled/forced.
SELECT n.nspname AS schema_name, c.relname AS table_name, c.relrowsecurity, c.relforcerowsecurity
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'tenant_id' AND NOT a.attisdropped
WHERE c.relkind IN ('r','p')
  AND n.nspname IN ('tenant','agency','ai','events','integrations','notif','billing','analytics','compliance')
  AND (NOT c.relrowsecurity OR NOT c.relforcerowsecurity)
ORDER BY 1,2;

-- 3. Tenant-scoped child FKs that do not include tenant_id.
SELECT con.conname AS fk_name, ns_child.nspname AS child_schema, child.relname AS child_table, ns_parent.nspname AS parent_schema, parent.relname AS parent_table
FROM pg_constraint con
JOIN pg_class child ON child.oid = con.conrelid
JOIN pg_namespace ns_child ON ns_child.oid = child.relnamespace
JOIN pg_class parent ON parent.oid = con.confrelid
JOIN pg_namespace ns_parent ON ns_parent.oid = parent.relnamespace
WHERE con.contype = 'f'
  AND ns_child.nspname IN ('tenant','agency','ai','events','integrations','notif','billing','analytics','compliance')
  AND EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = child.oid AND a.attname = 'tenant_id')
  AND EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = parent.oid AND a.attname = 'tenant_id')
  AND NOT EXISTS (
    SELECT 1
    FROM unnest(con.conkey) WITH ORDINALITY ck(attnum, ord)
    JOIN pg_attribute a ON a.attrelid = child.oid AND a.attnum = ck.attnum
    WHERE a.attname = 'tenant_id'
  )
ORDER BY 2,3,1;

-- 4. Remaining JSONB columns and why each is allowed.
SELECT n.nspname AS schema_name, c.relname AS table_name, a.attname AS column_name,
       COALESCE(aj.allowed_reason, 'NOT ALLOWED - normalize or add approved exception') AS allowed_reason
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_type t ON t.oid = a.atttypid
LEFT JOIN platform.allowed_jsonb_columns aj ON aj.schema_name = n.nspname AND aj.table_name = c.relname AND aj.column_name = a.attname
WHERE a.attnum > 0 AND NOT a.attisdropped AND t.typname = 'jsonb'
ORDER BY 1,2,3;

-- 5. Array columns and why each is allowed.
SELECT n.nspname AS schema_name, c.relname AS table_name, a.attname AS column_name,
       COALESCE(aa.allowed_reason, 'NOT ALLOWED - replace with child/junction table') AS allowed_reason
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_type t ON t.oid = a.atttypid
LEFT JOIN platform.allowed_array_columns aa ON aa.schema_name = n.nspname AND aa.table_name = c.relname AND aa.column_name = a.attname
WHERE a.attnum > 0 AND NOT a.attisdropped AND t.typtype = 'b' AND t.typcategory = 'A'
ORDER BY 1,2,3;

-- 6. Broad permissive RLS policies on sensitive tables.
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies
WHERE (schemaname, tablename) IN (
  ('tenant','candidate_contacts'),('tenant','candidate_documents'),('tenant','candidate_eeo_data'),
  ('tenant','offers'),('billing','invoices'),('ai','interview_evaluations')
)
AND permissive = 'PERMISSIVE'
AND (qual IS NULL OR qual NOT LIKE '%app.current_tenant_id%');

-- 7. FK columns missing supporting indexes.
WITH fk_cols AS (
  SELECT con.conname, con.conrelid, con.conkey
  FROM pg_constraint con WHERE con.contype = 'f'
)
SELECT conname AS fk_name, conrelid::regclass AS table_name
FROM fk_cols fk
WHERE NOT EXISTS (
  SELECT 1 FROM pg_index i
  WHERE i.indrelid = fk.conrelid
    AND i.indisvalid
    AND fk.conkey <@ string_to_array(i.indkey::text, ' ')::smallint[]
)
ORDER BY 2,1;

-- 8. Natural-key risk: tenant-scoped tables with tenant_id/id but no additional unique constraint.
SELECT n.nspname AS schema_name, c.relname AS table_name
FROM pg_class c
JOIN pg_namespace n ON n.oid=c.relnamespace
JOIN pg_attribute at ON at.attrelid=c.oid AND at.attname='tenant_id'
WHERE c.relkind='r' AND n.nspname IN ('tenant','agency','ai','billing','notif')
GROUP BY n.nspname, c.relname, c.oid
HAVING COUNT(*) FILTER (
  WHERE EXISTS (SELECT 1 FROM pg_constraint con WHERE con.conrelid=c.oid AND con.contype='u')
) = 0
ORDER BY 1,2;

-- 9. Tables with deleted_at but no active partial indexes.
SELECT n.nspname AS schema_name, c.relname AS table_name
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE c.relkind='r'
  AND EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid=c.oid AND a.attname='deleted_at' AND NOT a.attisdropped)
  AND NOT EXISTS (SELECT 1 FROM pg_index i WHERE i.indrelid=c.oid AND pg_get_expr(i.indpred, i.indrelid) ILIKE '%deleted_at IS NULL%')
ORDER BY 1,2;

-- 10. Append-only tables that do not have deny-update/delete triggers.
SELECT n.nspname AS schema_name, c.relname AS table_name
FROM (VALUES
  ('platform','audit_logs'),('tenant','security_events'),('events','domain_events'),
  ('billing','usage_events'),('ai','ai_usage_events'),('analytics','analytics_events')
) AS x(schema_name, table_name)
JOIN pg_namespace n ON n.nspname=x.schema_name
JOIN pg_class c ON c.relnamespace=n.oid AND c.relname=x.table_name
WHERE NOT EXISTS (
  SELECT 1 FROM pg_trigger t WHERE t.tgrelid=c.oid AND NOT t.tgisinternal AND t.tgname='trg_append_only_guard'
);
