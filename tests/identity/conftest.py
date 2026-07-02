from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

os.environ.setdefault("IDENTITY_RATE_LIMIT_BACKEND", "memory")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from gnxthire_common.db import create_sync_engine
from gnxthire_testing.database import database_tests_enabled

pytestmark = pytest.mark.skipif(
    not database_tests_enabled(),
    reason="Set GNXTHIRE_RUN_DB_TESTS=1 and DATABASE_URL to run identity DB-backed tests.",
)


def unique_suffix() -> str:
    return uuid.uuid4().hex[:12]


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    return create_sync_engine()


@pytest.fixture()
def app_client() -> Iterator[TestClient]:
    from gnxthire_identity.main import create_app

    with TestClient(create_app(), client=("127.0.0.1", 51999)) as client:
        yield client


@pytest.fixture()
def seed_tenant(db_engine: Engine):
    def _seed(*, status: str = "active") -> uuid.UUID:
        suffix = unique_suffix()
        with db_engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))
            tenant_id = connection.execute(
                text(
                    """
                    INSERT INTO platform.tenants (name, tenant_type, primary_admin_email, status, activated_at)
                    VALUES (
                      :name, 'corporate', :email, CAST(:status AS tenant_status_enum),
                      CASE WHEN CAST(:status AS text) = 'active' THEN now() ELSE NULL END
                    )
                    RETURNING id
                    """
                ),
                {
                    "name": f"Identity Test Tenant {suffix}",
                    "email": f"owner-{suffix}@identity-test.example",
                    "status": status,
                },
            ).scalar_one()
        return tenant_id

    return _seed


@pytest.fixture()
def seed_tenant_user(db_engine: Engine):
    from gnxthire_identity.security import hash_password

    def _seed(
        *,
        tenant_id: uuid.UUID,
        email: str | None = None,
        password: str = "SmokeTestPass123!",
        status: str = "active",
        email_verified: bool = True,
    ) -> str:
        email = email or f"user-{unique_suffix()}@identity-test.example"
        with db_engine.begin() as connection:
            connection.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))
            connection.execute(
                text(
                    """
                    INSERT INTO tenant.users (
                      tenant_id, email, display_name, status, password_hash, email_verified_at
                    )
                    VALUES (
                      :tenant_id, :email, 'Identity Test User', :status, :password_hash,
                      CASE WHEN :email_verified THEN now() ELSE NULL END
                    )
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "email": email,
                    "status": status,
                    "password_hash": hash_password(password),
                    "email_verified": email_verified,
                },
            )
        return email

    return _seed


@pytest.fixture()
def seed_platform_admin(db_engine: Engine):
    from gnxthire_identity.security import hash_password

    def _seed(*, password: str = "SmokeTestPass123!", status: str = "active", email_verified: bool = True) -> str:
        email = f"admin-{unique_suffix()}@identity-test.example"
        with db_engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO platform.platform_users (email, display_name, status, password_hash, email_verified_at)
                    VALUES (
                        :email,
                        'Identity Test Admin',
                        :status,
                        :password_hash,
                        CASE WHEN :email_verified THEN now() ELSE NULL END
                    )
                    """
                ),
                {
                    "email": email,
                    "status": status,
                    "password_hash": hash_password(password),
                    "email_verified": email_verified,
                },
            )
        return email

    return _seed
