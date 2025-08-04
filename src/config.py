import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
DATABASE_SCHEMA = os.getenv("DATABASE_SCHEMA")
DATABASE_URL = os.getenv("DATABASE_URL")