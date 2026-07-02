from __future__ import annotations

import ssl
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, unquote, urlparse

import pytest

from gnxthire_common.errors import AuthenticationError, RateLimitError, ValidationFailure
from gnxthire_identity.config import IdentitySettings
from gnxthire_identity.email import (
    CapturingEmailSender,
    EmailDeliveryError,
    IdentityEmail,
    SmtpEmailSender,
    build_email_verification_url,
    build_password_reset_url,
    password_reset_email,
)
from gnxthire_identity.rate_limit import MemoryRateLimiter, RateLimitRule
from gnxthire_identity.security import (
    SignedTokenClaims,
    build_totp_uri,
    create_signed_token,
    decrypt_secret,
    encrypt_secret,
    generate_totp_secret,
    hash_password,
    token_hmac,
    validate_password_policy,
    verify_password,
    verify_signed_token,
    verify_totp_code,
)


def test_password_hash_verifies_without_storing_raw_password() -> None:
    password_hash = hash_password("Sufficiently$trong123")

    assert "Sufficiently" not in password_hash
    assert verify_password("Sufficiently$trong123", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_password_policy_rejects_weak_password() -> None:
    settings = IdentitySettings()

    with pytest.raises(ValidationFailure):
        validate_password_policy("short", "user@example.com", settings)


def test_signed_token_rejects_tampering_and_wrong_audience() -> None:
    settings = IdentitySettings()
    token = create_signed_token(
        SignedTokenClaims(
            subject="actor-1",
            actor_type="tenant_user",
            token_type="access",
            audience=settings.tenant_audience,
            issuer=settings.token_issuer,
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
            tenant_id="tenant-1",
        ),
        settings.access_token_secret.get_secret_value(),
    )

    payload = verify_signed_token(
        token,
        secret=settings.access_token_secret.get_secret_value(),
        issuer=settings.token_issuer,
        audience=settings.tenant_audience,
        token_type="access",
    )

    assert payload["sub"] == "actor-1"
    with pytest.raises(AuthenticationError):
        verify_signed_token(
            f"{token}tampered",
            secret=settings.access_token_secret.get_secret_value(),
            issuer=settings.token_issuer,
            audience=settings.tenant_audience,
            token_type="access",
        )
    with pytest.raises(AuthenticationError):
        verify_signed_token(
            token,
            secret=settings.access_token_secret.get_secret_value(),
            issuer=settings.token_issuer,
            audience=settings.platform_admin_audience,
            token_type="access",
        )


def test_opaque_token_hmac_does_not_reveal_token() -> None:
    raw_token = "raw-token-value"
    digest = token_hmac(raw_token, "secret")

    assert raw_token not in digest
    assert digest.startswith("sha256:")


def test_totp_secret_encrypt_round_trip_and_uri() -> None:
    settings = IdentitySettings()
    secret = generate_totp_secret()
    encrypted = encrypt_secret(secret, settings.mfa_secret_encryption_key.get_secret_value())
    uri = build_totp_uri(
        issuer=settings.mfa_totp_issuer,
        account_name="user@example.com",
        secret=secret,
        digits=settings.mfa_totp_digits,
        interval=settings.mfa_totp_interval_seconds,
    )

    assert decrypt_secret(encrypted, settings.mfa_secret_encryption_key.get_secret_value()) == secret
    assert "otpauth://totp/" in uri
    assert secret in uri
    parsed_uri = urlparse(uri)
    query_params = parse_qs(parsed_uri.query)
    assert parsed_uri.scheme == "otpauth"
    assert parsed_uri.netloc == "totp"
    assert unquote(parsed_uri.path.lstrip("/")) == f"{settings.mfa_totp_issuer}:user@example.com"
    assert query_params == {
        "secret": [secret],
        "issuer": [settings.mfa_totp_issuer],
        "algorithm": ["SHA1"],
        "digits": [str(settings.mfa_totp_digits)],
        "period": [str(settings.mfa_totp_interval_seconds)],
    }
    assert not verify_totp_code(
        secret=secret,
        code="000000",
        digits=settings.mfa_totp_digits,
        interval=settings.mfa_totp_interval_seconds,
        valid_window=0,
    )


def test_email_urls_contain_raw_token_only_in_message_body() -> None:
    settings = IdentitySettings()
    url = build_password_reset_url(settings, token="raw-reset-token", tenant="tenant-1")
    verify_url = build_email_verification_url(settings, token="raw-verify-token", tenant="tenant-1")
    sender = CapturingEmailSender()

    sender.send(password_reset_email("user@example.com", reset_url=url))

    assert "raw-reset-token" in sender.messages[0].text_body
    assert "raw-verify-token" in verify_url


def test_memory_rate_limiter_blocks_after_limit() -> None:
    limiter = MemoryRateLimiter()
    rule = RateLimitRule("test", max_attempts=1, window_seconds=60)

    limiter.hit("actor", rule)

    with pytest.raises(RateLimitError):
        limiter.hit("actor", rule)


def test_production_identity_settings_reject_local_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(ValueError, match="production identity secrets"):
        IdentitySettings()


def test_identity_settings_reject_conflicting_smtp_security_modes() -> None:
    with pytest.raises(ValueError, match="SMTP_USE_TLS and SMTP_USE_SSL"):
        IdentitySettings(SMTP_USE_TLS=True, SMTP_USE_SSL=True)


def test_smtp_ssl_handshake_failure_returns_controlled_error(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = IdentitySettings(SMTP_USE_SSL=True, SMTP_USE_TLS=False)

    def raise_ssl_error(*_args: object, **_kwargs: object) -> None:
        raise ssl.SSLError("wrong version number")

    monkeypatch.setattr("gnxthire_identity.email.smtplib.SMTP_SSL", raise_ssl_error)

    with pytest.raises(EmailDeliveryError):
        SmtpEmailSender(settings).send(
            IdentityEmail(
                to_email="user@example.com",
                subject="Test",
                text_body="Test",
                html_body="<p>Test</p>",
            )
        )
