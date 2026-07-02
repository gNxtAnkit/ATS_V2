from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from gnxthire_common.config import Settings, get_settings
from gnxthire_common.errors import AppError, DatabaseAppError


def validate_database_url(database_url: str) -> str:
    url = make_url(database_url)
    if url.drivername not in {"postgresql+psycopg", "postgresql"}:
        raise ValueError("database_url must use the postgresql+psycopg driver")
    if not url.database:
        raise ValueError("database_url must include a database name")
    if not url.username:
        raise ValueError("database_url must include a database user")
    return database_url


def create_engine_from_url(database_url: str, *, echo: bool = False) -> Engine:
    validate_database_url(database_url)
    return create_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
        future=True,
    )


def create_sync_engine(settings: Settings | None = None) -> Engine:
    resolved_settings = settings or get_settings()
    return create_engine_from_url(
        str(resolved_settings.database_url),
        echo=resolved_settings.database_echo,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, future=True)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Commits on success and on a handled `AppError` (auth/validation/rate-limit/etc.
    failures deliberately raised after writes such as security/audit events, which must
    persist even though the request itself ends in an error response). Rolls back only
    on unexpected exceptions, where the transaction state cannot be trusted."""
    session = session_factory()
    try:
        yield session
    except AppError:
        session.commit()
        raise
    except Exception:
        session.rollback()
        raise
    else:
        session.commit()
    finally:
        session.close()


@contextmanager
def transaction(session: Session) -> Iterator[Session]:
    with session.begin():
        yield session


def execute_scalar(session: Session, statement: Any) -> Any:
    return session.execute(statement).scalar_one()


def session_dependency(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_scope(session_factory) as session:
        yield session


def check_database_connection(engine: Engine) -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise DatabaseAppError("database health check failed", safe_detail="Database is unavailable") from exc
