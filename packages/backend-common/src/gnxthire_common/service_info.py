from __future__ import annotations

from pydantic import BaseModel, Field

from gnxthire_common.config import get_settings


class ServiceInfo(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    environment: str = Field(min_length=1)


def build_service_info(default_service_name: str) -> ServiceInfo:
    settings = get_settings()
    service_name = settings.service_name
    if service_name == "service-shell":
        service_name = default_service_name
    return ServiceInfo(
        name=service_name,
        version=settings.version,
        environment=settings.environment,
    )
