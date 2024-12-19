from fastapi import APIRouter, HTTPException, Path, Depends
from api.database import SessionLocal
from sqlalchemy.orm import Session
from api.models.schema import BookSchema, Response
from api.repository.repositoryBook import RepositoryBook

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
        _book = RepositoryBook.create(db, created=request)
        return Response(code=200, status="Ok", message="Created", result=_book).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get(db: Session=Depends(get_db)):
    try:
        _book = RepositoryBook.get(db, 0, 100)
        return Response(code=200, status="Ok", message="Finded all", result=_book).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}")
async def get_by_id(id: int, db: Session=Depends(get_db)):
    try:
        _book = RepositoryBook.get_by_id(db, id)
        if not _book:
            raise HTTPException(status_code=404, detail=f"Book {id} not found")
        return Response(code=200, status="Ok", message="Finded one", result=_book).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/")
async def update(request: BookSchema, db: Session=Depends(get_db)):
    try:
        _book = RepositoryBook.update(db, request)
        if not _book:
            raise HTTPException(status_code=404, detail=f"Book {id} not found")
        return Response(code=200, status="Ok", message="Updated", result=_book).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{id}")
async def delete(id: int, db: Session=Depends(get_db)):
    try:
        _book = RepositoryBook.remove(db, id=id)
        if not _book:
            raise HTTPException(status_code=404, detail=f"Book {id} not found")
        return Response(code=200, status="Ok", message="Delete one", result=_book).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))