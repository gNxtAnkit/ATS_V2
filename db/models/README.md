# gNxtHire SQLAlchemy Models - Short File Bundle

This bundle is ready to paste/extract into `db/models`.

## Files

- `core.py` - Declarative `Base`, naming convention, mixins, PostgreSQL domains/enums.
- `platform.py` - `platform` schema models.
- `tenant.py` - tenant identity, RBAC, ABAC, config, API key, connector-instance, dashboard/report tenant models.
- `candidates.py` - candidate domain models.
- `corporate.py` - corporate ATS models.
- `agency.py` - agency ATS/client portal/submittal/placement models.
- `workflow.py` - workflow/approval engine models.
- `ai.py` - AI recruiter/interview/telephony models.
- `integrations.py` - platform integration, event, notification, and related shared models.
- `billing.py` - billing, usage, subscription, invoice, payment, revenue models.
- `analytics.py` - reporting, analytics, compliance, retention, evidence models.
- `__init__.py` - central registry for Alembic model discovery.
- `alembic_env_snippet.py` - example `env.py` target metadata import.

## Alembic usage

In `alembic/env.py` use:

```python
from db.models import Base
target_metadata = Base.metadata
```

## Important migration note

These are SQLAlchemy ORM models for Alembic autogenerate/table metadata. PostgreSQL RLS policies,
custom trigger functions, views, some partition details, and seed data should still be managed as explicit
Alembic operations because SQLAlchemy table metadata cannot fully represent them safely.
