from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.database import get_db
from sqlalchemy.orm import Session
from src.schema.base import Response
from src.schema.user import DTOUserCreate, DTOUserUpdate, DTOUserResponse
from src.service.serviceUser import ServiceUser
from uuid import UUID

user = APIRouter()

# @user.post("/swagger", status_code=200)
# async def create(form_data: OAuth2PasswordRequestForm=Depends(), db: Session=Depends(get_db)):
#     try:
#         print(form_data)
#         return Response(code=200, status="Ok", message="Ok", result="_result").dict(exclude_none=True)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @user.post("/login", status_code=200)
# async def create(request: SchemaSwagger, db: Session=Depends(get_db)):
#     try:
#         _result = ServiceUser.login(db, created=request)
#         return Response(code=200, status="Ok", message="Ok", result=_result).dict(exclude_none=True)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@user.post("/", status_code=201)
async def create(request: DTOUserCreate, db: Session=Depends(get_db), current_user=Depends(ServiceUser.get_current_user)):
    try:
        _result = ServiceUser.create(db, created=request)
        return Response(code=201, status="Created", message="Created", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@user.patch("/", status_code=202)
async def cancel(request: DTOUserResponse, db: Session=Depends(get_db)):
    try:
        _result = DTOUserResponse.cancel(db, cancelled=request)
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
            raise HTTPException(status_code=404, detail=f"Object {id} not found")
        return Response(code=200, status="Ok", message="Finded one", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user.put("/", status_code=202)
async def update(request: DTOUserUpdate, db: Session=Depends(get_db), current_user=Depends(ServiceUser.get_current_user)):
    try:
        _result = ServiceUser.update(db, updated=request)
        if not _result:
            raise HTTPException(status_code=404, detail=f"Object {id} not found")
        return Response(code=202, status="Accepted", message="Updated", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user.delete("/{id}", status_code=204)
async def delete(id: UUID, db: Session=Depends(get_db), current_user=Depends(ServiceUser.get_current_user)):
    try:
        _result = ServiceUser.remove(db, id=id)
        if not _result:
            raise HTTPException(status_code=404, detail=f"Object {id} not found")
        return Response(code=204, status="No Content", message="Delete one", result=_result).dict(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))