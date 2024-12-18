from fastapi import Body, FastAPI, HTTPException
from config import engine
from sqlalchemy.exc import SQLAlchemyError

import model
import router

try:
    model.Base.metadata.create_all(bind=engine)
except SQLAlchemyError as e:
    raise RuntimeError(f"Error creating tables in the database: {e}")

app = FastAPI()

@app.get("/")
async def home():
    return await {"message": "Welcome Home", "status": "success"}

app.include_router(router.router, prefix="/book", tags=["book"])