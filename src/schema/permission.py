from pydantic import BaseModel, field_validator, Field
from typing import Optional, List
from uuid import UUID
from src.enum.permissionAction import EnumPermissionAction
from src.validation.validations import Validation
from src.schema.basic import BaseConfig, DTOMixinAudit, DTOSoftDeleteMixin, DTOPagination
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.schema.role import DTORoleRetrieve
DTORoleRetrieve = None

class DTOPermissionCreate(BaseModel):
    """DTO for creating a permission"""
    name: str
    description: Optional[str] = None
    action: EnumPermissionAction

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        result = Validation.validate_name(v, "Permission name")
        if result is None:
            raise ValueError("Permission name is required")
        return result

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_name(v, "Description")

    model_config = BaseConfig.model_config

class DTOPermissionUpdate(BaseModel):
    """DTO for updating a permission"""
    name: Optional[str] = None
    description: Optional[str] = None
    action: Optional[EnumPermissionAction] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_name(v, "Permission name")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_name(v, "Description")

    model_config = BaseConfig.model_config

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