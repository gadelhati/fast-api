from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from src.database import engine
from src.database import Base
from src.route.user import user
from src.route.role import role
from src.route.admin import admin
from src.route.permission import permission

try:
    Base.metadata.create_all(bind=engine)
except SQLAlchemyError as e:
    raise RuntimeError(f"Error creating tables in the database: {e}")

app = FastAPI()

origins = [
    "http://127.0.0.1:5173",
    "http://127.0.0.1",
    "http://localhost:5173",
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return {"message": "Welcome Fast API by Gadelha TI", "status": "success"}

app.include_router(permission)
app.include_router(role)
app.include_router(admin)
app.include_router(user)