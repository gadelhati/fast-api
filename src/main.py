from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from src.database import engine
from src.model import model
from src.route.routeBook import book
from src.route.routeUser import user

try:
    model.Base.metadata.create_all(bind=engine)
except SQLAlchemyError as e:
    raise RuntimeError(f"Error creating tables in the database: {e}")

app = FastAPI()

origins = [
    "http://127.0.0.1:5173",
    "http://127.0.0.1",
    "http://localhost:5173",
    "http://localhost",
    "https://example.com"
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return {"message": "Welcome Home", "status": "success"}

app.include_router(book, prefix="/book", tags=["book"])
app.include_router(user, prefix="/user", tags=["user"])