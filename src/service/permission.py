from sqlalchemy.orm import Session
from typing import List
from src.model.permission import Permission
from src.schema.permission import DTOPermissionCreate, DTOPermissionUpdate, DTOPermissionRetrieve
from src.service.basic import ServiceBase

class ServicePermission(ServiceBase[Permission, DTOPermissionCreate, DTOPermissionUpdate, DTOPermissionRetrieve]):
    """Permission service with additional permission-specific methods"""
    
    def __init__(self, db: Session):
        super().__init__(Permission, db)
    
    def get_by_action(self, action: str, include_deleted: bool = False) -> List[DTOPermissionRetrieve]:
        """Get permissions by action"""
        query = self.db.query(self.model).filter(self.model.action == action)
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        instances = query.all()
        return [self._to_response_dto(instance) for instance in instances]