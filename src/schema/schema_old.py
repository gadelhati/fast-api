from typing import List, Union, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime
from fastapi import Body
from uuid import UUID, uuid4

T = TypeVar('T')

class SchemaBook(BaseModel):
    id: Optional[UUID]=Field(default_factory=uuid4)
    title: str
    description: Optional[str]=None
    class Config:
        orm_mode: True

class SchemaRole(BaseModel):
    id: Optional[UUID]=Field(default_factory=uuid4)
    name: str
    class Config:
        orm_mode: True

class SchemaUser(BaseModel):
    id: Optional[UUID]=Field(default_factory=uuid4)
    username: str = Field(..., unique=True, nullable=False)
    email: str = Field(..., unique=True, nullable=False)
    password: str = Field(..., min_length=7, max_length=255)
    attempt: int = Field(default=0, ge=0, le=10)
    active: bool = Field(default=True)
    secret: Union[str, None] = None
    role: List[SchemaRole] = []
    start_datetime: Optional[datetime] = Body(default=None)
    class Config:
        orm_mode: True

class SchemaSwagger(BaseModel):
    username: str = Field(..., unique=True, nullable=False)
    password: str = Field(..., min_length=7, max_length=255, nullable=False)

class SchemaToken(BaseModel):
    tokenType: str = 'Bearer '
    accessToken: str
    refreshToken: str
    roles: List[SchemaRole] = []
    class Config:
        orm_mode: True
    
class Response(BaseModel, Generic[T]):
    code: int
    status: str
    message: str
    result: Optional[T] = None