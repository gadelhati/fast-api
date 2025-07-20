from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from src.schema.base import BaseConfig, DTOAuditMixin, DTOSoftDeleteMixin
from src.schema.base_basic import DTORoleBasic
from src.validation.validations import Validation

class DTOUserCreate(BaseModel):
    """DTO for creating a user"""
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    is_active: bool = True
    role_ids: Optional[List[UUID]] = Field(default=None, max_length=Validation.MAX_ROLES_PER_USER)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        return Validation.validate_username(v)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return Validation.validate_password(v)

    @field_validator('first_name')
    @classmethod
    def validate_first_name(cls, v: str) -> str:
        result = Validation.validate_name(v, "First name")
        if result is None:
            raise ValueError("First name is required")
        return result

    @field_validator('last_name')
    @classmethod
    def validate_last_name(cls, v: str) -> str:
        result = Validation.validate_name(v, "Last name")
        if result is None:
            raise ValueError("Last name is required")
        return result
    
    @field_validator('role_ids')
    @classmethod
    def validate_role_ids(cls, v: Optional[List[UUID]]) -> Optional[List[UUID]]:
        if v is None:
            return v
        if len(v) > Validation.MAX_ROLES_PER_USER:
            raise ValueError(f"A user cannot have more than {Validation.MAX_ROLES_PER_USER} roles")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate roles not allowed")
        return v

    model_config = BaseConfig.model_config

class DTOUserUpdate(BaseModel):
    """DTO for updating a user"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    role_ids: Optional[List[UUID]] = Field(default=None, max_length=Validation.MAX_ROLES_PER_USER)

    @field_validator('first_name')
    @classmethod
    def validate_first_name(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_name(v, "First name")

    @field_validator('last_name')
    @classmethod
    def validate_last_name(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_name(v, "Last name")
    
    @field_validator('role_ids')
    @classmethod
    def validate_role_ids(cls, v: Optional[List[UUID]]) -> Optional[List[UUID]]:
        if v is None:
            return v
        if len(v) > Validation.MAX_ROLES_PER_USER:
            raise ValueError(f"A user cannot have more than {Validation.MAX_ROLES_PER_USER} roles")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate roles not allowed")
        return v

    model_config = BaseConfig.model_config

class DTOUserResponse(DTOAuditMixin, DTOSoftDeleteMixin):
    """DTO for user response"""
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    roles: List['DTORoleBasic'] = Field(default_factory=list)

# Rebuild models to resolve forward references in circular relationships
DTOUserResponse.model_rebuild()