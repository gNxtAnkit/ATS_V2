from __future__ import annotations

from collections.abc import Mapping, Sequence

from pydantic import BaseModel, Field


class FieldError(BaseModel):
    field: str = Field(min_length=1)
    message: str = Field(min_length=1)
    code: str = Field(default="invalid", min_length=1)


class AppError(Exception):
    code = "internal_error"
    status_code = 500

    def __init__(
        self,
        message: str,
        *,
        safe_detail: str | None = None,
        field_errors: Sequence[FieldError] | None = None,
    ) -> None:
        super().__init__(message)
        self.safe_detail = safe_detail or message
        self.field_errors = tuple(field_errors or ())


class ValidationFailure(AppError):
    code = "validation_failed"
    status_code = 400


class ValidationAppError(ValidationFailure):
    pass


class AuthenticationError(AppError):
    code = "authentication_required"
    status_code = 401


class AuthorizationError(AppError):
    code = "authorization_denied"
    status_code = 403


class TenantContextRequired(AuthorizationError):
    code = "tenant_context_required"


class PlatformContextRequired(AuthorizationError):
    code = "platform_context_required"


class NotFoundError(AppError):
    code = "not_found"
    status_code = 404


class ConflictError(AppError):
    code = "conflict"
    status_code = 409


class RateLimitError(AppError):
    code = "rate_limited"
    status_code = 429


class DatabaseAppError(AppError):
    code = "database_error"
    status_code = 500


class ErrorBody(BaseModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    field_errors: list[FieldError] = Field(default_factory=list)
    request_id: str = Field(min_length=1)


class ErrorEnvelope(BaseModel):
    error: ErrorBody


def build_error_envelope(
    *,
    request_id: str,
    code: str,
    message: str,
    field_errors: Sequence[FieldError] | None = None,
    details: Mapping[str, str] | None = None,
) -> ErrorEnvelope:
    normalized_field_errors = list(field_errors or ())
    if details:
        normalized_field_errors.extend(
            FieldError(field=field, message=detail) for field, detail in details.items()
        )
    return ErrorEnvelope(
        error=ErrorBody(
            request_id=request_id,
            code=code,
            message=message,
            field_errors=normalized_field_errors,
        )
    )


def error_to_envelope(error: AppError, *, request_id: str) -> ErrorEnvelope:
    return build_error_envelope(
        request_id=request_id,
        code=error.code,
        message=error.safe_detail,
        field_errors=error.field_errors,
    )


GnxthireError = AppError
