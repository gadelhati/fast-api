from fastapi import Body
from datetime import datetime
from pydantic import BaseModel
from typing import List, Union

class Role(BaseModel):
    name: str

class User(BaseModel):
    username: str
    email: str
    password: str
    attempt: int
    active: bool = None
    secret: Union[str, None] = None
    role: List[Role] = []
    start_datetime: datetime = Body()