from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from src.enum.permissionAction import EnumPermissionAction

# Base configuration for all models
class BaseConfig:
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat() if v else None
        },
        str_strip_whitespace=True,
        validate_assignment=True
    )

class DTOUserBasic(BaseModel):
    """Base DTO for user (used in listings and relationships)"""
    id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool

    model_config = BaseConfig.model_config

class DTORoleBasic(BaseModel):
    """Base DTO for role (used in listings and relationships)"""
    id: UUID
    name: str
    description: Optional[str] = None
    is_default: bool = False

    model_config = BaseConfig.model_config

class DTOPermissionBasic(BaseModel):
    """Basic DTO for permission (used in listings and relationships)"""
    id: UUID
    name: str
    description: Optional[str] = None
    action: EnumPermissionAction
    
    model_config = BaseConfig.model_config

# Rebuild models to resolve forward references in circular relationships
DTOUserBasic.model_rebuild()
DTORoleBasic.model_rebuild()
DTOPermissionBasic.model_rebuild()