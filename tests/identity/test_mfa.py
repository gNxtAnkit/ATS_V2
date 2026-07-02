from __future__ import annotations

import time

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from gnxthire_common.errors import AuthenticationError, ConflictError
from gnxthire_identity.config import get_identity_settings
from gnxthire_identity.email import CapturingEmailSender
from gnxthire_identity.rate_limit import MemoryRateLimiter
from gnxthire_identity.request_metadata import RequestMetadata
from gnxthire_identity.security import _totp_at_counter
from gnxthire_identity.tenant.repository import TenantIdentityRepository
from gnxthire_identity.tenant.service import TenantIdentityService

METADATA = RequestMetadata(request_id="test-request", correlation_id=None, ip_address="127.0.0.1", user_agent="pytest")


def _current_totp_code(secret: str) -> str:
    settings = get_identity_settings()
    counter = int(time.time()) // settings.mfa_totp_interval_seconds
    return _totp_at_counter(secret, counter, settings.mfa_totp_digits)


@pytest.fixture()
def tenant_service_and_session(db_engine):
    session = sessionmaker(bind=db_engine, expire_on_commit=False, future=True)()
    sender = CapturingEmailSender()
    service = TenantIdentityService(
        repository=TenantIdentityRepository(session),
        settings=get_identity_settings(),
        email_sender=sender,
        rate_limiter=MemoryRateLimiter(),
    )
    yield service, session
    session.commit()
    session.close()


def _get_user(session, tenant_id, email):
    repository = TenantIdentityRepository(session)
    return repository.get_tenant_user_by_email(tenant_id, email)


def test_totp_setup_returns_provisioning_uri_but_does_not_enable_mfa(
    tenant_service_and_session, seed_tenant, seed_tenant_user
) -> None:
    service, session = tenant_service_and_session
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")
    session.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))
    user = _get_user(session, tenant_id, email)

    uri, secret = service.setup_totp(user=user, metadata=METADATA)

    assert uri.startswith("otpauth://totp/")
    assert secret in uri
    login = service.login(email=email, password="StrongPassw0rd!", metadata=METADATA)
    assert login.status == "authenticated"  # MFA not required until confirmed


def test_totp_confirm_enables_mfa_and_login_then_requires_challenge(
    tenant_service_and_session, seed_tenant, seed_tenant_user
) -> None:
    service, session = tenant_service_and_session
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")
    session.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))
    user = _get_user(session, tenant_id, email)
    _uri, secret = service.setup_totp(user=user, metadata=METADATA)

    with pytest.raises(AuthenticationError):
        service.confirm_totp(user=user, code="000000", metadata=METADATA)

    recovery_codes = service.confirm_totp(user=user, code=_current_totp_code(secret), metadata=METADATA)
    assert len(recovery_codes) == get_identity_settings().mfa_recovery_code_count

    login = service.login(email=email, password="StrongPassw0rd!", metadata=METADATA)
    assert login.status == "mfa_required"
    assert login.mfa_challenge_token

    completed = service.verify_mfa_challenge(
        challenge_token=login.mfa_challenge_token, code=_current_totp_code(secret), metadata=METADATA
    )
    assert completed.status == "authenticated"
    assert completed.tokens.access_token


def test_recovery_code_is_single_use(tenant_service_and_session, seed_tenant, seed_tenant_user) -> None:
    service, session = tenant_service_and_session
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")
    session.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))
    user = _get_user(session, tenant_id, email)
    _uri, secret = service.setup_totp(user=user, metadata=METADATA)
    recovery_codes = service.confirm_totp(user=user, code=_current_totp_code(secret), metadata=METADATA)

    login = service.login(email=email, password="StrongPassw0rd!", metadata=METADATA)
    first_use = service.verify_mfa_challenge(
        challenge_token=login.mfa_challenge_token, code=recovery_codes[0], metadata=METADATA
    )
    assert first_use.status == "authenticated"

    login_again = service.login(email=email, password="StrongPassw0rd!", metadata=METADATA)
    with pytest.raises(AuthenticationError):
        service.verify_mfa_challenge(
            challenge_token=login_again.mfa_challenge_token, code=recovery_codes[0], metadata=METADATA
        )


def test_recovery_code_verify_route_is_single_use(app_client, seed_tenant, seed_tenant_user, db_engine) -> None:
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")
    service_session = sessionmaker(bind=db_engine, expire_on_commit=False, future=True)()
    service = TenantIdentityService(
        repository=TenantIdentityRepository(service_session),
        settings=get_identity_settings(),
        email_sender=CapturingEmailSender(),
        rate_limiter=MemoryRateLimiter(),
    )
    service_session.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))
    user = _get_user(service_session, tenant_id, email)
    _uri, secret = service.setup_totp(user=user, metadata=METADATA)
    recovery_codes = service.confirm_totp(user=user, code=_current_totp_code(secret), metadata=METADATA)
    service_session.commit()
    service_session.close()

    login = app_client.post("/v1/identity/auth/login", json={"email": email, "password": "StrongPassw0rd!"})
    assert login.status_code == 200
    challenge_token = login.json()["mfa_challenge_token"]

    first_use = app_client.post(
        "/v1/identity/mfa/recovery-code/verify",
        json={"mfa_challenge_token": challenge_token, "recovery_code": recovery_codes[0]},
    )
    assert first_use.status_code == 200
    assert first_use.json()["status"] == "authenticated"

    login_again = app_client.post("/v1/identity/auth/login", json={"email": email, "password": "StrongPassw0rd!"})
    second_use = app_client.post(
        "/v1/identity/mfa/recovery-code/verify",
        json={"mfa_challenge_token": login_again.json()["mfa_challenge_token"], "recovery_code": recovery_codes[0]},
    )
    assert second_use.status_code == 401


def test_password_policy_route_returns_configured_policy(app_client) -> None:
    response = app_client.get("/v1/identity/auth/password-policy")

    assert response.status_code == 200
    body = response.json()
    assert body["min_length"] == get_identity_settings().password_min_length
    assert body["require_uppercase"] is get_identity_settings().password_require_uppercase


def test_disable_mfa_requires_password(tenant_service_and_session, seed_tenant, seed_tenant_user) -> None:
    service, session = tenant_service_and_session
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")
    session.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))
    user = _get_user(session, tenant_id, email)
    _uri, secret = service.setup_totp(user=user, metadata=METADATA)
    service.confirm_totp(user=user, code=_current_totp_code(secret), metadata=METADATA)

    with pytest.raises(AuthenticationError):
        service.disable_mfa(user=user, password="WrongPassword!", metadata=METADATA)

    result = service.disable_mfa(user=user, password="StrongPassw0rd!", metadata=METADATA)
    assert result.message == "MFA disabled"

    login = service.login(email=email, password="StrongPassw0rd!", metadata=METADATA)
    assert login.status == "authenticated"


def test_confirm_without_pending_setup_raises_conflict(
    tenant_service_and_session, seed_tenant, seed_tenant_user
) -> None:
    service, session = tenant_service_and_session
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")
    session.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))
    user = _get_user(session, tenant_id, email)

    with pytest.raises(ConflictError):
        service.confirm_totp(user=user, code="123456", metadata=METADATA)
