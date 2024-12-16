from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql://postgres:G%40delha@localhost:5432/fastAPI"

# user = "postgresql"
# password = "efjbe46Ni4a6WC8i5h2Vn3FOtGwZQVTm"
# host = "dpg-ctcd7etds78s739cdma0-a.oregon-postgres.render.com"
# port = 5432
# database = "mfa_p68q"

# engine = create_engine("postgresql://{0}:{1}@{2}:{3}/{4}".format(
#             user, password, host, port, database
#         ))
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()