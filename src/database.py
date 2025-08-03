from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncAttrs
from src.config import DATABASE_SCHEMA, DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
with engine.connect() as conn:
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DATABASE_SCHEMA}"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base(cls=AsyncAttrs)
Base.metadata.schema = DATABASE_SCHEMA

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()