from sqlalchemy import (Integer, DateTime, ForeignKey, UUID, func)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from uuid import uuid4
from typing import Optional
from uuid import UUID as PyUUID

class Base(DeclarativeBase):
	"""Base class for all models"""

	pass

class AuditMixin:
	"""Mixin for audit"""
	
	id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
	created_by: Mapped[Optional[PyUUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
	updated_by: Mapped[Optional[PyUUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
	version_id: Mapped[int] = mapped_column(Integer, default=1, nullable=False, doc="Optimistic locking version")

	__mapper_args__ = {
        "version_id_col": version_id,
        "version_id_generator": True
    }

class SoftDeleteMixin:
	"""Mixin for soft delete"""
	
	deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
	deleted_by: Mapped[Optional[PyUUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)