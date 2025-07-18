from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum
import re

class EnumPermissionAction(str, Enum):
    """Enum for permission actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

class DTOAuditMixin(BaseModel):
    """Mixin for audit fields in DTOs"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    version_id: int = Field(
        default=1,
        description="Registry version for concurrency control",
        examples=[1],
        json_schema_extra={
            "min": 1,
            "readOnly": True
        }
    )

    model_config = ConfigDict(json_encoders={UUID: str, datetime: lambda v: v.isoformat()}, from_attributes=True)
    
class DTOSoftDeleteMixin(BaseModel):
    """Mixin for logical deletion fields in DTOs"""
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(json_encoders={UUID: str, datetime: lambda v: v.isoformat()}, from_attributes=True)

class Validation:
    """Centralized validation rules"""
    USERNAME_MIN_LENGTH = 3
    PASSWORD_MIN_LENGTH = 8
    MAX_ROLES_PER_USER = 10
    MAX_PERMISSIONS_PER_ROLE = 50
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return EmailStr.validate(v)

    @staticmethod
    def validate_username(v: str) -> str:
        if len(v) < Validation.USERNAME_MIN_LENGTH:
            raise ValueError(f"Username must be at least {Validation.USERNAME_MIN_LENGTH} characters long")
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Username must contain only letters, numbers and underscores")
        return v

    @staticmethod
    def validate_password(v: str) -> str:
        if len(v) < Validation.PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {Validation.PASSWORD_MIN_LENGTH} characters")
        if not any(c.isupper() for c in v):
            raise ValueError("The password should contain at least 1 uppercase character")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    @staticmethod
    def validate_name(v: str, field_name: str) -> str:
        if len(v) < 1:
            raise ValueError(f"{field_name} is required")
        return v.strip()

class TimestampMixin(BaseModel):
    """Mixin for timestamps"""
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(json_encoders={UUID: str, datetime: lambda v: v.isoformat()}, from_attributes=True)
    
class DTOUserBasic(BaseModel):
    """Base DTO for user (used in listings and relationships)"""
    id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool

    model_config = ConfigDict(json_encoders={UUID: str}, from_attributes=True)

class DTOUserCreate(BaseModel):
    """DTO for creating a request"""
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    is_active: bool = True
    role_ids: Optional[List[UUID]] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return Validation.validate_email(v)

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
        return Validation.validate_name(v, "first name")

    @field_validator('last_name')
    @classmethod
    def validate_last_name(cls, v: str) -> str:
        return Validation.validate_name(v, "last name")
    
    model_config = ConfigDict(json_encoders={UUID: str})

class DTOUserUpdate(BaseModel):
    """DTO for updating a request"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    role_ids: Optional[List[UUID]] = None

    @field_validator('email', mode='before')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_email(v) if v else None

    @field_validator('first_name', mode='before')
    @classmethod
    def validate_first_name(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_name(v, "first name")

    @field_validator('last_name', mode='before')
    @classmethod
    def validate_last_name(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_name(v, "last name")
    
    @field_validator('role_ids')
    @classmethod
    def validate_roles(cls, v: Optional[List[UUID]]) -> Optional[List[UUID]]:
        if v and len(v) > Validation.MAX_ROLES_PER_USER:
            raise ValueError(f"A user cannot have more than {Validation.MAX_ROLES_PER_USER} roles")
        if v and len(v) != len(set(v)):
            raise ValueError("Duplicate roles not allowed")
        return v

    model_config = ConfigDict(json_encoders={UUID: str})
        
class DTOUserResponse(DTOAuditMixin, DTOSoftDeleteMixin):
    """DTO to response to a request"""
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    roles: List['DTORoleBasic'] = []
    
class DTORoleBasic(BaseModel):
    """Base DTO for role (used in listings and relationships)"""
    id: UUID
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(json_encoders={UUID: str}, from_attributes=True)

class DTORoleCreate(BaseModel):
    """DTO for creating a role"""
    name: str
    description: Optional[str] = None
    is_default: bool = False
    permission_ids: Optional[List[UUID]] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return Validation.validate_name(v, "role name")

    @field_validator('permission_ids')
    @classmethod
    def validate_permissions_ids(cls, v: Optional[List[UUID]]) -> Optional[List[UUID]]:
        if not v:
            return v
        if v and len(v) > Validation.MAX_PERMISSIONS_PER_ROLE:
            raise ValueError(f"A role cannot have more than {Validation.MAX_PERMISSIONS_PER_ROLE} permissions")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate permissions not allowed")
        return v

    model_config = ConfigDict(json_encoders={UUID: str})

class DTORoleUpdate(BaseModel):
    """DTO for updating a role"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    permission_ids: Optional[List[UUID]] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_name(v, "role name") if v else None

    @field_validator('permission_ids')
    @classmethod
    def validate_permissions_ids(cls, v: Optional[List[UUID]]) -> Optional[List[UUID]]:
        if v and len(v) > Validation.MAX_PERMISSIONS_PER_ROLE:
            raise ValueError(f"A role cannot have more than {Validation.MAX_PERMISSIONS_PER_ROLE} roles")
        return v

    model_config = ConfigDict(json_encoders={UUID: str})

class DTORoleResponse(DTOAuditMixin, DTOSoftDeleteMixin):
    """DTO para resposta de um papel"""
    name: str
    description: Optional[str] = None
    is_default: bool
    permissions: List['DTOPermissionBasic'] = []
    users: List['DTOUserBasic'] = []

class DTOPermissionBasic(BaseModel):
    """Basic DTO for permission (used in listings and relationships)"""
    id: UUID
    name: str
    action: EnumPermissionAction
    
    model_config = ConfigDict(json_encoders={UUID: str}, from_attributes=True)
    
class DTOPermissionCreate(BaseModel):
    """DTO for creating a permission"""
    name: str
    description: Optional[str] = None
    action: EnumPermissionAction

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return Validation.validate_name(v, "permission name")

    model_config = ConfigDict(json_encoders={UUID: str})

class DTOPermissionUpdate(BaseModel):
    """DTO for updating a permission"""
    name: Optional[str] = None
    description: Optional[str] = None
    action: Optional[EnumPermissionAction] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        return Validation.validate_name(v, "permission name") if v else None

    model_config = ConfigDict(json_encoders={UUID: str})

class DTOPermissionResponse(DTOAuditMixin, DTOSoftDeleteMixin):
    """DTO to response to a request"""
    name: str
    description: Optional[str] = None
    action: EnumPermissionAction
    roles: List[DTORoleBasic] = []
    
class DTOLogin(BaseModel):
    """DTO for login"""
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < Validation.USERNAME_MIN_LENGTH:
            raise ValueError(f"Username or email must be at least {Validation.USERNAME_MIN_LENGTH} characters")
        return v.strip()

class DTOToken(BaseModel):
    """DTO for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: DTOUserBasic

class DTOPasswordReset(BaseModel):
    """DTO for password reset"""
    email: EmailStr

class DTOPasswordResetConfirm(BaseModel):
    """DTO for password reset confirmation"""
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return Validation.validate_password(v)

# Rebuild models to resolve forward references in circular relationships
DTOUserUpdate.model_rebuild()
DTOUserResponse.model_rebuild()
DTORoleBasic.model_rebuild()
DTORoleUpdate.model_rebuild()
DTORoleResponse.model_rebuild()
DTOPermissionBasic.model_rebuild()
DTOPermissionResponse.model_rebuild()