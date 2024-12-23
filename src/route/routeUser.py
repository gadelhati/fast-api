from fastapi import APIRouter, HTTPException, Path, Depends
from src.database import SessionLocal
from sqlalchemy.orm import Session
from src.schema.schema import SchemaUser, Response
from src.service.serviceUser import ServiceUser
from uuid import UUID

user = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@user.post("/", status_code=201)
async def create(request: SchemaUser, db: Session=Depends(get_db)):
    try:
        _result = ServiceUser.create(db, created=request)
        return Response(code=201, status="Created", message="Created", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@user.patch("/", status_code=202)
async def cancel(request: SchemaUser, db: Session=Depends(get_db)):
    try:
        _result = SchemaUser.cancel(db, cancelled=request)
        return Response(code=202, status="Accepted", message="Cancelled", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@user.get("/", status_code=200)
async def get(db: Session=Depends(get_db)):
    try:
        _result = ServiceUser.get(db, 0, 100)
        return Response(code=200, status="Ok", message="Finded all", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@user.get("/{id}", status_code=200)
async def get_by_id(id: UUID, db: Session=Depends(get_db)):
    try:
        _result = ServiceUser.get_by_id(db, id)
        if not _result:
            raise HTTPException(status_code=404, detail=f"Book {id} not found")
        return Response(code=200, status="Ok", message="Finded one", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user.put("/", status_code=202)
async def update(request: SchemaUser, db: Session=Depends(get_db)):
    try:
        _result = ServiceUser.update(db, updated=request)
        if not _result:
            raise HTTPException(status_code=404, detail=f"Book {id} not found")
        return Response(code=202, status="Accepted", message="Updated", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user.delete("/{id}", status_code=204)
async def delete(id: UUID, db: Session=Depends(get_db)):
    try:
        _result = ServiceUser.remove(db, id=id)
        if not _result:
            raise HTTPException(status_code=404, detail=f"Book {id} not found")
        return Response(code=204, status="No Content", message="Delete one", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))