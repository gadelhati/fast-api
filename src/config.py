import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_SCHEMA = os.getenv("DATABASE_SCHEMA")
DATABASE_URL = os.getenv("DATABASE_URL")