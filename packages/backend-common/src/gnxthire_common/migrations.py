from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


BASELINE_SCHEMA_FILES = tuple(f"{number:02d}_{name}.sql" for number, name in [
    (0, "extensions_schemas_types"),
    (1, "platform_admin"),
    (2, "tenant_identity_rbac_config"),
    (3, "candidate_domain"),
    (4, "corporate_ats"),
    (5, "agency_ats"),
    (6, "workflow_engine"),
    (7, "ai_recruiter_interview_telephony"),
    (8, "integrations_events_notifications"),
    (9, "billing_usage_revenue"),
    (10, "reporting_analytics_compliance"),
    (11, "rls_policies"),
    (12, "indexes_triggers_views"),
    (13, "seed_data"),
])
VALIDATION_FILE = "14_validation_queries.sql"


@dataclass(frozen=True)
class SchemaFileCheck:
    file_name: str
    exists: bool


def required_schema_files(schema_directory: Path) -> list[SchemaFileCheck]:
    return [
        SchemaFileCheck(file_name=file_name, exists=(schema_directory / file_name).exists())
        for file_name in [*BASELINE_SCHEMA_FILES, VALIDATION_FILE]
    ]


def assert_required_schema_files(schema_directory: Path) -> None:
    missing = [check.file_name for check in required_schema_files(schema_directory) if not check.exists]
    if missing:
        raise FileNotFoundError(f"Missing required schema files: {', '.join(missing)}")
