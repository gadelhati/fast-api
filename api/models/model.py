from sqlalchemy import Column, Integer, String, Boolean
from api.database import Base

class Book(Base):
    __tablename__ = "book"

    id=Column(Integer, primary_key=True, index=True)
    title=Column(String(50), nullable=False)
    description=Column(String(255), nullable=True)

class Role(Base):
    __tablename__ = "role2"

    id=Column(Integer, primary_key=True, index=True)
    name=Column(String(50), nullable=False)
    
class User(Base):
    __tablename__ = "user2"

    id=Column(Integer, primary_key=True, index=True)
    username=Column(String(50), unique=True, nullable=False)
    email=Column(String(150), unique=True, nullable=False)
    password=Column(String(35), nullable=False)
    attempt=Column(Integer, default=0)
    active=Column(Boolean, default=True)
    secret=Column(String(150))
    # role: List[Role] = []
    # start_datetime: datetime = Body()