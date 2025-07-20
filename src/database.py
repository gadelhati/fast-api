from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncAttrs

# DATABASE_URL = "postgresql://postgresql_e3u5_user:sGC82cam8LyB08Sj3x3SLIRgKq2bpiPx@dpg-cu3c4mhopnds73855c4g-a.oregon-postgres.render.com/postgresql_e3u5"
# DATABASE_URL = "postgresql://postgresql_e3u5_user:sGC82cam8LyB08Sj3x3SLIRgKq2bpiPx@dpg-cu3c4mhopnds73855c4g-a/postgresql_e3u5"
# DATABASE_URL = jdbc:postgresql://postgresql:efjbe46Ni4a6WC8i5h2Vn3FOtGwZQVTm@dpg-ctcd7etds78s739cdma0-a:5432/mfa_p68q
DATABASE_URL = "postgresql://postgres:G%40delha@localhost:5432/fastAPI"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base(cls=AsyncAttrs)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()