from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from src.validation.validations import Validation
from src.schema.basic import BaseConfig, DTOMixinAudit, DTOSoftDeleteMixin, DTOPagination
from src.schema.role import DTORoleRetrieve

class DTOUserCreate(BaseModel):
    """DTO for creating a user"""
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
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
    def validate_role_ids(cls, v: List[UUID]) -> List[UUID]:
        if len(v) > Validation.MAX_ROLES_PER_USER:
            raise ValueError(f"A user cannot have more than {Validation.MAX_ROLES_PER_USER} roles")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate roles not allowed")
        return v

    model_config = BaseConfig.model_config

class DTOUserUpdate(BaseModel):
    """DTO for updating a user"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    role_ids: Optional[List[UUID]] = Field(default=None, max_length=Validation.MAX_ROLES_PER_USER)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_username(v)

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
    def validate_role_ids(cls, v: List[UUID]) -> List[UUID]:
        if len(v) > Validation.MAX_ROLES_PER_USER:
            raise ValueError(f"A user cannot have more than {Validation.MAX_ROLES_PER_USER} roles")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate roles not allowed")
        return v

    model_config = BaseConfig.model_config

class DTOUserRetrieve(DTOMixinAudit, DTOSoftDeleteMixin):
    """DTO for user response"""
    id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    roles: List["DTORoleRetrieve"] = Field(default_factory=list)

class DTOUserRoleUpdate(BaseModel):
    """DTO for updating only user roles"""
    role_ids: List[UUID] = Field(..., max_length=Validation.MAX_ROLES_PER_USER)

    @field_validator('role_ids')
    @classmethod
    def validate_role_ids(cls, v: List[UUID]) -> List[UUID]:
        if len(v) > Validation.MAX_ROLES_PER_USER:
            raise ValueError(f"A user cannot have more than {Validation.MAX_ROLES_PER_USER} roles")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate roles not allowed")
        return v

    model_config = BaseConfig.model_config

class DTOPasswordUpdate(BaseModel):
    """DTO for updating only user password"""
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return Validation.validate_password(v)

    model_config = BaseConfig.model_config

class DTOUserRetrieveAll(DTOPagination):
    """DTO for user list response with pagination"""
    items: List['DTOUserRetrieve']

# Rebuild models to resolve forward references in circular relationships
DTOUserRetrieve.model_rebuild()
DTOUserRetrieveAll.model_rebuild()