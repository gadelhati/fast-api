from fastapi import APIRouter, HTTPException, Path, Depends
from config import SessionLocal
from sqlalchemy.orm import Session
from schema import BookSchema, Response
import crud

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
async def create(request: BookSchema, db: Session=Depends(get_db)):
    try:
        _book = crud.create_book(db, book=request)
        return await Response(code=200, status="Ok", message="Created", result=_book).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get(db: Session=Depends(get_db)):
    try:
        _book = crud.get_book(db, 0, 100)
        return await Response(code=200, status="Ok", message="Finded all", result=_book).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}")
async def get_by_id(id: int, db: Session=Depends(get_db)):
    try:
        _book = crud.get_book_by_id(db, id)
        if not _book:
            raise HTTPException(status_code=404, detail=f"Book {id} not found")
        return await Response(code=200, status="Ok", message="Finded one", result=_book).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/")
async def update_book(request: BookSchema, db: Session=Depends(get_db)):
    try:
        _book = crud.update_book(db, request)
        if not _book:
            raise HTTPException(status_code=404, detail=f"Book {id} not found")
        return await Response(code=200, status="Ok", message="Updated", result=_book).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{id}")
async def delete(id: int, db: Session=Depends(get_db)):
    try:
        _book = crud.remove_book(db, book_id=id)
        if not _book:
            raise HTTPException(status_code=404, detail=f"Book {id} not found")
        return await Response(code=200, status="Ok", message="Delete one").dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))