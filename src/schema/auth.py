from __future__ import annotations
from pydantic import BaseModel, EmailStr, field_validator, Field
from src.validation.validations import Validation

from src.schema.basic import BaseConfig
from src.schema.user import DTOUserRetrieve

class DTOLogin(BaseModel):
    """DTO for login"""
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < Validation.USERNAME_MIN_LENGTH:
            raise ValueError(f"Username or email must be at least {Validation.USERNAME_MIN_LENGTH} characters")
        return v

    model_config = BaseConfig.model_config

class DTOToken(BaseModel):
    """DTO for token response"""
    access_token: str
    token_type: str = "bearer"
    refreshToken: str
    expires_in: int
    user: "DTOUserRetrieve"

    model_config = BaseConfig.model_config

class DTOPasswordReset(BaseModel):
    """DTO for password reset request"""
    email: EmailStr

    model_config = BaseConfig.model_config

class DTOPasswordResetConfirm(BaseModel):
    """DTO for password reset confirmation"""
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return Validation.validate_password(v)

    model_config = BaseConfig.model_config

# Rebuild models to resolve forward references in circular relationships
DTOToken.model_rebuild()