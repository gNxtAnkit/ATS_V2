# Database Schema

This directory contains the regenerated PostgreSQL 16+ schema baseline.

## Execution Order

Run files in numeric order:

1. `00_extensions_schemas_types.sql`
2. `01_platform_admin.sql`
3. `02_tenant_identity_rbac_config.sql`
4. `03_candidate_domain.sql`
5. `04_corporate_ats.sql`
6. `05_agency_ats.sql`
7. `06_workflow_engine.sql`
8. `07_ai_recruiter_interview_telephony.sql`
9. `08_integrations_events_notifications.sql`
10. `09_billing_usage_revenue.sql`
11. `10_reporting_analytics_compliance.sql`
12. `11_rls_policies.sql`
13. `12_indexes_triggers_views.sql`
14. `13_seed_data.sql`

`14_validation_queries.sql` is run after migration as a validation gate.
