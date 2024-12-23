from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from src.database import engine
from src.model import model
from src.route.routeBook import router

try:
    model.Base.metadata.create_all(bind=engine)
except SQLAlchemyError as e:
    raise RuntimeError(f"Error creating tables in the database: {e}")

app = FastAPI()

origins = [
    "http://127.0.0.2",
    "http://127.0.0.2:8081",
    "https://example.com"
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
    return {"message": "Welcome Home", "status": "success"}

app.include_router(router, prefix="/book", tags=["book"])