from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ActorType(StrEnum):
    TENANT_USER = "tenant_user"
    PLATFORM_USER = "platform_user"
    AI_AGENT = "ai_agent"
    SYSTEM = "system"
    WEBHOOK = "webhook"
    SCHEDULER = "scheduler"


class RequestContext(BaseModel):
    request_id: str = Field(min_length=1)
    tenant_id: UUID | None = None
    actor_id: UUID | None = None
    actor_type: ActorType
    is_platform_admin: bool = False
    platform_admin_id: UUID | None = None
    correlation_id: str | None = None
    permissions: tuple[str, ...] = ()
    support_session_id: UUID | None = None
    source_ip: str | None = None
    user_agent: str | None = None
    auth_subject: str | None = None
    session_id: UUID | None = None

    @model_validator(mode="after")
    def validate_realm_context(self) -> RequestContext:
        if self.is_platform_admin and self.actor_type != ActorType.PLATFORM_USER:
            raise ValueError("platform-admin context requires actor_type=platform_user")
        if self.is_platform_admin and self.platform_admin_id is None:
            raise ValueError("platform-admin context requires platform_admin_id")
        if self.support_session_id is not None and not self.is_platform_admin:
            raise ValueError("support_session_id is allowed only for platform-admin context")
        if not self.is_platform_admin and self.tenant_id is None:
            raise ValueError("tenant-facing context requires tenant_id")
        return self

    @property
    def effective_correlation_id(self) -> str:
        return self.correlation_id or self.request_id
