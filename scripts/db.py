from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(REPOSITORY_ROOT / "packages" / "backend-common" / "src"))
if getattr(sys.modules.get("db"), "__file__", None) == __file__:
    del sys.modules["db"]

import psycopg
from sqlalchemy.dialects.postgresql import DOMAIN, ENUM
from sqlalchemy.orm import configure_mappers

from db.models import Base
from db.models.core import DataTierEnum

from gnxthire_common.config import get_settings
from gnxthire_common.migrations import assert_required_schema_files


SCHEMA_DIRECTORY = REPOSITORY_ROOT / "db" / "schema"
ALEMBIC_INI = REPOSITORY_ROOT / "alembic.ini"
EXPECTED_ALEMBIC_HEAD = "0003_platform_admin_perms"
EXPECTED_SCHEMAS = {
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
}
EXPECTED_EXTENSIONS = {"pgcrypto", "citext", "pg_trgm", "btree_gin", "btree_gist", "vector"}
EXPECTED_PARTITION_TABLES = {
    "platform.audit_logs_default",
    "tenant.security_events_default",
    "ai.ai_usage_events_default",
    "events.domain_events_default",
    "billing.usage_events_default",
    "analytics.analytics_events_default",
}

VALIDATION_FAILURE_MARKERS = (
    "NOT ALLOWED",
)
APPLICATION_SCHEMAS = {
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
}
INTENTIONALLY_GLOBAL_TABLES = {
    ("analytics", "dimension_definitions"),
    ("analytics", "metric_definitions"),
    ("notif", "notification_template_channels"),
    ("notif", "notification_template_contents"),
    ("notif", "notification_template_variables"),
    ("notif", "notification_templates"),
}
ADVISORY_VALIDATION_QUERIES = {
    7: "FK columns missing supporting indexes",
    8: "Natural-key risk",
    9: "Soft-delete tables without active partial indexes",
}


@dataclass(frozen=True)
class ValidationResult:
    name: str
    row_count: int
    failed: bool


def run(command: list[str]) -> None:
    print(f"+ {' '.join(command)}")
    completed_process = subprocess.run(command, cwd=REPOSITORY_ROOT, check=False)
    if completed_process.returncode != 0:
        raise SystemExit(completed_process.returncode)


def alembic(command: list[str]) -> None:
    if not ALEMBIC_INI.exists():
        raise SystemExit("Missing alembic.ini")
    run([sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI), *command])


def database_url() -> str:
    return str(get_settings().database_url).replace("postgresql+psycopg://", "postgresql://")


def expected_model_tables() -> set[str]:
    return set(Base.metadata.tables)


def expected_database_tables() -> set[str]:
    return expected_model_tables() | EXPECTED_PARTITION_TABLES


def expected_type_names() -> set[str]:
    model_type_names = {
        column.type.name
        for table in Base.metadata.tables.values()
        for column in table.columns
        if isinstance(column.type, (DOMAIN, ENUM)) and column.type.name is not None
    }
    return model_type_names | {DataTierEnum.name}


def sql_table_inventory() -> set[str]:
    import re

    sql_tables: set[str] = set()
    for sql_file in sorted(SCHEMA_DIRECTORY.glob("[0-9][0-9]_*.sql")):
        if sql_file.name == "14_validation_queries.sql":
            continue
        sql_text = sql_file.read_text(encoding="utf-8")
        for match in re.finditer(r"CREATE\s+TABLE\s+([a-z_]+)\.([a-z_]+)", sql_text, flags=re.I):
            sql_tables.add(f"{match.group(1)}.{match.group(2)}")
    return sql_tables


def assert_model_registry_matches_schema_artifacts() -> None:
    configure_mappers()
    missing_from_models = sql_table_inventory() - expected_database_tables()
    extra_model_tables = expected_model_tables() - sql_table_inventory()
    if missing_from_models or extra_model_tables:
        details = []
        if missing_from_models:
            details.append(f"missing from models/explicit partitions: {sorted(missing_from_models)}")
        if extra_model_tables:
            details.append(f"extra model tables: {sorted(extra_model_tables)}")
        raise SystemExit("Model/schema table inventory mismatch: " + "; ".join(details))


def split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    dollar_quote_tag: str | None = None
    single_quote = False
    double_quote = False
    index = 0

    while index < len(sql_text):
        char = sql_text[index]
        next_two = sql_text[index : index + 2]

        if not single_quote and not double_quote and dollar_quote_tag is None and next_two == "--":
            newline_index = sql_text.find("\n", index)
            if newline_index == -1:
                break
            index = newline_index + 1
            continue

        if char == "'" and not double_quote and dollar_quote_tag is None:
            single_quote = not single_quote
        elif char == '"' and not single_quote and dollar_quote_tag is None:
            double_quote = not double_quote
        elif char == "$" and not single_quote and not double_quote:
            closing_index = sql_text.find("$", index + 1)
            if closing_index != -1:
                tag = sql_text[index : closing_index + 1]
                tag_body = tag[1:-1]
                valid_tag = tag == "$$" or tag_body.replace("_", "").isalnum()
                if dollar_quote_tag is None and valid_tag:
                    dollar_quote_tag = tag
                elif dollar_quote_tag == tag:
                    dollar_quote_tag = None

        if char == ";" and not single_quote and not double_quote and dollar_quote_tag is None:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)
        index += 1

    trailing_statement = "".join(current).strip()
    if trailing_statement:
        statements.append(trailing_statement)
    return statements


def validation_query_name(statement: str, fallback_index: int) -> str:
    first_line = statement.splitlines()[0].strip()
    if first_line.startswith("--"):
        return first_line.removeprefix("--").strip()
    return f"validation_query_{fallback_index}"


def row_has_failure_marker(row: tuple[object, ...]) -> bool:
    return any(
        isinstance(value, str) and any(marker in value for marker in VALIDATION_FAILURE_MARKERS)
        for value in row
    )


def filtered_validation_rows(index: int, rows: list[tuple[object, ...]]) -> list[tuple[object, ...]]:
    if index == 1:
        return [row for row in rows if (str(row[0]), str(row[1])) not in INTENTIONALLY_GLOBAL_TABLES]
    if index in {4, 5}:
        return [
            row
            for row in rows
            if str(row[0]) in APPLICATION_SCHEMAS
            and f"{row[0]}.{row[1]}" not in EXPECTED_PARTITION_TABLES
            and row_has_failure_marker(row)
        ]
    if index in ADVISORY_VALIDATION_QUERIES:
        return []
    return rows


def should_fail_validation(index: int, rows: list[tuple[object, ...]]) -> bool:
    if not rows:
        return False
    return bool(filtered_validation_rows(index, rows))


def validate() -> None:
    assert_required_schema_files(SCHEMA_DIRECTORY)
    assert_model_registry_matches_schema_artifacts()
    validation_sql = (SCHEMA_DIRECTORY / "14_validation_queries.sql").read_text(encoding="utf-8")
    statements = split_sql_statements(validation_sql)
    results: list[ValidationResult] = []

    with psycopg.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            run_catalog_validation(cursor)
            for index, statement in enumerate(statements, start=1):
                cursor.execute(statement)
                rows = cursor.fetchall()
                name = validation_query_name(statement, index)
                failing_rows = filtered_validation_rows(index, rows)
                failed = bool(failing_rows)
                results.append(ValidationResult(name=name, row_count=len(failing_rows), failed=failed))
                if failed:
                    print(f"FAILED: {name} returned {len(failing_rows)} failing row(s)")
                    for row in failing_rows[:10]:
                        print(f"  {row}")
                elif index in ADVISORY_VALIDATION_QUERIES and rows:
                    print(
                        f"ADVISORY: {name} returned {len(rows)} governance finding(s); "
                        "not a Phase 1 blocking failure."
                    )
                else:
                    print(f"OK: {name} returned {len(rows)} row(s)")

    failures = [result for result in results if result.failed]
    if failures:
        raise SystemExit(f"Schema validation failed: {len(failures)} failing query group(s)")


def check() -> None:
    assert_required_schema_files(SCHEMA_DIRECTORY)
    assert_model_registry_matches_schema_artifacts()
    print(
        "DB model/schema artifact check passed: "
        f"{len(expected_model_tables())} model tables, "
        f"{len(EXPECTED_PARTITION_TABLES)} explicit partition tables."
    )


def fetch_names(cursor: psycopg.Cursor[tuple[object, ...]], sql: str) -> set[str]:
    cursor.execute(sql)
    return {str(row[0]) for row in cursor.fetchall()}


def assert_expected_set(name: str, actual: set[str], expected: set[str]) -> None:
    missing = expected - actual
    if missing:
        raise SystemExit(f"Missing expected {name}: {sorted(missing)}")
    print(f"OK: expected {name} present ({len(expected)})")


def run_catalog_validation(cursor: psycopg.Cursor[tuple[object, ...]]) -> None:
    cursor.execute("SELECT version_num FROM alembic_version")
    current_heads = {str(row[0]) for row in cursor.fetchall()}
    if current_heads != {EXPECTED_ALEMBIC_HEAD}:
        raise SystemExit(f"Alembic head mismatch: expected {EXPECTED_ALEMBIC_HEAD}, got {sorted(current_heads)}")
    print(f"OK: Alembic current head is {EXPECTED_ALEMBIC_HEAD}")

    schemas = fetch_names(
        cursor,
        "SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg_%' AND nspname <> 'information_schema'",
    )
    assert_expected_set("schemas", schemas, EXPECTED_SCHEMAS)

    extensions = fetch_names(cursor, "SELECT extname FROM pg_extension")
    assert_expected_set("extensions", extensions, EXPECTED_EXTENSIONS)

    tables = fetch_names(
        cursor,
        """
        SELECT n.nspname || '.' || c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relkind IN ('r','p')
        """,
    )
    assert_expected_set("tables", tables, expected_database_tables())

    expected_types_sql = ", ".join(f"'{type_name}'" for type_name in sorted(expected_type_names()))
    type_names = fetch_names(cursor, f"SELECT typname FROM pg_type WHERE typname IN ({expected_types_sql})")
    assert_expected_set("enum/domain types", type_names, expected_type_names())

    cursor.execute("SELECT COUNT(*) FROM platform.plans")
    plan_count = int(cursor.fetchone()[0])
    if plan_count < 3:
        raise SystemExit(f"Expected platform seed plans to exist, found {plan_count}")
    print(f"OK: platform seed plans present ({plan_count})")


def reset_local() -> None:
    if get_settings().environment == "production":
        raise SystemExit("Refusing to reset a production environment.")
    alembic(["downgrade", "base"])
    alembic(["upgrade", "head"])
    validate()


def main() -> None:
    os.environ.setdefault("PYTHONPATH", str(REPOSITORY_ROOT / "packages" / "backend-common" / "src"))
    commands = {
        "upgrade": lambda: alembic(["upgrade", "head"]),
        "downgrade": lambda: alembic(["downgrade", sys.argv[2] if len(sys.argv) > 2 else "-1"]),
        "current": lambda: alembic(["current"]),
        "heads": lambda: alembic(["heads"]),
        "history": lambda: alembic(["history"]),
        "check": check,
        "reset-local": reset_local,
        "validate": validate,
    }
    command_name = sys.argv[1] if len(sys.argv) > 1 else "check"
    command = commands.get(command_name)
    if command is None:
        raise SystemExit(f"Unknown DB command: {command_name}")
    command()


if __name__ == "__main__":
    main()
