import re
from pathlib import Path

from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import CheckConstraint

from db.models import Base


def test_generated_model_registry_imports_all_tables() -> None:
    configure_mappers()

    assert len(Base.metadata.tables) == 286
    assert "platform.tenants" in Base.metadata.tables
    assert "tenant.users" in Base.metadata.tables
    assert "tenant.candidates" in Base.metadata.tables
    assert "agency.clients" in Base.metadata.tables
    assert "events.event_outbox" in Base.metadata.tables
    assert "billing.invoices" in Base.metadata.tables


def test_model_table_inventory_matches_schema_sql_except_default_partitions() -> None:
    schema_directory = Path(__file__).resolve().parents[2] / "db" / "schema"
    sql_tables: set[str] = set()
    for sql_file in sorted(schema_directory.glob("[0-9][0-9]_*.sql")):
        if sql_file.name == "14_validation_queries.sql":
            continue
        sql_text = sql_file.read_text(encoding="utf-8")
        for match in re.finditer(r"CREATE\s+TABLE\s+([a-z_]+)\.([a-z_]+)", sql_text, flags=re.I):
            sql_tables.add(f"{match.group(1)}.{match.group(2)}")

    default_partitions = {
        "platform.audit_logs_default",
        "tenant.security_events_default",
        "ai.ai_usage_events_default",
        "events.domain_events_default",
        "billing.usage_events_default",
        "analytics.analytics_events_default",
    }

    assert sql_tables - set(Base.metadata.tables) == default_partitions
    assert set(Base.metadata.tables) - sql_tables == set()


def test_unnamed_check_constraints_get_unique_names() -> None:
    plans_table = Base.metadata.tables["platform.plans"]
    check_names = [
        constraint.name
        for constraint in plans_table.constraints
        if isinstance(constraint, CheckConstraint)
    ]

    assert len(check_names) == len(set(check_names))
    assert all(name and name.startswith("ck_plans_") for name in check_names)
