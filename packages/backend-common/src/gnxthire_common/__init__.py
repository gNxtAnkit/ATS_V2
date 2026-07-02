"""Shared backend foundations for gNxtHire services."""

from gnxthire_common.config import Settings, get_settings
from gnxthire_common.context import ActorType, RequestContext
from gnxthire_common.health import AppHealthResult, HealthCheckResult, HealthStatus
from gnxthire_common.service_info import ServiceInfo, build_service_info

__all__ = [
    "ActorType",
    "AppHealthResult",
    "HealthCheckResult",
    "HealthStatus",
    "RequestContext",
    "ServiceInfo",
    "Settings",
    "build_service_info",
    "get_settings",
]
