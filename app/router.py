from fastapi import APIRouter, HTTPException, Path, Depends
from config import SessionLocal
from sqlalchemy.orm import Session
from schema import BookSchema, RequestBook, Response

import crud

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create")
async def create(request: RequestBook, db: Session=Depends(get_db)):
    crud.create_book(db, book=request.parameter)
    return Response(code=200, status="Ok", message="Created").dict(exclude_none=True)

@router.get("/")
async def get(db: Session=Depends(get_db)):
    _book = crud.get_book(db, 0, 100)
    return Response(code=200, status="Ok", message="Finded all", result=_book).dict(exclude_none=True)

@router.get("/{id}")
async def get_by_id(id: int, db: Session=Depends(get_db)):
    _book = crud.get_book_by_id(db, id)
    return Response(code=200, status="Ok", message="Finded one", result=_book).dict(exclude_none=True)

@router.post("/update")
async def update_book(request: RequestBook, db: Session=Depends(get_db)):
    _book = crud.update_book(db, book_id=request.parameter.id, title=request.parameter.title, description=request.parameter.descritption)
    return Response(code=200, status="Ok", message="Updated", result=_book)

@router.delete("/{id}")
async def delete(id: int, db: Session=Depends(get_db)):
    crud.remove_book(db, book_id=id)
    return Response(code=200, status="Ok", message="Delete one").dict(exclude_none=True)