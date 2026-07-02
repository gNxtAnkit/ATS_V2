from __future__ import annotations

import base64
import json

import pytest


def _decode_payload(token: str) -> dict:
    _header, payload_segment, _signature = token.split(".", 2)
    padded = payload_segment + "=" * ((4 - len(payload_segment) % 4) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def test_platform_admin_login_with_email_and_password_only(app_client, seed_platform_admin) -> None:
    email = seed_platform_admin(password="StrongPassw0rd!")

    response = app_client.post(
        "/v1/identity/platform-admin/auth/login", json={"email": email, "password": "StrongPassw0rd!"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "authenticated"
    assert body["tokens"]["access_token"]


def test_platform_admin_token_has_no_tenant_id_claim(app_client, seed_platform_admin) -> None:
    email = seed_platform_admin(password="StrongPassw0rd!")
    tokens = app_client.post(
        "/v1/identity/platform-admin/auth/login", json={"email": email, "password": "StrongPassw0rd!"}
    ).json()["tokens"]

    payload = _decode_payload(tokens["access_token"])

    assert "tid" not in payload
    assert payload["actor_type"] == "platform_user"
    assert payload["aud"] == "gnxthire-platform-admin"


def test_tenant_user_cannot_login_via_platform_admin_route(app_client, seed_tenant, seed_tenant_user) -> None:
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")

    response = app_client.post(
        "/v1/identity/platform-admin/auth/login", json={"email": email, "password": "StrongPassw0rd!"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid credentials"


def test_platform_admin_cannot_login_via_tenant_route(app_client, seed_platform_admin) -> None:
    email = seed_platform_admin(password="StrongPassw0rd!")

    response = app_client.post("/v1/identity/auth/login", json={"email": email, "password": "StrongPassw0rd!"})

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid credentials"


def test_platform_admin_routes_reject_tenant_token(app_client, seed_tenant, seed_tenant_user) -> None:
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")
    tokens = app_client.post(
        "/v1/identity/auth/login", json={"email": email, "password": "StrongPassw0rd!"}
    ).json()["tokens"]

    response = app_client.get(
        "/v1/identity/platform-admin/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )

    assert response.status_code == 401


def test_platform_admin_me_returns_no_tenant_context(app_client, seed_platform_admin) -> None:
    email = seed_platform_admin(password="StrongPassw0rd!")
    tokens = app_client.post(
        "/v1/identity/platform-admin/auth/login", json={"email": email, "password": "StrongPassw0rd!"}
    ).json()["tokens"]

    response = app_client.get(
        "/v1/identity/platform-admin/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] is None
    assert body["actor_type"] == "platform_admin"


def test_platform_admin_wrong_password_locks_after_threshold(db_engine, seed_platform_admin) -> None:
    # Exercised at the service layer with a permissive rate limiter so the DB-level
    # lockout (a distinct control from HTTP rate limiting) can be verified in isolation;
    # both defaulting to the same threshold would otherwise make them indistinguishable
    # over HTTP.
    from sqlalchemy.orm import sessionmaker

    from gnxthire_common.errors import AuthenticationError
    from gnxthire_identity.config import get_identity_settings
    from gnxthire_identity.email import CapturingEmailSender
    from gnxthire_identity.platform_admin.repository import PlatformAdminRepository
    from gnxthire_identity.platform_admin.service import PlatformAdminIdentityService
    from gnxthire_identity.rate_limit import RateLimitRule
    from gnxthire_identity.request_metadata import RequestMetadata

    class _PermissiveRateLimiter:
        def hit(self, key: str, rule: RateLimitRule) -> None:
            return None

    metadata = RequestMetadata(request_id="req", correlation_id=None, ip_address="127.0.0.1", user_agent="pytest")
    session = sessionmaker(bind=db_engine, expire_on_commit=False, future=True)()
    service = PlatformAdminIdentityService(
        repository=PlatformAdminRepository(session),
        settings=get_identity_settings(),
        email_sender=CapturingEmailSender(),
        rate_limiter=_PermissiveRateLimiter(),
    )
    email = seed_platform_admin(password="StrongPassw0rd!")

    for _ in range(get_identity_settings().platform_admin_login_lockout_max_failed_attempts):
        with pytest.raises(AuthenticationError):
            service.login(email=email, password="WrongPassword!", metadata=metadata)

    with pytest.raises(AuthenticationError):
        service.login(email=email, password="StrongPassw0rd!", metadata=metadata)

    session.commit()
    session.close()
