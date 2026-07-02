from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from gnxthire_common.errors import NotFoundError
from gnxthire_common.pagination import CursorPage, CursorPayload, build_cursor_page, decode_cursor

from gnxthire_identity.api.dependencies import request_metadata, require_platform_admin
from gnxthire_identity.platform_admin.repository import PlatformAdminRepository, PlatformUserRecord
from gnxthire_identity.platform_admin.schemas import (
    CreatePlatformUserRequest,
    PlatformUserResponse,
    UpdatePlatformUserRequest,
)
from gnxthire_identity.request_metadata import RequestMetadata

router = APIRouter(prefix="/v1/identity/platform-users", tags=["identity-platform-users"])


def _to_response(repository: PlatformAdminRepository, record: PlatformUserRecord) -> PlatformUserResponse:
    return PlatformUserResponse(
        id=record.id,
        email=record.email,
        display_name=record.display_name,
        status=record.status,
        email_verified=record.email_verified_at is not None,
        mfa_enabled=repository.has_active_mfa_factor(record.id),
        mfa_required=record.mfa_required,
        last_login_at=record.last_login_at,
    )


def _audit(
    repository: PlatformAdminRepository,
    *,
    actor_id: UUID,
    action_key: str,
    target_id: UUID,
    after_state: dict[str, object],
    metadata: RequestMetadata,
) -> None:
    repository.write_audit_log(
        actor_type="platform_user",
        actor_platform_user_id=actor_id,
        action_key=action_key,
        object_id=target_id,
        after_state=after_state,
        ip_address=metadata.ip_address,
        user_agent=metadata.user_agent,
        request_id=metadata.request_id,
    )


def _require_target(repository: PlatformAdminRepository, platform_admin_user_id: UUID) -> PlatformUserRecord:
    target = repository.get_platform_user_by_id(platform_admin_user_id)
    if target is None:
        raise NotFoundError("Platform user not found", safe_detail="Platform user not found")
    return target


@router.get("", response_model=CursorPage[PlatformUserResponse])
def list_platform_users(
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = Query(default=None),
    authenticated=Depends(require_platform_admin),
) -> CursorPage[PlatformUserResponse]:
    _actor, repository, _settings = authenticated
    after_created_at: datetime | None = None
    after_id: UUID | None = None
    if cursor:
        payload = decode_cursor(cursor)
        after_created_at = datetime.fromisoformat(payload.sort_value)
        after_id = payload.entity_id
    records = repository.list_platform_users(after_created_at=after_created_at, after_id=after_id, limit=limit + 1)
    page = records[:limit]
    next_payload = None
    if len(records) > limit:
        last = page[-1]
        next_payload = CursorPayload(sort_value=last.created_at.isoformat(), entity_id=last.id)
    return build_cursor_page([_to_response(repository, record) for record in page], limit=limit, next_payload=next_payload)


@router.post("", response_model=PlatformUserResponse)
def create_platform_user(
    payload: CreatePlatformUserRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_platform_admin),
) -> PlatformUserResponse:
    actor, repository, _settings = authenticated
    created = repository.create_platform_user(email=payload.email, display_name=payload.display_name)
    _audit(
        repository,
        actor_id=actor.id,
        action_key="platform_admin.user_created",
        target_id=created.id,
        after_state={"email": created.email, "status": created.status},
        metadata=metadata,
    )
    return _to_response(repository, created)


@router.get("/{platform_admin_user_id}", response_model=PlatformUserResponse)
def get_platform_user(
    platform_admin_user_id: UUID,
    authenticated=Depends(require_platform_admin),
) -> PlatformUserResponse:
    _actor, repository, _settings = authenticated
    return _to_response(repository, _require_target(repository, platform_admin_user_id))


@router.patch("/{platform_admin_user_id}", response_model=PlatformUserResponse)
def update_platform_user(
    platform_admin_user_id: UUID,
    payload: UpdatePlatformUserRequest,
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_platform_admin),
) -> PlatformUserResponse:
    actor, repository, _settings = authenticated
    target = _require_target(repository, platform_admin_user_id)
    repository.update_display_name(target.id, payload.display_name)
    _audit(
        repository,
        actor_id=actor.id,
        action_key="platform_admin.user_updated",
        target_id=target.id,
        after_state={"display_name": payload.display_name},
        metadata=metadata,
    )
    return _to_response(repository, _require_target(repository, platform_admin_user_id))


def _transition_status(
    platform_admin_user_id: UUID,
    new_status: str,
    action_key: str,
    metadata: RequestMetadata,
    authenticated,
) -> PlatformUserResponse:
    actor, repository, _settings = authenticated
    target = _require_target(repository, platform_admin_user_id)
    repository.set_platform_user_status(target.id, new_status)
    _audit(
        repository,
        actor_id=actor.id,
        action_key=action_key,
        target_id=target.id,
        after_state={"previous_status": target.status, "new_status": new_status},
        metadata=metadata,
    )
    return _to_response(repository, _require_target(repository, platform_admin_user_id))


@router.post("/{platform_admin_user_id}/activate", response_model=PlatformUserResponse)
def activate_platform_user(
    platform_admin_user_id: UUID,
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_platform_admin),
) -> PlatformUserResponse:
    return _transition_status(
        platform_admin_user_id, "active", "platform_admin.user_activated", metadata, authenticated
    )


@router.post("/{platform_admin_user_id}/deactivate", response_model=PlatformUserResponse)
def deactivate_platform_user(
    platform_admin_user_id: UUID,
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_platform_admin),
) -> PlatformUserResponse:
    return _transition_status(
        platform_admin_user_id, "suspended", "platform_admin.user_deactivated", metadata, authenticated
    )


@router.post("/{platform_admin_user_id}/lock", response_model=PlatformUserResponse)
def lock_platform_user(
    platform_admin_user_id: UUID,
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_platform_admin),
) -> PlatformUserResponse:
    actor, repository, _settings = authenticated
    target = _require_target(repository, platform_admin_user_id)
    repository.lock_platform_user(target.id)
    _audit(
        repository,
        actor_id=actor.id,
        action_key="platform_admin.user_locked",
        target_id=target.id,
        after_state={"previous_status": target.status, "new_status": "locked"},
        metadata=metadata,
    )
    return _to_response(repository, _require_target(repository, platform_admin_user_id))


@router.post("/{platform_admin_user_id}/unlock", response_model=PlatformUserResponse)
def unlock_platform_user(
    platform_admin_user_id: UUID,
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_platform_admin),
) -> PlatformUserResponse:
    return _transition_status(
        platform_admin_user_id, "active", "platform_admin.user_unlocked", metadata, authenticated
    )


@router.post("/{platform_admin_user_id}/require-password-reset", response_model=PlatformUserResponse)
def require_password_reset(
    platform_admin_user_id: UUID,
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_platform_admin),
) -> PlatformUserResponse:
    actor, repository, _settings = authenticated
    target = _require_target(repository, platform_admin_user_id)
    repository.revoke_user_sessions(target.id)
    repository.revoke_pending_password_reset_tokens(target.id)
    _audit(
        repository,
        actor_id=actor.id,
        action_key="platform_admin.user_password_reset_required",
        target_id=target.id,
        after_state={},
        metadata=metadata,
    )
    return _to_response(repository, _require_target(repository, platform_admin_user_id))


@router.post("/{platform_admin_user_id}/require-mfa", response_model=PlatformUserResponse)
def require_mfa(
    platform_admin_user_id: UUID,
    metadata: RequestMetadata = Depends(request_metadata),
    authenticated=Depends(require_platform_admin),
) -> PlatformUserResponse:
    actor, repository, _settings = authenticated
    target = _require_target(repository, platform_admin_user_id)
    repository.set_mfa_required(target.id, True)
    _audit(
        repository,
        actor_id=actor.id,
        action_key="platform_admin.user_mfa_required",
        target_id=target.id,
        after_state={"mfa_required": True},
        metadata=metadata,
    )
    return _to_response(repository, _require_target(repository, platform_admin_user_id))
