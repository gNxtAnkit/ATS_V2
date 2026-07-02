# SQLAlchemy model generation report

Generated from uploaded gNxtHire PostgreSQL schema artifacts.

## Counts

- ORM table models generated: 282
- PostgreSQL enum types generated in `core/database.py`: 73
- PostgreSQL domain types generated in `core/database.py`: 4
- Parsed CREATE INDEX statements represented in models: 26

## Domain grouping

- `domain_platform_admin`: 41 tables
- `domain_tenant_identity_rbac_config`: 39 tables
- `domain_candidate_domain`: 18 tables
- `domain_corporate_ats`: 30 tables
- `domain_agency_ats`: 18 tables
- `domain_workflow_engine`: 22 tables
- `domain_ai_recruiter_interview_telephony`: 47 tables
- `domain_integrations_events_notifications`: 36 tables
- `domain_billing_usage_revenue`: 13 tables
- `domain_reporting_analytics_compliance`: 18 tables

## Corrected SQL-to-ORM representation

The raw SQL contains one expression-based UNIQUE declaration inside `CREATE TABLE`, which PostgreSQL does not support as a table constraint. The generated SQLAlchemy model represents it as a unique `Index`, which is the correct PostgreSQL/Alembic representation.

- `tenant.pipeline_stage_definitions`
- `uq_pipeline_stage_definitions_key`
- columns/expression: `tenant_id`, `COALESCE(requisition_id,'00000000-0000-0000-0000-000000000000'::uuid)`, `stage_key`

## Alembic limitations

SQLAlchemy ORM models do not fully represent:
- RLS policies
- trigger functions and triggers
- views
- `CREATE EXTENSION`
- `CREATE SCHEMA`
- application context functions
- seed data
- default partition child tables

Add these as explicit Alembic operations around the model-generated table migration.
