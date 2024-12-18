from typing import List, Union, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from fastapi import Body
from datetime import datetime

T = TypeVar('T')

class BookSchema(BaseModel):
    id: Optional[int]=None
    title: str
    description: Optional[str]=None

    class Config:
        orm_mode: True

class Role(BaseModel):
    name: str
    class Config:
        orm_mode: True

class User(BaseModel):
    username: str
    email: str
    password: str
    attempt: int # = Field(..., default=0, min_length=3, max_length=10)
    active: bool = None
    secret: Union[str, None] = None
    role: List[Role] = []
    start_datetime: datetime = Body()
    class Config:
        orm_mode: True

class Response(BaseModel, Generic[T]):
    code: int
    status: str
    message: str
    result: Optional[T] = None