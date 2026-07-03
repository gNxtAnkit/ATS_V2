from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from gnxthire_common.errors import ConflictError, NotFoundError
from gnxthire_common.logging import redact_mapping
from gnxthire_common.pagination import CursorPayload, decode_cursor, encode_cursor


def row_to_dict(row: Mapping[str, Any]) -> dict[str, Any]:
    return dict(row)


def clean_update_payload(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


class PlatformAdminRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def one(self, sql: str, params: Mapping[str, Any]) -> dict[str, Any] | None:
        row = self.session.execute(text(sql), dict(params)).mappings().one_or_none()
        return row_to_dict(row) if row else None

    def many(self, sql: str, params: Mapping[str, Any]) -> list[dict[str, Any]]:
        rows = self.session.execute(text(sql), dict(params)).mappings().all()
        return [row_to_dict(row) for row in rows]

    def execute(self, sql: str, params: Mapping[str, Any]) -> None:
        self.session.execute(text(sql), dict(params))

    def execute_returning_one(self, sql: str, params: Mapping[str, Any]) -> dict[str, Any]:
        try:
            row = self.session.execute(text(sql), dict(params)).mappings().one()
        except IntegrityError as exc:
            raise ConflictError("Database constraint violation", safe_detail="Resource conflicts with existing data") from exc
        return row_to_dict(row)

    def require_by_id(self, table: str, entity_id: UUID, *, id_column: str = "id") -> dict[str, Any]:
        row = self.one(
            f"SELECT * FROM {table} WHERE {id_column} = :id LIMIT 1",
            {"id": entity_id},
        )
        if row is None:
            raise NotFoundError("Resource not found", safe_detail="Resource not found")
        return row

    def list_page(
        self,
        *,
        table: str,
        limit: int,
        cursor: str | None,
        filters: Mapping[str, Any] | None = None,
        search_columns: Sequence[str] = (),
        search: str | None = None,
        search_extra_sql: str | None = None,
        order_column: str = "created_at",
    ) -> tuple[list[dict[str, Any]], str | None, bool]:
        """search_extra_sql is an optional additional OR-ed raw SQL predicate (e.g. an
        EXISTS subquery reaching into a related table) for callers whose search needs to
        cover a column that isn't on `table` itself — see list_tenants' domain search.
        It must be caller-supplied literal SQL (never built from user input) and may
        reference the bound :search parameter; this mirrors the trust model already used
        for `table`/`search_columns` throughout this repository."""
        params: dict[str, Any] = {"limit": limit + 1}
        conditions: list[str] = []
        for key, value in (filters or {}).items():
            if value is not None:
                conditions.append(f"{key} = :{key}")
                params[key] = value
        if search and (search_columns or search_extra_sql):
            search_conditions = [f"{column}::text ILIKE :search" for column in search_columns]
            if search_extra_sql:
                search_conditions.append(search_extra_sql)
            conditions.append("(" + " OR ".join(search_conditions) + ")")
            params["search"] = f"%{search}%"
        if cursor:
            payload = decode_cursor(cursor)
            conditions.append(f"({order_column}, id) > (CAST(:cursor_sort AS timestamptz), CAST(:cursor_id AS uuid))")
            params["cursor_sort"] = payload.sort_value
            params["cursor_id"] = payload.entity_id
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = self.many(
            f"""
            SELECT *
            FROM {table}
            {where}
            ORDER BY {order_column}, id
            LIMIT :limit
            """,
            params,
        )
        page = rows[:limit]
        next_cursor = None
        if len(rows) > limit and page:
            last = page[-1]
            sort_value = last.get(order_column)
            if isinstance(sort_value, datetime):
                sort_value = sort_value.isoformat()
            next_cursor = encode_cursor(CursorPayload(sort_value=str(sort_value), entity_id=last["id"]))
        return page, next_cursor, len(rows) > limit

    def insert_audit_log(
        self,
        *,
        request_id: str,
        actor_platform_user_id: UUID,
        action_key: str,
        object_schema: str,
        object_table: str,
        object_id: UUID | None,
        tenant_id: UUID | None = None,
        before_state: Mapping[str, Any] | None = None,
        after_state: Mapping[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        before_redacted = redact_mapping(before_state or {})
        after_redacted = redact_mapping(after_state or {})
        diff_state = _build_diff(before_redacted, after_redacted)
        self.session.execute(
            text(
                """
                INSERT INTO platform.audit_logs (
                  tenant_id, actor_type, actor_platform_user_id, action_key,
                  object_schema, object_table, object_id, before_state, after_state, diff_state,
                  ip_address, user_agent, request_id, occurred_at
                ) VALUES (
                  :tenant_id, 'platform_user', :actor_platform_user_id, :action_key,
                  :object_schema, :object_table, :object_id, CAST(:before_state AS jsonb),
                  CAST(:after_state AS jsonb), CAST(:diff_state AS jsonb),
                  CAST(:ip_address AS inet), :user_agent, :request_id, :occurred_at
                )
                """
            ),
            {
                "tenant_id": tenant_id,
                "actor_platform_user_id": actor_platform_user_id,
                "action_key": action_key,
                "object_schema": object_schema,
                "object_table": object_table,
                "object_id": object_id,
                "before_state": json.dumps(before_redacted, default=str),
                "after_state": json.dumps(after_redacted, default=str),
                "diff_state": json.dumps(diff_state, default=str),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_id": request_id,
                "occurred_at": datetime.now(UTC),
            },
        )

    def update_by_id(
        self,
        *,
        table: str,
        entity_id: UUID,
        values: Mapping[str, Any],
        lock_version: int | None = None,
        touch_updated_at: bool = True,
    ) -> dict[str, Any]:
        updates = clean_update_payload(values)
        if not updates:
            return self.require_by_id(table, entity_id)
        params: dict[str, Any] = {"id": entity_id}
        assignments = []
        for index, (key, value) in enumerate(updates.items()):
            param = f"value_{index}"
            assignments.append(f"{key} = :{param}")
            params[param] = value
        lock_filter = ""
        if lock_version is not None:
            lock_filter = " AND lock_version = :lock_version"
            params["lock_version"] = lock_version
        updated_at_assignment = ", updated_at = now()" if touch_updated_at else ""
        row = self.one(
            f"""
            UPDATE {table}
            SET {", ".join(assignments)}{updated_at_assignment}
            WHERE id = :id{lock_filter}
            RETURNING *
            """,
            params,
        )
        if row is None:
            raise ConflictError("Resource update conflict", safe_detail="Resource update conflict")
        return row

    def replace_child_rows(
        self,
        *,
        delete_sql: str,
        insert_sql: str,
        delete_params: Mapping[str, Any],
        rows: Sequence[Mapping[str, Any]],
    ) -> None:
        self.execute(delete_sql, delete_params)
        for row in rows:
            self.execute(insert_sql, row)


def _build_diff(before_state: Mapping[str, Any], after_state: Mapping[str, Any]) -> dict[str, Any]:
    diff: dict[str, Any] = {}
    for key in set(before_state) | set(after_state):
        if before_state.get(key) != after_state.get(key):
            diff[key] = {"before": before_state.get(key), "after": after_state.get(key)}
    return diff
