from __future__ import annotations

import pytest
from sqlalchemy.orm import sessionmaker

from gnxthire_common.errors import AuthenticationError
from gnxthire_identity.config import get_identity_settings
from gnxthire_identity.email import CapturingEmailSender
from gnxthire_identity.platform_admin.repository import PlatformAdminRepository
from gnxthire_identity.platform_admin.service import PlatformAdminIdentityService
from gnxthire_identity.rate_limit import MemoryRateLimiter
from gnxthire_identity.request_metadata import RequestMetadata
from gnxthire_identity.tenant.repository import TenantIdentityRepository
from gnxthire_identity.tenant.service import TenantIdentityService

METADATA = RequestMetadata(request_id="test-request", correlation_id=None, ip_address="127.0.0.1", user_agent="pytest")


@pytest.fixture()
def tenant_service(db_engine):
    session = sessionmaker(bind=db_engine, expire_on_commit=False, future=True)()
    sender = CapturingEmailSender()
    service = TenantIdentityService(
        repository=TenantIdentityRepository(session),
        settings=get_identity_settings(),
        email_sender=sender,
        rate_limiter=MemoryRateLimiter(),
    )
    yield service, sender
    session.commit()
    session.close()


@pytest.fixture()
def platform_admin_service(db_engine):
    session = sessionmaker(bind=db_engine, expire_on_commit=False, future=True)()
    sender = CapturingEmailSender()
    service = PlatformAdminIdentityService(
        repository=PlatformAdminRepository(session),
        settings=get_identity_settings(),
        email_sender=sender,
        rate_limiter=MemoryRateLimiter(),
    )
    yield service, sender
    session.commit()
    session.close()


def test_forgot_password_sends_email_using_frontend_reset_url(tenant_service, seed_tenant, seed_tenant_user) -> None:
    service, sender = tenant_service
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")

    service.forgot_password(email=email, metadata=METADATA)

    assert len(sender.messages) == 1
    assert sender.messages[0].to_email == email
    assert str(get_identity_settings().frontend_password_reset_url) in sender.messages[0].text_body


def test_reset_password_works_once_and_revokes_sessions(tenant_service, seed_tenant, seed_tenant_user) -> None:
    service, sender = tenant_service
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")

    service.forgot_password(email=email, metadata=METADATA)
    reset_url = sender.messages[0].text_body
    raw_token = reset_url.split("token=")[1].split("&")[0].split('"')[0]

    service.reset_password(
        raw_token=raw_token, new_password="EvenStronger1!", confirm_password="EvenStronger1!", metadata=METADATA
    )

    with pytest.raises(AuthenticationError):
        service.reset_password(
            raw_token=raw_token, new_password="AnotherPass1!", confirm_password="AnotherPass1!", metadata=METADATA
        )

    login_with_new_password = service.login(email=email, password="EvenStronger1!", metadata=METADATA)
    assert login_with_new_password.status == "authenticated"


def test_reset_token_stored_hashed_only(tenant_service, seed_tenant, seed_tenant_user, db_engine) -> None:
    from sqlalchemy import text

    service, sender = tenant_service
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")

    service.forgot_password(email=email, metadata=METADATA)
    reset_url = sender.messages[0].text_body
    raw_token = reset_url.split("token=")[1].split("&")[0].split('"')[0]

    with db_engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))
        stored_values = connection.execute(
            text("SELECT token_hmac FROM tenant.password_reset_tokens WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id},
        ).scalars().all()

    assert all(raw_token not in value for value in stored_values)
    assert all(value.startswith("sha256:") for value in stored_values)


def test_platform_admin_reset_uses_platform_admin_frontend_url(
    platform_admin_service, seed_platform_admin
) -> None:
    service, sender = platform_admin_service
    email = seed_platform_admin(password="StrongPassw0rd!")

    service.forgot_password(email=email, metadata=METADATA)

    assert len(sender.messages) == 1
    assert str(get_identity_settings().frontend_platform_admin_password_reset_url) in sender.messages[0].text_body


def test_platform_admin_email_verification_uses_platform_admin_frontend_url(
    platform_admin_service, seed_platform_admin
) -> None:
    service, sender = platform_admin_service
    email = seed_platform_admin(password="StrongPassw0rd!", email_verified=False)

    service.request_email_verification(email=email, metadata=METADATA)

    assert len(sender.messages) == 1
    assert str(get_identity_settings().frontend_platform_admin_email_verify_url) in sender.messages[0].text_body


def test_platform_admin_reset_password_works_once(platform_admin_service, seed_platform_admin) -> None:
    service, sender = platform_admin_service
    email = seed_platform_admin(password="StrongPassw0rd!")

    service.forgot_password(email=email, metadata=METADATA)
    reset_url = sender.messages[0].text_body
    raw_token = reset_url.split("token=")[1].split("&")[0].split('"')[0]

    service.reset_password(
        raw_token=raw_token, new_password="EvenStronger1!", confirm_password="EvenStronger1!", metadata=METADATA
    )

    with pytest.raises(AuthenticationError):
        service.reset_password(
            raw_token=raw_token, new_password="AnotherPass1!", confirm_password="AnotherPass1!", metadata=METADATA
        )
