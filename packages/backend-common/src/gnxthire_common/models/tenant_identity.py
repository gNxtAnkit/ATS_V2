from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime, String

from gnxthire_common.models.base import (
    Base,
    OptimisticLockMixin,
    SoftDeleteMixin,
    TenantScopedMixin,
    TimestampMixin,
    UuidPrimaryKeyMixin,
)


class BusinessUnit(
    Base,
    TenantScopedMixin,
    UuidPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
):
    __tablename__ = "business_units"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_business_units_tenant_id"),
        UniqueConstraint("tenant_id", "code", name="uq_business_units_tenant_code"),
        ForeignKeyConstraint(["tenant_id"], ["platform.tenants.id"], name="fk_business_units_tenant"),
        ForeignKeyConstraint(
            ["tenant_id", "parent_business_unit_id"],
            ["tenant.business_units.tenant_id", "tenant.business_units.id"],
            name="fk_business_units_parent",
        ),
        {"schema": "tenant"},
    )

    parent_business_unit_id: Mapped[UUID | None] = mapped_column()
    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    cost_center: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")


class User(
    Base,
    TenantScopedMixin,
    UuidPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_users_tenant_id"),
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        ForeignKeyConstraint(["tenant_id"], ["platform.tenants.id"], name="fk_users_tenant"),
        ForeignKeyConstraint(
            ["tenant_id", "business_unit_id"],
            ["tenant.business_units.tenant_id", "tenant.business_units.id"],
            name="fk_users_business_unit",
        ),
        {"schema": "tenant"},
    )

    business_unit_id: Mapped[UUID | None] = mapped_column()
    email: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    given_name: Mapped[str | None] = mapped_column(String)
    family_name: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="invited")
    provisioning_source: Mapped[str] = mapped_column(String, nullable=False, default="manual")
    is_tenant_admin: Mapped[bool] = mapped_column(nullable=False, default=False)
    password_hash: Mapped[str | None] = mapped_column(String)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Role(
    Base,
    TenantScopedMixin,
    UuidPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    OptimisticLockMixin,
):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_roles_tenant_id"),
        UniqueConstraint("tenant_id", "role_key", name="uq_roles_tenant_key"),
        ForeignKeyConstraint(["tenant_id"], ["platform.tenants.id"], name="fk_roles_tenant"),
        {"schema": "tenant"},
    )

    role_key: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    is_system_role: Mapped[bool] = mapped_column(nullable=False, default=False)


class Permission(Base, TenantScopedMixin, UuidPrimaryKeyMixin):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_permissions_tenant_id"),
        UniqueConstraint("tenant_id", "permission_key", name="uq_permissions_tenant_key"),
        ForeignKeyConstraint(["tenant_id"], ["platform.tenants.id"], name="fk_permissions_tenant"),
        {"schema": "tenant"},
    )

    permission_key: Mapped[str] = mapped_column(String, nullable=False)
    resource_key: Mapped[str] = mapped_column(String, nullable=False)
    action_key: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
