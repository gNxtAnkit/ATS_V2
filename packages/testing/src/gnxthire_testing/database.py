from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def database_tests_enabled() -> bool:
    return os.environ.get("GNXTHIRE_RUN_DB_TESTS") == "1"


def test_database_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("GNXTHIRE_TEST_DATABASE_URL")


def create_sqlite_test_engine() -> Engine:
    return create_engine("sqlite+pysqlite:///:memory:", future=True)


def create_test_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, future=True)


@contextmanager
def test_session_scope(engine: Engine) -> Iterator[Session]:
    session_factory = create_test_session_factory(engine)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
