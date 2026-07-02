from __future__ import annotations

from sqlalchemy import text


def test_login_accepts_only_email_and_password(app_client, seed_tenant, seed_tenant_user) -> None:
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")

    response = app_client.post(
        "/v1/identity/auth/login", json={"email": email, "password": "StrongPassw0rd!"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "authenticated"
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]


def test_login_rejects_stray_tenant_field(app_client, seed_tenant, seed_tenant_user) -> None:
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")

    response = app_client.post(
        "/v1/identity/auth/login",
        json={"email": email, "password": "StrongPassw0rd!", "tenant": "whatever"},
    )

    assert response.status_code == 422


def test_login_with_unknown_email_returns_generic_error(app_client) -> None:
    response = app_client.post(
        "/v1/identity/auth/login", json={"email": "no-such-user@identity-test.example", "password": "x"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid credentials"


def test_login_with_wrong_password_returns_generic_error_and_writes_event(
    app_client, seed_tenant, seed_tenant_user, db_engine
) -> None:
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")

    response = app_client.post("/v1/identity/auth/login", json={"email": email, "password": "WrongPassword!"})

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid credentials"
    with db_engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))
        count = connection.execute(
            text(
                "SELECT count(*) FROM tenant.security_events WHERE tenant_id = :tenant_id AND event_type = 'login_failed'"
            ),
            {"tenant_id": tenant_id},
        ).scalar_one()
    assert count >= 1


def test_duplicate_active_email_across_tenants_fails_safely_and_writes_event(
    app_client, seed_tenant, seed_tenant_user, db_engine
) -> None:
    shared_email = "duplicate-user@identity-test.example"
    tenant_one = seed_tenant()
    tenant_two = seed_tenant()
    seed_tenant_user(tenant_id=tenant_one, email=shared_email, password="StrongPassw0rd!")
    seed_tenant_user(tenant_id=tenant_two, email=shared_email, password="StrongPassw0rd!")

    response = app_client.post(
        "/v1/identity/auth/login", json={"email": shared_email, "password": "StrongPassw0rd!"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid credentials"
    with db_engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.is_platform_admin', 'true', true)"))
        row = connection.execute(
            text(
                """
                SELECT after_state FROM platform.audit_logs
                WHERE action_key = 'identity.duplicate_active_email_conflict'
                ORDER BY occurred_at DESC LIMIT 1
                """
            )
        ).mappings().one()
    assert row["after_state"]["email"] == shared_email
    assert str(tenant_one) in row["after_state"]["tenant_ids"]
    assert str(tenant_two) in row["after_state"]["tenant_ids"]


def test_successful_login_sets_tenant_context(app_client, seed_tenant, seed_tenant_user) -> None:
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")

    login_response = app_client.post(
        "/v1/identity/auth/login", json={"email": email, "password": "StrongPassw0rd!"}
    )
    access_token = login_response.json()["tokens"]["access_token"]

    me_response = app_client.get("/v1/identity/auth/me", headers={"Authorization": f"Bearer {access_token}"})

    assert me_response.status_code == 200
    body = me_response.json()
    assert body["tenant_id"] == str(tenant_id)
    assert body["actor_type"] == "tenant_user"
    assert body["email"] == email


def test_logout_revokes_session(app_client, seed_tenant, seed_tenant_user) -> None:
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")
    tokens = app_client.post(
        "/v1/identity/auth/login", json={"email": email, "password": "StrongPassw0rd!"}
    ).json()["tokens"]

    logout_response = app_client.post("/v1/identity/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert logout_response.status_code == 200

    refresh_response = app_client.post("/v1/identity/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_response.status_code == 401


def test_refresh_rotates_token_and_old_token_is_invalid(app_client, seed_tenant, seed_tenant_user) -> None:
    tenant_id = seed_tenant()
    email = seed_tenant_user(tenant_id=tenant_id, password="StrongPassw0rd!")
    tokens = app_client.post(
        "/v1/identity/auth/login", json={"email": email, "password": "StrongPassw0rd!"}
    ).json()["tokens"]

    refreshed = app_client.post("/v1/identity/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    reused_old = app_client.post("/v1/identity/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reused_old.status_code == 401

    works_with_new = app_client.post("/v1/identity/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]})
    assert works_with_new.status_code == 200


def test_platform_admin_token_rejected_by_tenant_me(app_client, seed_platform_admin) -> None:
    email = seed_platform_admin(password="StrongPassw0rd!")
    tokens = app_client.post(
        "/v1/identity/platform-admin/auth/login", json={"email": email, "password": "StrongPassw0rd!"}
    ).json()["tokens"]

    response = app_client.get("/v1/identity/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})

    assert response.status_code == 401
