from pydantic import BaseModel, field_validator, Field
from typing import Optional, List
from uuid import UUID
from src.enum.permissionAction import EnumPermissionAction
from src.schema.base import BaseConfig, DTOAuditMixin, DTOSoftDeleteMixin
from src.schema.base_basic import DTORoleBasic
from src.validation.validations import Validation

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

class DTOPermissionResponse(DTOAuditMixin, DTOSoftDeleteMixin):
    """DTO for permission response"""
    name: str
    description: Optional[str] = None
    action: EnumPermissionAction
    roles: List[DTORoleBasic] = Field(default_factory=list)

# Rebuild models to resolve forward references in circular relationships
DTOPermissionResponse.model_rebuild()