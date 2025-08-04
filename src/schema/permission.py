from pydantic import Field
from typing import Optional, List
from uuid import UUID
from src.enum.permissionAction import EnumPermissionAction
from src.schema.basic import DTOMixinAudit, DTOSoftDeleteMixin, DTOPagination
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.schema.role import DTORoleRetrieve
DTORoleRetrieve = None

class DTOPermissionRetrieve(DTOMixinAudit, DTOSoftDeleteMixin):
    """DTO for permission response"""
    id: UUID
    name: str
    description: Optional[str] = None
    action: EnumPermissionAction
    roles: List['DTORoleRetrieve'] = Field(default_factory=list)

class DTOPermissionRetrieveAll(DTOPagination):
    """DTO for permission list response with pagination"""
    items: List['DTOPermissionRetrieve']

# Rebuild models to resolve forward references in circular relationships
DTOPermissionRetrieve.model_rebuild()
DTOPermissionRetrieveAll.model_rebuild()