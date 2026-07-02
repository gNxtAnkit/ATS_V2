from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from gnxthire_identity.schemas import EmailModel


class TenantLoginRequest(EmailModel):
    """Tenant is never accepted here; it is resolved internally from the normalized email."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1)


class ForgotPasswordRequest(EmailModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=16)
    new_password: str = Field(min_length=1)
    confirm_password: str = Field(min_length=1)


class RequestEmailVerificationRequest(EmailModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)


class VerifyEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=16)
