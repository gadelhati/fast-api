from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Table, 
    ForeignKey, UUID, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, List
from uuid import UUID as PyUUID
from schema.schema import EnumPermissionAction
from enum import Enum

# model validations:
#    required fields(nullable=False),
#    unicidade(unique=True),
#    maximum string length(String(N)),
#    data types(UUID, DateTime, etc.)

class Base(DeclarativeBase):
    pass

class AuditMixin:
	"""Mixin for audit"""
	
	id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now())
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc))
	created_by: Mapped[Optional[PyUUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
	updated_by: Mapped[Optional[PyUUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
	version_id: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

	__mapper_args__ = {
        "version_id_col": version_id,
        "version_id_generator": False
    }

class SoftDeleteMixin:
	"""Mixin for soft delete"""
	
	deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
	deleted_by: Mapped[Optional[PyUUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

user_roles = Table(
	"user_roles",
	Base.metadata,
	Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
	Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
)

role_permissions = Table(
	"role_permissions",
	Base.metadata,
	Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
	Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)
)

class User(Base, AuditMixin, SoftDeleteMixin):
	"""User Model"""
	__tablename__ = "users"
	
	email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
	username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
	_password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
	
	first_name: Mapped[str] = mapped_column(String(100), nullable=False)
	last_name: Mapped[str] = mapped_column(String(100), nullable=False)
	
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
	is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
	
	last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, doc="Last login")
	failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Count of failed login attempts")
	locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, doc="Account blocking date")
	
	# relationships
	roles: Mapped[List["Role"]] = relationship(
		"Role",
		secondary=user_roles,
		back_populates="users",
		order_by="Role.name",
        doc="Roles assigned to the user"
	)

class Role(Base, AuditMixin, SoftDeleteMixin):
	"""Role Model"""
	__tablename__ = "roles"
	
	name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
	description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
	is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
	
	# relationships
	permissions: Mapped[List["Permission"]] = relationship(
		"Permission",
		secondary=role_permissions,
		back_populates="roles",
		order_by="Permission.name"
	)
	users: Mapped[List["User"]] = relationship(
		"User",
		secondary=user_roles,
		back_populates="roles",
		order_by="User.username"
	)

class Permission(Base, AuditMixin, SoftDeleteMixin):
	"""Permission model"""
	__tablename__ = "permissions"
	
	name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
	description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

	action: Mapped[EnumPermissionAction] = mapped_column(
        Enum(EnumPermissionAction, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
	
	# relationships
	roles: Mapped[List["Role"]] = relationship(
		"Role",
		secondary=role_permissions,
		back_populates="permissions",
		order_by="Role.name"
	)