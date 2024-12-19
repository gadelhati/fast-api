from sqlalchemy import Column, Integer, String
from api.config import Base

class Book(Base):
    __tablename__ = "book"

    id=Column(Integer, primary_key=True, index=True)
    title=Column(String(50), nullable=False)
    description=Column(String(255), nullable=True)