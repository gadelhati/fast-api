from sqlalchemy import Column, ForeignKey, DateTime, Table, func
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base
from datetime import datetime, timezone

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now()),
    Column("created_by", UUID(as_uuid=True), nullable=True)
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now()),
    Column("created_by", UUID(as_uuid=True), nullable=True)
)