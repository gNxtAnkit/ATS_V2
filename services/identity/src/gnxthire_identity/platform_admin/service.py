from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from gnxthire_common.errors import AuthenticationError, ConflictError, ValidationFailure
from gnxthire_identity.config import IdentitySettings
from gnxthire_identity.email import (
    EmailSender,
    build_email_verification_url,
    build_password_reset_url,
    mfa_disabled_email,
    mfa_enabled_email,
    password_changed_email,
    password_reset_email,
    verification_email,
)
from gnxthire_identity.platform_admin.repository import (
    PENDING_TOTP_SECRET_PREFIX,
    PlatformAdminRepository,
    PlatformUserRecord,
)
from gnxthire_identity.rate_limit import EMAIL_RATE_LIMIT, LOGIN_RATE_LIMIT, MFA_RATE_LIMIT, RateLimiter, TOKEN_RATE_LIMIT
from gnxthire_identity.request_metadata import RequestMetadata
from gnxthire_identity.schemas import LoginResponse, MessageResponse, TokenPair
from gnxthire_identity.security import (
    SignedTokenClaims,
    build_totp_uri,
    create_signed_token,
    decrypt_secret,
    encrypt_secret,
    expires_in,
    generate_opaque_token,
    generate_recovery_codes,
    generate_totp_secret,
    hash_password,
    token_hmac,
    utcnow,
    validate_password_policy,
    verify_password,
    verify_signed_token,
    verify_totp_code,
)


class PlatformAdminIdentityService:
    def __init__(
        self,
        *,
        repository: PlatformAdminRepository,
        settings: IdentitySettings,
        email_sender: EmailSender,
        rate_limiter: RateLimiter,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._email_sender = email_sender
        self._rate_limiter = rate_limiter

    def login(self, *, email: str, password: str, metadata: RequestMetadata) -> LoginResponse:
        self._rate_limiter.hit(f"{metadata.ip_address}:platform-admin:{email}", LOGIN_RATE_LIMIT)
        user = self._repository.get_platform_user_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            if user is not None:
                self._write_audit(user.id, "platform_admin.login_failed", "system", metadata)
                self._enforce_lockout_threshold(user, metadata)
            raise AuthenticationError("Invalid credentials", safe_detail="Invalid credentials")
        self._ensure_user_can_authenticate(user)
        mfa_factor = self._repository.get_primary_totp_factor(user.id)
        if mfa_factor is not None:
            challenge = self._create_mfa_challenge(user)
            self._write_audit(user.id, "platform_admin.login_success", "platform_user", metadata, {"mfa_required": True})
            return LoginResponse(
                status="mfa_required",
                mfa_required=True,
                mfa_challenge_token=challenge,
                challenge_token=challenge,
                available_methods=self._available_mfa_methods(user.id),
                expires_in_seconds=self._settings.mfa_challenge_expires_minutes * 60,
            )
        tokens = self._issue_session_tokens(user, metadata, mfa_verified=False)
        self._repository.update_last_login(user.id)
        self._write_audit(user.id, "platform_admin.login_success", "platform_user", metadata)
        return LoginResponse(status="authenticated", tokens=tokens, mfa_required=False)

    def refresh(self, *, refresh_token: str, metadata: RequestMetadata) -> TokenPair:
        self._rate_limiter.hit(f"{metadata.ip_address}:platform-admin:refresh", TOKEN_RATE_LIMIT)
        payload = verify_signed_token(
            refresh_token,
            secret=self._settings.refresh_token_secret.get_secret_value(),
            issuer=self._settings.token_issuer,
            audience=self._settings.platform_admin_audience,
            token_type="refresh",
        )
        session_hash = token_hmac(refresh_token, self._settings.refresh_token_secret.get_secret_value())
        session = self._repository.get_active_session_by_hash(session_hash)
        if session is None or session.revoked_at is not None or session.expires_at <= utcnow():
            raise AuthenticationError("Invalid refresh token", safe_detail="Invalid refresh token")
        user = self._repository.get_platform_user_by_id(session.platform_user_id)
        if user is None or user.status != "active":
            raise AuthenticationError("Invalid refresh token", safe_detail="Invalid refresh token")
        new_refresh = self._create_refresh_token(user, str(session.id))
        new_hash = token_hmac(new_refresh, self._settings.refresh_token_secret.get_secret_value())
        self._repository.rotate_session_token(
            session.id, new_hash, utcnow() + timedelta(days=self._settings.refresh_token_expires_days)
        )
        access_token = self._create_access_token(user, str(session.id))
        self._write_audit(user.id, "platform_admin.login_success", "platform_user", metadata, {"refresh": True})
        return TokenPair(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_in_seconds=self._settings.access_token_expires_minutes * 60,
        )

    def logout(self, *, refresh_token: str | None, metadata: RequestMetadata) -> MessageResponse:
        if refresh_token:
            try:
                verify_signed_token(
                    refresh_token,
                    secret=self._settings.refresh_token_secret.get_secret_value(),
                    issuer=self._settings.token_issuer,
                    audience=self._settings.platform_admin_audience,
                    token_type="refresh",
                )
                session_hash = token_hmac(refresh_token, self._settings.refresh_token_secret.get_secret_value())
                session = self._repository.get_active_session_by_hash(session_hash)
                if session is not None:
                    self._repository.revoke_session(session.id)
                    self._write_audit(session.platform_user_id, "platform_admin.logout", "platform_user", metadata)
            except AuthenticationError:
                pass
        return MessageResponse(message="Logged out")

    def forgot_password(self, *, email: str, metadata: RequestMetadata) -> MessageResponse:
        self._rate_limiter.hit(f"{metadata.ip_address}:platform-admin:{email}", EMAIL_RATE_LIMIT)
        user = self._repository.get_platform_user_by_email(email)
        if user is not None:
            raw_token = generate_opaque_token()
            hmac_value = token_hmac(raw_token, self._settings.password_reset_token_secret.get_secret_value())
            self._repository.create_password_reset_token(
                platform_user_id=user.id,
                token_hmac=hmac_value,
                expires_at=expires_in(minutes=self._settings.password_reset_expires_minutes),
            )
            reset_url = build_password_reset_url(self._settings, token=raw_token, platform_admin=True)
            self._email_sender.send(password_reset_email(user.email, reset_url=reset_url))
            self._write_audit(user.id, "platform_admin.password_reset_requested", "system", metadata)
        return MessageResponse(message="If an account exists, reset instructions have been sent.")

    def reset_password(
        self, *, raw_token: str, new_password: str, confirm_password: str, metadata: RequestMetadata
    ) -> MessageResponse:
        self._rate_limiter.hit(f"{metadata.ip_address}:platform-admin:reset", EMAIL_RATE_LIMIT)
        if new_password != confirm_password:
            raise ValidationFailure("Password confirmation does not match", safe_detail="Invalid password")
        hmac_value = token_hmac(raw_token, self._settings.password_reset_token_secret.get_secret_value())
        user_id = self._repository.consume_password_reset_token(hmac_value)
        if user_id is None:
            self._write_audit(None, "platform_admin.password_reset_invalid_token", "system", metadata)
            raise AuthenticationError("Invalid reset token", safe_detail="Invalid reset token")
        user = self._repository.get_platform_user_by_id(user_id)
        if user is None:
            raise AuthenticationError("Invalid reset token", safe_detail="Invalid reset token")
        validate_password_policy(new_password, user.email, self._settings)
        self._repository.update_password(user.id, hash_password(new_password))
        self._repository.revoke_user_sessions(user.id)
        self._email_sender.send(password_changed_email(user.email))
        self._write_audit(user.id, "platform_admin.password_reset_completed", "system", metadata)
        return MessageResponse(message="Password reset completed")

    def request_email_verification(self, *, email: str, metadata: RequestMetadata) -> MessageResponse:
        self._rate_limiter.hit(f"{metadata.ip_address}:platform-admin:{email}:verify", EMAIL_RATE_LIMIT)
        user = self._repository.get_platform_user_by_email(email)
        if user is not None and user.email_verified_at is None:
            raw_token = generate_opaque_token()
            hmac_value = token_hmac(raw_token, self._settings.email_token_secret.get_secret_value())
            self._repository.create_email_verification_token(
                platform_user_id=user.id,
                email=user.email,
                token_hmac=hmac_value,
                expires_at=expires_in(hours=self._settings.email_verification_expires_hours),
            )
            verification_url = build_email_verification_url(self._settings, token=raw_token, platform_admin=True)
            self._email_sender.send(verification_email(user.email, verification_url=verification_url))
            self._write_audit(user.id, "platform_admin.email_verification_requested", "system", metadata)
        return MessageResponse(message="If an account exists, verification instructions have been sent.")

    def verify_email(self, *, raw_token: str, metadata: RequestMetadata) -> MessageResponse:
        self._rate_limiter.hit(f"{metadata.ip_address}:platform-admin:verify-email", EMAIL_RATE_LIMIT)
        hmac_value = token_hmac(raw_token, self._settings.email_token_secret.get_secret_value())
        user_id = self._repository.consume_email_verification_token(hmac_value)
        if user_id is None:
            self._write_audit(None, "platform_admin.email_verification_invalid_token", "system", metadata)
            raise AuthenticationError("Invalid verification token", safe_detail="Invalid verification token")
        self._repository.mark_email_verified(user_id)
        self._write_audit(user_id, "platform_admin.email_verified", "system", metadata)
        return MessageResponse(message="Email verified")

    def setup_totp(self, *, user: PlatformUserRecord, metadata: RequestMetadata) -> tuple[str, str]:
        if self._repository.get_primary_totp_factor(user.id) is not None:
            raise ConflictError("MFA is already enabled", safe_detail="MFA is already enabled for this account.")
        secret = generate_totp_secret()
        encrypted_secret = encrypt_secret(secret, self._settings.mfa_secret_encryption_key.get_secret_value())
        self._repository.create_pending_totp_factor(user.id, encrypted_secret)
        self._write_audit(user.id, "platform_admin.mfa_setup_started", "platform_user", metadata)
        uri = build_totp_uri(
            issuer=self._settings.mfa_totp_issuer,
            account_name=user.email,
            secret=secret,
            digits=self._settings.mfa_totp_digits,
            interval=self._settings.mfa_totp_interval_seconds,
        )
        return uri, secret

    def confirm_totp(self, *, user: PlatformUserRecord, code: str, metadata: RequestMetadata) -> list[str]:
        factor = self._repository.get_pending_totp_factor(user.id)
        if factor is None or factor.secret_ref is None:
            raise ConflictError("No pending MFA setup", safe_detail="No pending MFA setup")
        encrypted_secret = self._pending_secret_ref_to_encrypted_secret(factor.secret_ref)
        secret = decrypt_secret(encrypted_secret, self._settings.mfa_secret_encryption_key.get_secret_value())
        if not verify_totp_code(
            secret=secret,
            code=code,
            digits=self._settings.mfa_totp_digits,
            interval=self._settings.mfa_totp_interval_seconds,
            valid_window=self._settings.mfa_totp_valid_window,
        ):
            self._write_audit(user.id, "platform_admin.mfa_failed", "platform_user", metadata)
            raise AuthenticationError("Invalid MFA code", safe_detail="Invalid MFA code")
        recovery_codes = generate_recovery_codes(
            self._settings.mfa_recovery_code_count, self._settings.mfa_recovery_code_length
        )
        self._repository.enable_mfa_factor(factor.id, encrypted_secret)
        self._repository.replace_recovery_codes(
            user.id,
            [token_hmac(code, self._settings.mfa_challenge_secret.get_secret_value()) for code in recovery_codes],
        )
        self._email_sender.send(mfa_enabled_email(user.email))
        self._write_audit(user.id, "platform_admin.mfa_enabled", "platform_user", metadata)
        return recovery_codes

    def verify_mfa_challenge(self, *, challenge_token: str, code: str, metadata: RequestMetadata) -> LoginResponse:
        self._rate_limiter.hit(f"{metadata.ip_address}:platform-admin:mfa", MFA_RATE_LIMIT)
        payload = verify_signed_token(
            challenge_token,
            secret=self._settings.mfa_challenge_secret.get_secret_value(),
            issuer=self._settings.token_issuer,
            audience=self._settings.platform_admin_audience,
            token_type="mfa_challenge",
        )
        user_id = UUID(payload["sub"])
        user = self._repository.get_platform_user_by_id(user_id)
        if user is None:
            raise AuthenticationError("Invalid MFA challenge", safe_detail="Invalid MFA challenge")
        self._ensure_user_can_authenticate(user)
        factor = self._repository.get_primary_totp_factor(user_id)
        verified = False
        if factor is not None and factor.secret_ref is not None:
            secret = decrypt_secret(factor.secret_ref, self._settings.mfa_secret_encryption_key.get_secret_value())
            verified = verify_totp_code(
                secret=secret,
                code=code,
                digits=self._settings.mfa_totp_digits,
                interval=self._settings.mfa_totp_interval_seconds,
                valid_window=self._settings.mfa_totp_valid_window,
            )
        if not verified:
            recovery_hash = token_hmac(code, self._settings.mfa_challenge_secret.get_secret_value())
            verified = self._repository.consume_recovery_code(user_id, recovery_hash)
            if verified:
                self._write_audit(
                    user_id, "platform_admin.login_success", "platform_user", metadata, {"recovery_code_used": True}
                )
        if not verified:
            self._write_audit(user_id, "platform_admin.mfa_failed", "platform_user", metadata)
            raise AuthenticationError("Invalid MFA code", safe_detail="Invalid MFA code")
        tokens = self._issue_session_tokens(user, metadata, mfa_verified=True)
        self._repository.update_last_login(user.id)
        self._write_audit(user.id, "platform_admin.login_success", "platform_user", metadata, {"mfa_verified": True})
        return LoginResponse(status="authenticated", tokens=tokens, mfa_required=False)

    def regenerate_recovery_codes(self, *, user: PlatformUserRecord, password: str, metadata: RequestMetadata) -> list[str]:
        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid credentials", safe_detail="Invalid credentials")
        if self._repository.get_primary_totp_factor(user.id) is None:
            raise ConflictError("MFA is not enabled", safe_detail="MFA is not enabled for this account.")
        codes = generate_recovery_codes(self._settings.mfa_recovery_code_count, self._settings.mfa_recovery_code_length)
        self._repository.replace_recovery_codes(
            user.id, [token_hmac(code, self._settings.mfa_challenge_secret.get_secret_value()) for code in codes]
        )
        self._write_audit(user.id, "platform_admin.mfa_recovery_codes_regenerated", "platform_user", metadata)
        return codes

    def disable_mfa(self, *, user: PlatformUserRecord, password: str, metadata: RequestMetadata) -> MessageResponse:
        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid credentials", safe_detail="Invalid credentials")
        if self._repository.get_primary_totp_factor(user.id) is None:
            raise ConflictError("MFA is not enabled", safe_detail="MFA is not enabled for this account.")
        self._repository.disable_mfa(user.id)
        self._email_sender.send(mfa_disabled_email(user.email))
        self._write_audit(user.id, "platform_admin.mfa_disabled", "platform_user", metadata)
        return MessageResponse(message="MFA disabled")

    def change_password(
        self,
        *,
        user: PlatformUserRecord,
        current_password: str,
        new_password: str,
        confirm_password: str,
        metadata: RequestMetadata,
    ) -> MessageResponse:
        if new_password != confirm_password:
            raise ValidationFailure("Password confirmation does not match", safe_detail="Invalid password")
        if not verify_password(current_password, user.password_hash):
            raise AuthenticationError("Invalid credentials", safe_detail="Invalid credentials")
        validate_password_policy(new_password, user.email, self._settings)
        self._repository.update_password(user.id, hash_password(new_password))
        self._repository.revoke_user_sessions(user.id)
        self._email_sender.send(password_changed_email(user.email))
        self._write_audit(user.id, "platform_admin.password_changed", "platform_user", metadata)
        return MessageResponse(message="Password changed")

    def _ensure_user_can_authenticate(self, user: PlatformUserRecord) -> None:
        if user.status not in {"active", "invited"}:
            raise AuthenticationError("Account is not active", safe_detail="Invalid credentials")

    def _enforce_lockout_threshold(self, user: PlatformUserRecord, metadata: RequestMetadata) -> None:
        failed_count = self._repository.count_recent_failed_logins(
            user.id, window_minutes=self._settings.platform_admin_login_lockout_window_minutes
        )
        if failed_count >= self._settings.platform_admin_login_lockout_max_failed_attempts:
            self._repository.lock_platform_user(user.id)
            self._write_audit(user.id, "platform_admin.account_locked", "system", metadata)

    def _issue_session_tokens(
        self, user: PlatformUserRecord, metadata: RequestMetadata, *, mfa_verified: bool
    ) -> TokenPair:
        placeholder_session_id = "00000000-0000-0000-0000-000000000000"
        refresh_token = self._create_refresh_token(user, placeholder_session_id)
        refresh_hash = token_hmac(refresh_token, self._settings.refresh_token_secret.get_secret_value())
        session_id = self._repository.create_session(
            platform_user_id=user.id,
            session_token_hash=refresh_hash,
            expires_at=datetime.now(UTC) + timedelta(days=self._settings.refresh_token_expires_days),
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
            mfa_verified=mfa_verified,
        )
        refresh_token = self._create_refresh_token(user, str(session_id))
        refresh_hash = token_hmac(refresh_token, self._settings.refresh_token_secret.get_secret_value())
        self._repository.rotate_session_token(
            session_id, refresh_hash, datetime.now(UTC) + timedelta(days=self._settings.refresh_token_expires_days)
        )
        return TokenPair(
            access_token=self._create_access_token(user, str(session_id)),
            refresh_token=refresh_token,
            expires_in_seconds=self._settings.access_token_expires_minutes * 60,
        )

    def _create_access_token(self, user: PlatformUserRecord, session_id: str) -> str:
        return create_signed_token(
            SignedTokenClaims(
                subject=str(user.id),
                actor_type="platform_user",
                token_type="access",
                audience=self._settings.platform_admin_audience,
                issuer=self._settings.token_issuer,
                expires_at=expires_in(minutes=self._settings.access_token_expires_minutes),
                session_id=session_id,
                tenant_id=None,
            ),
            self._settings.access_token_secret.get_secret_value(),
        )

    def _create_refresh_token(self, user: PlatformUserRecord, session_id: str) -> str:
        return create_signed_token(
            SignedTokenClaims(
                subject=str(user.id),
                actor_type="platform_user",
                token_type="refresh",
                audience=self._settings.platform_admin_audience,
                issuer=self._settings.token_issuer,
                expires_at=expires_in(days=self._settings.refresh_token_expires_days),
                session_id=session_id,
                tenant_id=None,
            ),
            self._settings.refresh_token_secret.get_secret_value(),
        )

    def _create_mfa_challenge(self, user: PlatformUserRecord) -> str:
        return create_signed_token(
            SignedTokenClaims(
                subject=str(user.id),
                actor_type="platform_user",
                token_type="mfa_challenge",
                audience=self._settings.platform_admin_audience,
                issuer=self._settings.token_issuer,
                expires_at=expires_in(minutes=self._settings.mfa_challenge_expires_minutes),
                tenant_id=None,
            ),
            self._settings.mfa_challenge_secret.get_secret_value(),
        )

    def _available_mfa_methods(self, platform_user_id: UUID) -> list[str]:
        methods = ["totp"]
        if self._repository.count_active_recovery_codes(platform_user_id) > 0:
            methods.append("recovery_code")
        return methods

    def _pending_secret_ref_to_encrypted_secret(self, secret_ref: str) -> str:
        if not secret_ref.startswith(PENDING_TOTP_SECRET_PREFIX):
            raise ConflictError("No pending MFA setup", safe_detail="No pending MFA setup")
        return secret_ref.removeprefix(PENDING_TOTP_SECRET_PREFIX)

    def _write_audit(
        self,
        platform_user_id: UUID | None,
        action_key: str,
        actor_type: str,
        metadata: RequestMetadata,
        after_state: dict[str, object] | None = None,
    ) -> None:
        self._repository.write_audit_log(
            actor_type=actor_type,
            actor_platform_user_id=platform_user_id,
            action_key=action_key,
            object_id=platform_user_id,
            after_state=after_state,
            ip_address=metadata.ip_address,
            user_agent=metadata.user_agent,
            request_id=metadata.request_id,
        )
