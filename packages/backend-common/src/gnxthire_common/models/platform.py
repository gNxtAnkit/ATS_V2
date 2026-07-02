from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime, Integer, Numeric, String

from gnxthire_common.models.base import (
    Base,
    OptimisticLockMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UuidPrimaryKeyMixin,
)


class Plan(Base, UuidPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, OptimisticLockMixin):
    __tablename__ = "plans"
    __table_args__ = (
        UniqueConstraint("code", name="uq_plans_code"),
        {"schema": "platform"},
    )

    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    billing_interval: Mapped[str] = mapped_column(String, nullable=False)
    base_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    min_seats: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_seats: Mapped[int | None] = mapped_column(Integer)
    trial_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Tenant(Base, UuidPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, OptimisticLockMixin):
    __tablename__ = "tenants"
    __table_args__ = (
        UniqueConstraint("id", name="uq_tenants_id"),
        {"schema": "platform"},
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    legal_entity_name: Mapped[str | None] = mapped_column(String)
    tenant_type: Mapped[str] = mapped_column(String, nullable=False)
    primary_admin_email: Mapped[str] = mapped_column(String, nullable=False)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("platform.plans.id"))
    status: Mapped[str] = mapped_column(String, nullable=False, default="provisioning")
    isolation_tier: Mapped[str] = mapped_column(String, nullable=False, default="shared")
    region: Mapped[str] = mapped_column(String, nullable=False, default="US")
    data_residency_zone: Mapped[str | None] = mapped_column(String)
    infra_pool_id: Mapped[UUID | None] = mapped_column(ForeignKey("platform.infra_pools.id"))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    churned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
