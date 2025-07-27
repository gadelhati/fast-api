from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Generic, TypeVar
from uuid import UUID
from datetime import datetime
from schema.association import DTOUserBasic, DTORoleBasic, DTOPermissionBasic

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
    
class DTOMixinAudit(BaseModel):
    """Mixin for complete audit fields in DTOs"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    version_id: int = Field(
        default=1,
        description="Registry version for concurrency control",
        examples=[1],
        ge=1
    )

    model_config = BaseConfig.model_config

class DTOSoftDeleteMixin(BaseModel):
    """Mixin for soft delete fields in DTOs"""
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    
    model_config = BaseConfig.model_config

class DTOPagination(BaseModel):
    """DTO for paginated response"""
    total: int = Field(description="Total number of items")
    page: int = Field(default=1, ge=1, description="Current page")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
    
    model_config = BaseConfig.model_config

class DTOValidationError(BaseModel):
    """DTO for validation error details"""
    field: str
    message: str
    
    model_config = BaseConfig.model_config

class DTOErrorResponse(BaseModel):
    """DTO for error response"""
    error: str
    message: str
    details: Optional[List[DTOValidationError]] = None
    
    model_config = BaseConfig.model_config

class SchemaSwagger(BaseModel):
    username: str = Field(..., unique=True, nullable=False)
    password: str = Field(..., min_length=7, max_length=255, nullable=False)

T = TypeVar('T')
	
class Response(BaseModel, Generic[T]):
    code: int
    status: str
    message: str
    result: Optional[T] = None