from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from api.database import Base
from datetime import datetime
from typing import List

class Book(Base):
    __tablename__ = "book"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)

class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(35), nullable=False)
    attempt = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    secret = Column(String(150))
    start_datetime = Column(DateTime, default=datetime.utcnow)

    roles = relationship("Role", cascade="all, delete-orphan")