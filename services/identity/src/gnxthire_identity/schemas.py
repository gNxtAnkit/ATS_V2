from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class EmailModel(BaseModel):
    @field_validator("email", check_fields=False)
    @classmethod
    def validate_email_shape(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Invalid email address")
        return normalized


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class LoginResponse(BaseModel):
    status: str
    tokens: TokenPair | None = None
    mfa_challenge_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=1)
    confirm_password: str = Field(min_length=1)


class TotpSetupResponse(BaseModel):
    provisioning_uri: str
    manual_entry_secret: str


class TotpConfirmRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class TotpConfirmResponse(BaseModel):
    recovery_codes: list[str]


class TotpVerifyRequest(BaseModel):
    mfa_challenge_token: str = Field(min_length=1)
    code: str = Field(min_length=6, max_length=32)


class MfaRecoveryCodeVerifyRequest(BaseModel):
    mfa_challenge_token: str = Field(min_length=1)
    recovery_code: str = Field(min_length=6, max_length=64)


class RecoveryCodesResponse(BaseModel):
    recovery_codes: list[str]


class DisableMfaRequest(BaseModel):
    password: str = Field(min_length=1)


class MeResponse(BaseModel):
    actor_id: UUID
    actor_type: str
    tenant_id: UUID | None = None
    email: str
    display_name: str
    email_verified: bool
    mfa_enabled: bool


class MessageResponse(BaseModel):
    message: str


class PasswordPolicyResponse(BaseModel):
    min_length: int
    max_length: int
    require_uppercase: bool
    require_lowercase: bool
    require_number: bool
    require_special: bool
    prevent_email_similarity: bool
