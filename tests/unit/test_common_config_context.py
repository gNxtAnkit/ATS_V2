from uuid import uuid4

import pytest

from gnxthire_common.config import Settings
from gnxthire_common.context import ActorType, RequestContext


def test_settings_accept_phase1_environment_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GNXTHIRE_ENV", "test")
    monkeypatch.setenv("GNXTHIRE_SERVICE_NAME", "identity")

    settings = Settings()

    assert settings.environment == "test"
    assert settings.service_name == "identity"


def test_tenant_request_context_requires_tenant_id() -> None:
    with pytest.raises(ValueError, match="tenant-facing context requires tenant_id"):
        RequestContext(request_id="req_1", actor_type=ActorType.TENANT_USER)


def test_platform_admin_context_requires_platform_actor() -> None:
    with pytest.raises(ValueError, match="platform-admin context requires actor_type"):
        RequestContext(
            request_id="req_1",
            tenant_id=uuid4(),
            actor_id=uuid4(),
            actor_type=ActorType.TENANT_USER,
            is_platform_admin=True,
            platform_admin_id=uuid4(),
        )


def test_platform_admin_context_requires_platform_admin_id() -> None:
    with pytest.raises(ValueError, match="platform-admin context requires platform_admin_id"):
        RequestContext(
            request_id="req_1",
            actor_id=uuid4(),
            actor_type=ActorType.PLATFORM_USER,
            is_platform_admin=True,
        )


def test_valid_tenant_context_exposes_correlation_id() -> None:
    context = RequestContext(
        request_id="req_1",
        tenant_id=uuid4(),
        actor_id=uuid4(),
        actor_type=ActorType.TENANT_USER,
    )

    assert context.effective_correlation_id == "req_1"


def test_production_settings_require_explicit_external_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GNXTHIRE_ENV", "production")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GNXTHIRE_DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("GNXTHIRE_REDIS_URL", raising=False)

    with pytest.raises(ValueError, match="production settings require explicit environment values"):
        Settings()
