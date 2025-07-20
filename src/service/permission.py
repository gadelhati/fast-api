# services/permission_service.py
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional, List

from src.model.permission import Permission
from src.schema.permission import DTOPermissionCreate, DTOPermissionUpdate, DTOPermissionResponse
from src.service.base import BaseService

class PermissionService(BaseService[Permission, DTOPermissionCreate, DTOPermissionUpdate, DTOPermissionResponse]):
    """Permission service with additional permission-specific methods"""
    
    def __init__(self, db: Session):
        super().__init__(Permission, db)
    
    def get_by_action(self, action: str, include_deleted: bool = False) -> List[DTOPermissionResponse]:
        """Get permissions by action"""
        query = self.db.query(self.model).filter(self.model.action == action)
        
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
            
        instances = query.all()
        return [self._to_response_dto(instance) for instance in instances]