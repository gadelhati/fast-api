from typing import List, Optional
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Boolean
from src.database import Base
from src.model.base import AuditMixin, SoftDeleteMixin
from src.model.association import user_roles, role_permissions
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from src.model.user import User
	from src.model.permission import Permission

class Role(Base, AuditMixin, SoftDeleteMixin):
	"""Role Model"""
	__tablename__ = "roles"
	
	name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
	description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
	is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, doc="Whether this role is assigned by default to new users")
	is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, doc="Whether this is a system role (cannot be deleted)")
	
	# relationships
	permissions: Mapped[List["Permission"]] = relationship(
		"Permission",
		secondary=role_permissions,
		back_populates="roles",
		order_by="Permission.name",
		doc="Permissions granted to this role"
	)
	users: Mapped[List["User"]] = relationship(
		"User",
		secondary=user_roles,
		back_populates="roles",
		order_by="User.username",
		doc="Users assigned to this role"
	)

	def __repr__(self) -> str:
		return f"<Role(name='{self.name}')>"