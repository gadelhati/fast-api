from typing import List, Optional
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String
from src.database import Base
from src.model.mixin import AuditMixin, SoftDeleteMixin
from src.model.association import role_permissions
from src.model.role import Role

class Permission(Base, AuditMixin, SoftDeleteMixin):
    """Permissões específicas do sistema"""
    __tablename__ = "permissions"
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)  # ex: "users", "roles", "reports"
    action: Mapped[str] = mapped_column(String(20), nullable=False)    # ex: "create", "read", "update", "delete"
    
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        order_by="Role.name"
    )