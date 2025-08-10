from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.database import get_db
from sqlalchemy.orm import Session
from src.schema.basic import ResponseError, SchemaSwagger
from src.schema.user import DTOUserCreate, DTOUserUpdate, DTOUserRetrieve
from src.schema.auth import DTOToken
from src.service.user import ServiceUser
from uuid import UUID

user = APIRouter(prefix="/user", tags=["user"])

@user.post("/swagger", status_code=200)
async def create(form_data: OAuth2PasswordRequestForm=Depends(), db: Session=Depends(get_db)):
    try:
        print(form_data)
        return ResponseError(code=200, status="Ok", message="Ok", validationErrors="_result").dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user.post("/login", status_code=200)
async def create(request: SchemaSwagger, db: Session=Depends(get_db)):
    try:
        _result = ServiceUser.authenticate_user(db, request.username, request.password)
        return ResponseError(code=200, status="Ok", message="Ok", validationErrors=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user.post("/", status_code=201)
async def create(request: DTOUserCreate, db: Session=Depends(get_db), current_user=Depends(ServiceUser.get_current_user)):
    try:
        _result = ServiceUser.create(db, created=request)
        return ResponseError(code=201, status="Created", message="Created", validationErrors=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@user.patch("/", status_code=202)
async def cancel(request: DTOUserRetrieve, db: Session=Depends(get_db)):
    try:
        _result = DTOUserRetrieve.cancel(db, cancelled=request)
        return ResponseError(code=202, status="Accepted", message="Cancelled", validationErrors=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@user.get("/", status_code=200)
async def get(db: Session=Depends(get_db), current_user: dict = Depends(ServiceUser.get_current_user)):
    try:
        _result = ServiceUser.get(db, 0, 100)
        return ResponseError(code=200, status="Ok", message="Finded all", validationErrors=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@user.get("/{id}", status_code=200)
async def get_by_id(id: UUID, db: Session=Depends(get_db)):
    try:
        _result = ServiceUser.get_by_id(db, id)
        if not _result:
            raise HTTPException(status_code=404, detail=f"Object {id} not found")
        return ResponseError(code=200, status="Ok", message="Finded one", validationErrors=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user.put("/", status_code=202)
async def update(request: DTOUserUpdate, db: Session=Depends(get_db), current_user=Depends(ServiceUser.get_current_user)):
    try:
        _result = ServiceUser.update(db, updated=request)
        if not _result:
            raise HTTPException(status_code=404, detail=f"Object {id} not found")
        return ResponseError(code=202, status="Accepted", message="Updated", validationErrors=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user.delete("/{id}", status_code=204)
async def delete(id: UUID, db: Session=Depends(get_db), current_user=Depends(ServiceUser.get_current_user)):
    try:
        _result = ServiceUser.remove(db, id=id)
        if not _result:
            raise HTTPException(status_code=404, detail=f"Object {id} not found")
        return ResponseError(code=204, status="No Content", message="Delete one", validationErrors=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))