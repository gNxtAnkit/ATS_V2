from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from gnxthire_common.db import (
    check_database_connection,
    create_session_factory,
    session_scope,
    validate_database_url,
)
from gnxthire_common.health import HealthStatus, aggregate_health, database_health_check, redis_health_check


def test_database_url_validation_requires_postgres() -> None:
    with pytest.raises(ValueError, match="postgresql"):
        validate_database_url("sqlite+pysqlite:///:memory:")


def test_session_scope_commits_and_rolls_back() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"))
    session_factory = create_session_factory(engine)

    with session_scope(session_factory) as session:
        session.execute(text("INSERT INTO items (id, name) VALUES (1, 'committed')"))

    with pytest.raises(RuntimeError, match="force rollback"):
        with session_scope(session_factory) as session:
            session.execute(text("INSERT INTO items (id, name) VALUES (2, 'rolled back')"))
            raise RuntimeError("force rollback")

    with engine.connect() as connection:
        count = connection.execute(text("SELECT COUNT(*) FROM items")).scalar_one()

    assert count == 1


def test_health_models_and_database_check() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    database_check = database_health_check(engine)
    health = aggregate_health("unit-test", [database_check])

    assert database_check.status == HealthStatus.OK
    assert health.status == HealthStatus.OK
    check_database_connection(engine)


def test_redis_health_check_distinguishes_missing_client() -> None:
    result = redis_health_check(None)

    assert result.status == HealthStatus.DEGRADED
