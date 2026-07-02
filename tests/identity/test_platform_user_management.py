from __future__ import annotations

import uuid

from sqlalchemy import text


def _login(app_client, email: str, password: str) -> str:
    response = app_client.post("/v1/identity/platform-admin/auth/login", json={"email": email, "password": password})
    return response.json()["tokens"]["access_token"]


def test_management_routes_require_authenticated_platform_admin(app_client) -> None:
    response = app_client.get("/v1/identity/platform-users")
    assert response.status_code == 401


def test_tenant_token_cannot_access_platform_user_management(app_client, seed_tenant, seed_tenant_user) -> None:
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")
    tenant_token = app_client.post(
        "/v1/identity/auth/login", json={"email": email, "password": "StrongPassw0rd!"}
    ).json()["tokens"]["access_token"]

    response = app_client.get(
        "/v1/identity/platform-users", headers={"Authorization": f"Bearer {tenant_token}"}
    )

    assert response.status_code == 401


def test_authenticated_admin_can_manage_another_platform_user(
    app_client, seed_platform_admin, db_engine
) -> None:
    actor_email = seed_platform_admin(password="StrongPassw0rd!")
    access_token = _login(app_client, actor_email, "StrongPassw0rd!")
    headers = {"Authorization": f"Bearer {access_token}"}

    create_response = app_client.post(
        "/v1/identity/platform-users",
        json={"email": f"managed-{uuid.uuid4().hex[:10]}@identity-test.example", "display_name": "Managed Admin"},
        headers=headers,
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "invited"
    target_id = created["id"]

    activate_response = app_client.post(f"/v1/identity/platform-users/{target_id}/activate", headers=headers)
    assert activate_response.status_code == 200
    assert activate_response.json()["status"] == "active"

    lock_response = app_client.post(f"/v1/identity/platform-users/{target_id}/lock", headers=headers)
    assert lock_response.status_code == 200
    assert lock_response.json()["status"] == "locked"

    unlock_response = app_client.post(f"/v1/identity/platform-users/{target_id}/unlock", headers=headers)
    assert unlock_response.status_code == 200
    assert unlock_response.json()["status"] == "active"

    deactivate_response = app_client.post(f"/v1/identity/platform-users/{target_id}/deactivate", headers=headers)
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["status"] == "suspended"

    require_mfa_response = app_client.post(f"/v1/identity/platform-users/{target_id}/require-mfa", headers=headers)
    assert require_mfa_response.status_code == 200
    assert require_mfa_response.json()["mfa_required"] is True

    require_reset_response = app_client.post(
        f"/v1/identity/platform-users/{target_id}/require-password-reset", headers=headers
    )
    assert require_reset_response.status_code == 200

    get_response = app_client.get(f"/v1/identity/platform-users/{target_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["email"] == created["email"]

    with db_engine.begin() as connection:
        audit_count = connection.execute(
            text(
                "SELECT count(*) FROM platform.audit_logs WHERE object_id = :id AND actor_type = 'platform_user'"
            ),
            {"id": target_id},
        ).scalar_one()
    assert audit_count >= 5


def test_get_unknown_platform_user_returns_404(app_client, seed_platform_admin) -> None:
    actor_email = seed_platform_admin(password="StrongPassw0rd!")
    access_token = _login(app_client, actor_email, "StrongPassw0rd!")

    response = app_client.get(
        f"/v1/identity/platform-users/{uuid.uuid4()}", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 404
