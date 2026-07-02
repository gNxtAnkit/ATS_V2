from __future__ import annotations

from fastapi import APIRouter, Depends

from gnxthire_identity.api.dependencies import (
    rate_limiter_for_settings,
    require_tenant_user,
    request_metadata,
    tenant_identity_service,
)
from gnxthire_identity.config import IdentitySettings, get_identity_settings
from gnxthire_identity.email import SmtpEmailSender
from gnxthire_identity.request_metadata import RequestMetadata
from gnxthire_identity.schemas import (
    ChangePasswordRequest,
    DisableMfaRequest,
    LoginResponse,
    LogoutRequest,
    MfaRecoveryCodeVerifyRequest,
    MeResponse,
    MessageResponse,
    PasswordPolicyResponse,
    RecoveryCodesResponse,
    RefreshRequest,
    TokenPair,
    TotpConfirmRequest,
    TotpConfirmResponse,
    TotpSetupResponse,
    TotpVerifyRequest,
)
from gnxthire_identity.tenant.schemas import (
    ForgotPasswordRequest,
    RequestEmailVerificationRequest,
    ResetPasswordRequest,
    TenantLoginRequest,
    VerifyEmailRequest,
)
from gnxthire_identity.tenant.service import TenantIdentityService

router = APIRouter(prefix="/v1/identity", tags=["identity-tenant"])


def _password_policy_response(settings) -> PasswordPolicyResponse:
    return PasswordPolicyResponse(
        min_length=settings.password_min_length,
        max_length=settings.password_max_length,
        require_uppercase=settings.password_require_uppercase,
        require_lowercase=settings.password_require_lowercase,
        require_number=settings.password_require_number,
        require_special=settings.password_require_special,
        prevent_email_similarity=settings.password_prevent_email_similarity,
    )


def _service_from_authenticated(repository, settings) -> TenantIdentityService:
    return TenantIdentityService(
        repository=repository,
        settings=settings,
        email_sender=SmtpEmailSender(settings),
        rate_limiter=rate_limiter_for_settings(settings),
    )


@router.post("/auth/login", response_model=LoginResponse)
def login(
    payload: TenantLoginRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    service: TenantIdentityService = Depends(tenant_identity_service),
) -> LoginResponse:
    return service.login(email=payload.email, password=payload.password, metadata=metadata)


@router.get("/auth/password-policy", response_model=PasswordPolicyResponse)
def password_policy(settings: IdentitySettings = Depends(get_identity_settings)) -> PasswordPolicyResponse:
    return _password_policy_response(settings)


@router.post("/auth/refresh", response_model=TokenPair)
def refresh(
    payload: RefreshRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    service: TenantIdentityService = Depends(tenant_identity_service),
) -> TokenPair:
    return service.refresh(refresh_token=payload.refresh_token, metadata=metadata)


@router.post("/auth/logout", response_model=MessageResponse)
def logout(
    payload: LogoutRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    service: TenantIdentityService = Depends(tenant_identity_service),
) -> MessageResponse:
    return service.logout(refresh_token=payload.refresh_token, metadata=metadata)


@router.get("/auth/me", response_model=MeResponse)
def me(authenticated=Depends(require_tenant_user)) -> MeResponse:
    user, repository, _settings = authenticated
    mfa_factor = repository.get_primary_totp_factor(user.tenant_id, user.id)
    return MeResponse(
        actor_id=user.id,
        actor_type="tenant_user",
        tenant_id=user.tenant_id,
        email=user.email,
        display_name=user.display_name,
        email_verified=user.email_verified_at is not None,
        mfa_enabled=mfa_factor is not None,
    )


@router.post("/auth/forgot-password", response_model=MessageResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    service: TenantIdentityService = Depends(tenant_identity_service),
) -> MessageResponse:
    return service.forgot_password(email=payload.email, metadata=metadata)


@router.post("/auth/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    service: TenantIdentityService = Depends(tenant_identity_service),
) -> MessageResponse:
    return service.reset_password(
        raw_token=payload.token,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password,
        metadata=metadata,
    )


@router.post("/auth/request-email-verification", response_model=MessageResponse)
def request_email_verification(
    payload: RequestEmailVerificationRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    service: TenantIdentityService = Depends(tenant_identity_service),
) -> MessageResponse:
    return service.request_email_verification(email=payload.email, metadata=metadata)


@router.post("/auth/verify-email", response_model=MessageResponse)
def verify_email(
    payload: VerifyEmailRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    service: TenantIdentityService = Depends(tenant_identity_service),
) -> MessageResponse:
    return service.verify_email(raw_token=payload.token, metadata=metadata)


@router.post("/auth/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_tenant_user),
) -> MessageResponse:
    user, repository, settings = authenticated
    service = _service_from_authenticated(repository, settings)
    return service.change_password(
        user=user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password,
        metadata=metadata,
    )


@router.post("/mfa/totp/setup", response_model=TotpSetupResponse)
def mfa_setup(
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_tenant_user),
) -> TotpSetupResponse:
    user, repository, settings = authenticated
    service = _service_from_authenticated(repository, settings)
    provisioning_uri, secret = service.setup_totp(user=user, metadata=metadata)
    return TotpSetupResponse(provisioning_uri=provisioning_uri, manual_entry_secret=secret)


@router.post("/mfa/totp/confirm", response_model=TotpConfirmResponse)
def mfa_confirm(
    payload: TotpConfirmRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_tenant_user),
) -> TotpConfirmResponse:
    user, repository, settings = authenticated
    service = _service_from_authenticated(repository, settings)
    return TotpConfirmResponse(recovery_codes=service.confirm_totp(user=user, code=payload.code, metadata=metadata))


@router.post("/mfa/totp/verify", response_model=LoginResponse)
def mfa_verify(
    payload: TotpVerifyRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    service: TenantIdentityService = Depends(tenant_identity_service),
) -> LoginResponse:
    return service.verify_mfa_challenge(
        challenge_token=payload.mfa_challenge_token,
        code=payload.code,
        metadata=metadata,
    )


@router.post("/mfa/recovery-code/verify", response_model=LoginResponse)
def mfa_recovery_code_verify(
    payload: MfaRecoveryCodeVerifyRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    service: TenantIdentityService = Depends(tenant_identity_service),
) -> LoginResponse:
    return service.verify_mfa_challenge(
        challenge_token=payload.mfa_challenge_token,
        code=payload.recovery_code,
        metadata=metadata,
    )


@router.post("/mfa/recovery-codes/regenerate", response_model=RecoveryCodesResponse)
def recovery_codes_regenerate(
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_tenant_user),
) -> RecoveryCodesResponse:
    user, repository, settings = authenticated
    service = _service_from_authenticated(repository, settings)
    return RecoveryCodesResponse(recovery_codes=service.regenerate_recovery_codes(user=user, metadata=metadata))


@router.post("/mfa/disable", response_model=MessageResponse)
def mfa_disable(
    payload: DisableMfaRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_tenant_user),
) -> MessageResponse:
    user, repository, settings = authenticated
    service = _service_from_authenticated(repository, settings)
    return service.disable_mfa(user=user, password=payload.password, metadata=metadata)
