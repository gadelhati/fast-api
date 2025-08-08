from __future__ import annotations
from pydantic import BaseModel, field_validator, Field
from typing import Optional, List
from uuid import UUID

from src.validation.validations import Validation
from src.schema.basic import BaseConfig, DTOMixinAudit, DTOSoftDeleteMixin, DTOPagination
from src.schema.permission import DTOPermissionRetrieve

class DTORoleCreate(BaseModel):
    """DTO for creating a role"""
    name: str
    description: Optional[str] = None
    is_default: bool = False
    permission_ids: Optional[List[UUID]] = Field(default=None, max_length=Validation.MAX_PERMISSIONS_PER_ROLE)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        result = Validation.validate_name(v, "Role name")
        if result is None:
            raise ValueError("Role name is required")
        return result

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_name(v, "Description")

    @field_validator('permission_ids')
    @classmethod
    def validate_permission_ids(cls, v: Optional[List[UUID]]) -> Optional[List[UUID]]:
        if v is None:
            return v
        if len(v) > Validation.MAX_PERMISSIONS_PER_ROLE:
            raise ValueError(f"A role cannot have more than {Validation.MAX_PERMISSIONS_PER_ROLE} permissions")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate permissions not allowed")
        return v

    model_config = BaseConfig.model_config

class DTORoleUpdate(BaseModel):
    """DTO for updating a role"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    permission_ids: Optional[List[UUID]] = Field(default=None, max_length=Validation.MAX_PERMISSIONS_PER_ROLE)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_name(v, "Role name")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_name(v, "Description")

    @field_validator('permission_ids')
    @classmethod
    def validate_permission_ids(cls, v: Optional[List[UUID]]) -> Optional[List[UUID]]:
        if v is None:
            return v
        if len(v) > Validation.MAX_PERMISSIONS_PER_ROLE:
            raise ValueError(f"A role cannot have more than {Validation.MAX_PERMISSIONS_PER_ROLE} permissions")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate permissions not allowed")
        return v

    model_config = BaseConfig.model_config

class DTORoleRetrieve(DTOMixinAudit, DTOSoftDeleteMixin):
    """DTO for role response"""
    name: str
    description: Optional[str] = None
    is_default: bool
    permissions: List["DTOPermissionRetrieve"] = Field(default_factory=list)

class DTORoleRetrieveAll(DTOPagination):
    """DTO for role list response with pagination"""
    items: List["DTORoleRetrieve"]

# Rebuild models to resolve forward references in circular relationships
DTORoleRetrieve.model_rebuild()
DTORoleRetrieveAll.model_rebuild()