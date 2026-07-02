from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    """Canonical event envelope shape placeholder.

    TODO(Phase 10 - Events Service): Replace with the versioned event contract and outbox writer.
    """

    event_type: str = Field(min_length=1)
    event_version: str = Field(default="0.0")
    request_id: str | None = None
    tenant_id: str | None = None
