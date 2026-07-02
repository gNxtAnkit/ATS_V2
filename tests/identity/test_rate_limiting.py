from __future__ import annotations

import uuid


def test_tenant_login_rate_limit_blocks_after_max_attempts(app_client) -> None:
    email = f"rate-limit-{uuid.uuid4().hex[:12]}@identity-test.example"

    statuses = [
        app_client.post("/v1/identity/auth/login", json={"email": email, "password": "whatever"}).status_code
        for _ in range(6)
    ]

    assert statuses[:5] == [401, 401, 401, 401, 401]
    assert statuses[5] == 429


def test_platform_admin_login_rate_limit_blocks_after_max_attempts(app_client) -> None:
    email = f"rate-limit-{uuid.uuid4().hex[:12]}@identity-test.example"

    statuses = [
        app_client.post(
            "/v1/identity/platform-admin/auth/login", json={"email": email, "password": "whatever"}
        ).status_code
        for _ in range(6)
    ]

    assert statuses[:5] == [401, 401, 401, 401, 401]
    assert statuses[5] == 429
