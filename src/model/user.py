from typing import List, Optional
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, Integer
from datetime import datetime
from src.database import Base
from model.basic import MixinAudit, MixinSoftDelete
from src.model.association import user_roles
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from src.model.role import Role

class User(Base, MixinAudit, MixinSoftDelete):
	"""User Model"""
	__tablename__ = "users"
	
	username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
	email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
	_password_hash: Mapped[str] = mapped_column(String(255), nullable=False)	
	first_name: Mapped[str] = mapped_column(String(100), nullable=False)
	last_name: Mapped[str] = mapped_column(String(100), nullable=False)
	
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True, doc="Whether user account is active")
	is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, doc="Whether user email is verified")
	last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, doc="Last successful login timestamp")
	failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="Count of consecutive failed login attempts")
	locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, doc="Account lock expiration timestamp")
	
	# relationships
	roles: Mapped[List["Role"]] = relationship(
		"Role",
		secondary=user_roles,
		back_populates="users",
		order_by="Role.name",
        doc="Roles assigned to the user"
	)

	def __repr__(self) -> str:
		return f"<User(username='{self.username}', email='{self.email}')>"