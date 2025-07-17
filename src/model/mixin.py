from typing import Any, Dict, Generic, List, Optional, Sequence, Tuple, Type, TypeVar, Union, overload
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column, Session, InstrumentedAttribute
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base
from datetime import datetime, timezone
from uuid import UUID as PyUUID, uuid4
import sqlalchemy as sa

class Base(DeclarativeBase):
    pass

class AuditMixin:
    id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=sa.func.now(), onupdate=lambda: datetime.now(timezone.utc))
    created_by: Mapped[Optional[PyUUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[PyUUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[Optional[PyUUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

class ModelBook(GenericAuditEntity):
    __tablename__ = "book"
    title = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)

user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("role.id"), primary_key=True)
)

class ModelRole(GenericAuditEntity):
    __tablename__ = "role"
    name = Column(String(50), nullable=False)
    # user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    
class ModelUser(GenericAuditEntity):
    __tablename__ = "user"
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(35), nullable=False)
    attempt = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    secret = Column(String(150))
    start_datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # roles = relationship("Role", secondary=user_role, back_populates="users")
    roles = relationship("ModelRole", secondary=user_role)