from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


UnsafeLocalSecret = Literal[
    "change-me-local-access-secret",
    "change-me-local-refresh-secret",
    "change-me-local-mfa-secret",
    "change-me-local-email-token-secret",
    "change-me-local-reset-token-secret",
    "change-me-local-mfa-encryption-key",
]


class IdentitySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="local", validation_alias="APP_ENV")
    app_base_url: HttpUrl = Field(default="http://localhost:8000", validation_alias="APP_BASE_URL")
    tenant_app_base_url: HttpUrl = Field(
        default="http://localhost:5173", validation_alias="TENANT_APP_BASE_URL"
    )
    platform_admin_app_base_url: HttpUrl = Field(
        default="http://localhost:5174", validation_alias="PLATFORM_ADMIN_APP_BASE_URL"
    )

    access_token_secret: SecretStr = Field(
        default=SecretStr("change-me-local-access-secret"),
        validation_alias="IDENTITY_ACCESS_TOKEN_SECRET",
    )
    refresh_token_secret: SecretStr = Field(
        default=SecretStr("change-me-local-refresh-secret"),
        validation_alias="IDENTITY_REFRESH_TOKEN_SECRET",
    )
    mfa_challenge_secret: SecretStr = Field(
        default=SecretStr("change-me-local-mfa-secret"),
        validation_alias="IDENTITY_MFA_CHALLENGE_SECRET",
    )
    email_token_secret: SecretStr = Field(
        default=SecretStr("change-me-local-email-token-secret"),
        validation_alias="IDENTITY_EMAIL_TOKEN_SECRET",
    )
    password_reset_token_secret: SecretStr = Field(
        default=SecretStr("change-me-local-reset-token-secret"),
        validation_alias="IDENTITY_PASSWORD_RESET_TOKEN_SECRET",
    )
    mfa_secret_encryption_key: SecretStr = Field(
        default=SecretStr("change-me-local-mfa-encryption-key"),
        validation_alias="IDENTITY_MFA_SECRET_ENCRYPTION_KEY",
    )

    token_issuer: str = Field(default="gnxthire-identity", validation_alias="IDENTITY_TOKEN_ISSUER")
    tenant_audience: str = Field(
        default="gnxthire-tenant-app", validation_alias="IDENTITY_TENANT_AUDIENCE"
    )
    platform_admin_audience: str = Field(
        default="gnxthire-platform-admin", validation_alias="IDENTITY_PLATFORM_ADMIN_AUDIENCE"
    )
    access_token_expires_minutes: int = Field(
        default=15, ge=1, le=60, validation_alias="IDENTITY_ACCESS_TOKEN_EXPIRES_MINUTES"
    )
    refresh_token_expires_days: int = Field(
        default=30, ge=1, le=90, validation_alias="IDENTITY_REFRESH_TOKEN_EXPIRES_DAYS"
    )
    mfa_challenge_expires_minutes: int = Field(
        default=5, ge=1, le=15, validation_alias="IDENTITY_MFA_CHALLENGE_EXPIRES_MINUTES"
    )
    email_verification_expires_hours: int = Field(
        default=24, ge=1, le=168, validation_alias="IDENTITY_EMAIL_VERIFICATION_EXPIRES_HOURS"
    )
    password_reset_expires_minutes: int = Field(
        default=30, ge=5, le=120, validation_alias="IDENTITY_PASSWORD_RESET_EXPIRES_MINUTES"
    )

    login_lockout_max_failed_attempts: int = Field(
        default=5, ge=3, le=20, validation_alias="IDENTITY_LOGIN_LOCKOUT_MAX_FAILED_ATTEMPTS"
    )
    login_lockout_window_minutes: int = Field(
        default=15, ge=1, le=120, validation_alias="IDENTITY_LOGIN_LOCKOUT_WINDOW_MINUTES"
    )
    platform_admin_login_lockout_max_failed_attempts: int = Field(
        default=5, ge=3, le=20, validation_alias="IDENTITY_PLATFORM_ADMIN_LOGIN_LOCKOUT_MAX_FAILED_ATTEMPTS"
    )
    platform_admin_login_lockout_window_minutes: int = Field(
        default=15, ge=1, le=120, validation_alias="IDENTITY_PLATFORM_ADMIN_LOGIN_LOCKOUT_WINDOW_MINUTES"
    )

    password_min_length: int = Field(default=12, ge=8, validation_alias="PASSWORD_MIN_LENGTH")
    password_max_length: int = Field(default=128, le=512, validation_alias="PASSWORD_MAX_LENGTH")
    password_require_uppercase: bool = Field(default=True, validation_alias="PASSWORD_REQUIRE_UPPERCASE")
    password_require_lowercase: bool = Field(default=True, validation_alias="PASSWORD_REQUIRE_LOWERCASE")
    password_require_number: bool = Field(default=True, validation_alias="PASSWORD_REQUIRE_NUMBER")
    password_require_special: bool = Field(default=True, validation_alias="PASSWORD_REQUIRE_SPECIAL")
    password_prevent_email_similarity: bool = Field(
        default=True, validation_alias="PASSWORD_PREVENT_EMAIL_SIMILARITY"
    )

    mfa_totp_issuer: str = Field(default="gNxtHire", validation_alias="MFA_TOTP_ISSUER")
    mfa_totp_digits: int = Field(default=6, ge=6, le=8, validation_alias="MFA_TOTP_DIGITS")
    mfa_totp_interval_seconds: int = Field(
        default=30, ge=15, le=120, validation_alias="MFA_TOTP_INTERVAL_SECONDS"
    )
    mfa_totp_valid_window: int = Field(default=1, ge=0, le=2, validation_alias="MFA_TOTP_VALID_WINDOW")
    mfa_recovery_code_count: int = Field(default=10, ge=4, le=20, validation_alias="MFA_RECOVERY_CODE_COUNT")
    mfa_recovery_code_length: int = Field(default=12, ge=8, le=32, validation_alias="MFA_RECOVERY_CODE_LENGTH")

    email_delivery_enabled: bool = Field(
        default=True, validation_alias="IDENTITY_EMAIL_DELIVERY_ENABLED"
    )
    smtp_host: str = Field(default="localhost", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, ge=1, le=65535, validation_alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, validation_alias="SMTP_USERNAME")
    smtp_password: SecretStr | None = Field(default=None, validation_alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=False, validation_alias="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, validation_alias="SMTP_USE_SSL")
    smtp_from_email: str = Field(
        default="no-reply@local.gnxthire.com", validation_alias="SMTP_FROM_EMAIL"
    )
    smtp_from_name: str = Field(default="gNxtHire", validation_alias="SMTP_FROM_NAME")

    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    rate_limit_backend: Literal["redis", "memory"] = Field(
        default="redis", validation_alias="IDENTITY_RATE_LIMIT_BACKEND"
    )

    frontend_email_verify_url: HttpUrl = Field(
        default="http://localhost:5173/auth/verify-email",
        validation_alias="FRONTEND_EMAIL_VERIFY_URL",
    )
    frontend_platform_admin_email_verify_url: HttpUrl = Field(
        default="http://localhost:5174/auth/verify-email?realm=platform",
        validation_alias="FRONTEND_PLATFORM_ADMIN_EMAIL_VERIFY_URL",
    )
    frontend_password_reset_url: HttpUrl = Field(
        default="http://localhost:5173/auth/reset-password",
        validation_alias="FRONTEND_PASSWORD_RESET_URL",
    )
    frontend_platform_admin_password_reset_url: HttpUrl = Field(
        default="http://localhost:5174/auth/reset-password",
        validation_alias="FRONTEND_PLATFORM_ADMIN_PASSWORD_RESET_URL",
    )

    @field_validator("smtp_username", mode="before")
    @classmethod
    def blank_string_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @model_validator(mode="after")
    def validate_runtime_safety(self) -> IdentitySettings:
        if self.smtp_use_tls and self.smtp_use_ssl:
            raise ValueError("SMTP_USE_TLS and SMTP_USE_SSL are mutually exclusive")
        if self.app_env == "production":
            self._validate_production_secrets()
            if self.email_delivery_enabled and not self.smtp_host:
                raise ValueError("production email delivery requires SMTP_HOST")
            if self.rate_limit_backend != "redis":
                raise ValueError("production identity rate limiting requires redis backend")
        return self

    def _validate_production_secrets(self) -> None:
        unsafe_values = {
            self.access_token_secret.get_secret_value(),
            self.refresh_token_secret.get_secret_value(),
            self.mfa_challenge_secret.get_secret_value(),
            self.email_token_secret.get_secret_value(),
            self.password_reset_token_secret.get_secret_value(),
            self.mfa_secret_encryption_key.get_secret_value(),
        }
        if any(value.startswith("change-me-local-") or len(value) < 32 for value in unsafe_values):
            raise ValueError("production identity secrets must be strong non-local values")
        required_env = [
            "IDENTITY_ACCESS_TOKEN_SECRET",
            "IDENTITY_REFRESH_TOKEN_SECRET",
            "IDENTITY_MFA_CHALLENGE_SECRET",
            "IDENTITY_EMAIL_TOKEN_SECRET",
            "IDENTITY_PASSWORD_RESET_TOKEN_SECRET",
            "IDENTITY_MFA_SECRET_ENCRYPTION_KEY",
        ]
        missing = [name for name in required_env if name not in os.environ]
        if missing:
            raise ValueError(f"production identity secrets must be explicit: {', '.join(missing)}")


@lru_cache(maxsize=1)
def get_identity_settings() -> IdentitySettings:
    return IdentitySettings()
