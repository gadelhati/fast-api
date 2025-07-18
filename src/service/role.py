# services/role_service.py
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional, List

from model import Role
from schema import DTORoleCreate, DTORoleUpdate, DTORoleResponse
from services.base_service import BaseService

class RoleService(BaseService[Role, DTORoleCreate, DTORoleUpdate, DTORoleResponse]):
    """Role service with additional role-specific methods"""
    
    def __init__(self, db: Session):
        super().__init__(Role, db)
    
    def get_default_roles(self, include_deleted: bool = False) -> List[DTORoleResponse]:
        """Get all default roles"""
        query = self.db.query(self.model).filter(self.model.is_default == True)
        
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
            
        instances = query.all()
        return [self._to_response_dto(instance) for instance in instances]
    
    def update_permissions(
        self, 
        role_id: UUID, 
        permission_ids: List[UUID], 
        current_user_id: Optional[UUID] = None
    ) -> DTORoleResponse:
        """Update role permissions"""
        from model import Permission
        from schema import Validation
        
        if len(permission_ids) > Validation.MAX_PERMISSIONS_PER_ROLE:
            raise ValidationError(
                message=f"A role cannot have more than {Validation.MAX_PERMISSIONS_PER_ROLE} permissions",
                errors={"permission_ids": "Too many permissions"}
            )
        
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFoundError(resource_name="Role", resource_id=role_id)
            
        permissions = self.db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        if len(permissions) != len(permission_ids):
            found_ids = {str(perm.id) for perm in permissions}
            missing_ids = [str(pid) for pid in permission_ids if pid not in found_ids]
            raise NotFoundError(
                message=f"Some permissions not found: {', '.join(missing_ids)}",
                code="permissions_not_found"
            )
            
        try:
            role.permissions = permissions
            if hasattr(role, 'updated_by'):
                role.updated_by = current_user_id
                
            self.db.commit()
            self.db.refresh(role)
            return self._to_response_dto(role)
            
        except Exception as e:
            self.db.rollback()
            raise ServiceException(f"Error updating role permissions: {str(e)}")