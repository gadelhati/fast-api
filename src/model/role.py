from typing import List, Optional
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Boolean
from src.database import Base
from src.model.mixin import AuditMixin, SoftDeleteMixin
from src.model.association import user_roles, role_permissions
from src.model.user import User
from src.model.permission import Permission

class Role(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "roles"
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
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
        order_by="User.name"
    )