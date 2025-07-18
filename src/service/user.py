# services/user_service.py
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional, List

from model import User
from schema import DTOUserCreate, DTOUserUpdate, DTOUserResponse
from src.service.base import BaseService

class UserService(BaseService[User, DTOUserCreate, DTOUserUpdate, DTOUserResponse]):
    """User service with additional user-specific methods"""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[DTOUserResponse]:
        """Get user by email"""
        query = self.db.query(self.model).filter(self.model.email == email)
        
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
            
        instance = query.first()
        return self._to_response_dto(instance) if instance else None
    
    def get_by_username(self, username: str, include_deleted: bool = False) -> Optional[DTOUserResponse]:
        """Get user by username"""
        query = self.db.query(self.model).filter(self.model.username == username)
        
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
            
        instance = query.first()
        return self._to_response_dto(instance) if instance else None
    
    def update_roles(self, user_id: UUID, role_ids: List[UUID], current_user_id: Optional[UUID] = None) -> DTOUserResponse:
        """Update user roles"""
        from model import Role
        from schema import Validation
        
        if len(role_ids) > Validation.MAX_ROLES_PER_USER:
            raise ValidationError(
                message=f"A user cannot have more than {Validation.MAX_ROLES_PER_USER} roles",
                errors={"role_ids": "Too many roles"}
            )
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(resource_name="User", resource_id=user_id)
            
        roles = self.db.query(Role).filter(Role.id.in_(role_ids)).all()
        if len(roles) != len(role_ids):
            found_ids = {str(role.id) for role in roles}
            missing_ids = [str(rid) for rid in role_ids if rid not in found_ids]
            raise NotFoundError(
                message=f"Some roles not found: {', '.join(missing_ids)}",
                code="roles_not_found"
            )
            
        try:
            user.roles = roles
            if hasattr(user, 'updated_by'):
                user.updated_by = current_user_id
                
            self.db.commit()
            self.db.refresh(user)
            return self._to_response_dto(user)
            
        except Exception as e:
            self.db.rollback()
            raise ServiceException(f"Error updating user roles: {str(e)}")
    
    def set_password(self, user_id: UUID, password_hash: str, current_user_id: Optional[UUID] = None) -> bool:
        """Set user password hash"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(resource_name="User", resource_id=user_id)
            
        try:
            user._password_hash = password_hash
            if hasattr(user, 'updated_by'):
                user.updated_by = current_user_id
                
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise ServiceException(f"Error setting password: {str(e)}")