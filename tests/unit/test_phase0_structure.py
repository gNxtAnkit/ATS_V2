from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_required_phase0_paths_exist() -> None:
    required_paths = [
        "apps/api-gateway",
        "apps/web-tenant",
        "apps/web-platform-admin",
        "apps/web-client-portal",
        "apps/web-candidate",
        "packages/backend-common",
        "packages/frontend-common",
        "packages/contracts",
        "packages/testing",
        "db/schema",
        "db/migrations",
        "db/seeds",
        "db/validation",
        "docs/architecture/service-boundaries.md",
        "docs/engineering/local-development.md",
        "alembic.ini",
        "db/migrations/env.py",
    ]

    missing_paths = [path for path in required_paths if not (REPOSITORY_ROOT / path).exists()]

    assert missing_paths == []


def test_service_boundaries_are_documented() -> None:
    services_root = REPOSITORY_ROOT / "services"
    service_directories = [path for path in services_root.iterdir() if path.is_dir()]

    assert service_directories
    assert all((service_directory / "SERVICE_BOUNDARY.md").exists() for service_directory in service_directories)
