from __future__ import annotations
from typing import Optional, List
from uuid import UUID

from src.enum.permissionAction import EnumPermissionAction
from src.schema.basic import DTOMixinAudit, DTOSoftDeleteMixin, DTOPagination

class DTOPermissionRetrieve(DTOMixinAudit, DTOSoftDeleteMixin):
    """DTO for permission response"""
    name: str
    description: Optional[str] = None
    action: EnumPermissionAction

class DTOPermissionRetrieveAll(DTOPagination):
    """DTO for permission list response with pagination"""
    items: List["DTOPermissionRetrieve"]

# Rebuild models to resolve forward references in circular relationships
DTOPermissionRetrieve.model_rebuild()
DTOPermissionRetrieveAll.model_rebuild()