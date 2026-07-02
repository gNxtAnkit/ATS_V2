from __future__ import annotations

import logging
import json
from collections.abc import Mapping
from typing import Any

from gnxthire_common.context import RequestContext


SENSITIVE_KEY_PARTS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "session",
)
REDACTED_VALUE = "[REDACTED]"


def is_sensitive_key(key: str) -> bool:
    normalized_key = key.lower()
    return any(part in normalized_key for part in SENSITIVE_KEY_PARTS)


def redact_mapping(values: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in values.items():
        if is_sensitive_key(key):
            redacted[key] = REDACTED_VALUE
        elif isinstance(value, Mapping):
            redacted[key] = redact_mapping(value)
        elif isinstance(value, list):
            redacted[key] = [
                redact_mapping(item) if isinstance(item, Mapping) else item for item in value
            ]
        else:
            redacted[key] = value
    return redacted


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "structured", None)
        if isinstance(extra, Mapping):
            payload.update(redact_mapping(extra))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_logging(level: int = logging.INFO, *, json_logs: bool = True) -> None:
    handlers: list[logging.Handler] | None = None
    if json_logs:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        handlers = [handler]
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=handlers,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def context_log_fields(context: RequestContext) -> dict[str, Any]:
    return {
        "request_id": context.request_id,
        "correlation_id": context.effective_correlation_id,
        "tenant_id": context.tenant_id,
        "actor_id": context.actor_id,
        "actor_type": context.actor_type,
        "is_platform_admin": context.is_platform_admin,
        "platform_admin_id": context.platform_admin_id,
    }


def log_extra(values: Mapping[str, Any]) -> dict[str, Any]:
    return {"structured": redact_mapping(values)}
