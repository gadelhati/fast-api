from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class GenericAuditEntity(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), default=uuid4, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), default=uuid4)
    updated_by = Column(UUID(as_uuid=True), default=uuid4)

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
    start_datetime = Column(DateTime, default=datetime.utcnow)

    # roles = relationship("Role", secondary=user_role, back_populates="users")
    roles = relationship("ModelRole", secondary=user_role)