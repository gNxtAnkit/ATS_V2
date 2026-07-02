from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from gnxthire_identity.schemas import EmailModel


class PlatformAdminLoginRequest(EmailModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1)


class PlatformAdminForgotPasswordRequest(EmailModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)


class PlatformAdminResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=16)
    new_password: str = Field(min_length=1)
    confirm_password: str = Field(min_length=1)


class PlatformAdminRequestEmailVerificationRequest(EmailModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)


class PlatformAdminVerifyEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=16)


class CreatePlatformUserRequest(EmailModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=1, max_length=200)


class UpdatePlatformUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=200)


class PlatformUserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    status: str
    email_verified: bool
    mfa_enabled: bool
    mfa_required: bool
    last_login_at: datetime | None
