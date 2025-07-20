from typing import List, Optional
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Enum
from src.database import Base
from src.model.base import AuditMixin, SoftDeleteMixin
from src.enum.permissionAction import EnumPermissionAction
from src.model.association import role_permissions
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from src.model.role import Role

class Permission(Base, AuditMixin, SoftDeleteMixin):
	"""Permission model"""
	__tablename__ = "permissions"
	
	name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
	description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

	action: Mapped[EnumPermissionAction] = mapped_column(
        Enum(EnumPermissionAction, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        doc="Action type for this permission"
    )
	
	# relationships
	roles: Mapped[List["Role"]] = relationship(
		"Role",
		secondary=role_permissions,
		back_populates="permissions",
		order_by="Role.name",
        doc="Roles that have this permission"
	)

	def __repr__(self) -> str:
		return f"<Permission(name='{self.name}', action='{self.action.value}')>"