from fastapi import APIRouter, HTTPException, Depends
from src.database import get_db
from sqlalchemy.orm import Session
from schema.schema_old import SchemaBook, Response
from src.service.serviceUser import ServiceUser
from src.service.serviceBook import ServiceBook
from uuid import UUID

book = APIRouter()

@book.post("/", status_code=201)
async def create(request: SchemaBook, db: Session=Depends(get_db), current_user=Depends(ServiceUser.get_current_user)):
    try:
        _result = ServiceBook.create(db, created=request)
        return Response(code=201, status="Created", message="Created", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@book.patch("/", status_code=202)
async def cancel(request: SchemaBook, db: Session=Depends(get_db)):
    try:
        _result = ServiceBook.cancel(db, cancelled=request)
        return Response(code=202, status="Accepted", message="Cancelled", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@book.get("/", status_code=200)
async def get(db: Session=Depends(get_db)):
    try:
        _result = ServiceBook.get(db, 0, 100)
        return Response(code=200, status="Ok", message="Finded all", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@book.get("/{id}", status_code=200)
async def get_by_id(id: UUID, db: Session=Depends(get_db)):
    try:
        _result = ServiceBook.get_by_id(db, id)
        if not _result:
            raise HTTPException(status_code=404, detail=f"Object {id} not found")
        return Response(code=200, status="Ok", message="Finded one", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@book.put("/", status_code=202)
async def update(request: SchemaBook, db: Session=Depends(get_db), current_user=Depends(ServiceUser.get_current_user)):
    try:
        _result = ServiceBook.update(db, updated=request)
        if not _result:
            raise HTTPException(status_code=404, detail=f"Object {id} not found")
        return Response(code=202, status="Accepted", message="Updated", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@book.delete("/{id}", status_code=204)
async def delete(id: UUID, db: Session=Depends(get_db), current_user=Depends(ServiceUser.get_current_user)):
    try:
        _result = ServiceBook.remove(db, id=id)
        if not _result:
            raise HTTPException(status_code=404, detail=f"Object {id} not found")
        return Response(code=204, status="No Content", message="Delete one", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))