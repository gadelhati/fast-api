from sqlalchemy.orm import Session
from typing import List
from src.model.permission import Permission
from src.schema.permission import DTOPermissionRetrieve
from src.service.basic import ServiceBase
from src.enum.permissionAction import EnumPermissionAction

class ServicePermission(ServiceBase[Permission, None, None, DTOPermissionRetrieve]):
    """Permission service (read-only)"""
    
    def __init__(self, db: Session):
        super().__init__(Permission, db, DTOPermissionRetrieve)
    
    def get_by_action(self, action: EnumPermissionAction, include_deleted: bool = False) -> List[DTOPermissionRetrieve]:
        """Get permissions by enum action"""
        query = self.db.query(self.model).filter(self.model.action == action.value)
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        return [self._to_response_dto(instance) for instance in query.all()]
    
    def sync_with_enum(self) -> None:
        """Ensure all enum values exist in the DB (idempotent)."""
        existing_actions = {p.action for p in self.db.query(self.model).all()}
        for action in EnumPermissionAction:
            if action.value not in existing_actions:
                self.db.add(Permission(action=action.value))
        self.db.commit()