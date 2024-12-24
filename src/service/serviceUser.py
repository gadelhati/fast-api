from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from src.model.model import ModelUser
from src.schema.schema import SchemaUser
from src.schema.schema import SchemaToken
from sqlalchemy.dialects.postgresql import UUID
from passlib.hash import pbkdf2_sha256
from jose import jwt

import time
import uuid

class ServiceUser:
    def get(db: Session, skip: int=0, limit: int=0) -> List[ModelUser]:
        return db.query(ModelUser).offset(skip).limit(limit).all()

    def get_by_id(db: Session, id: UUID) -> Optional[ModelUser]:
        return db.query(ModelUser).filter(ModelUser.id == id).first()
    def get_by_username(db: Session, username: str) -> Optional[ModelUser]:
        return db.query(ModelUser).filter(ModelUser.username == username).first()
    def get_by_email(db: Session, email: str) -> Optional[ModelUser]:
        return db.query(ModelUser).filter(ModelUser.email == email).first()

    def login(db: Session, created: SchemaUser) -> ModelUser:
        _object_username = ServiceUser.get_by_username(db, created.username)
        _match = pbkdf2_sha256.verify(created.password, _object_username.password)
        if not _object_username or not _match:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return ServiceUser.creat_jwt(_object_username)
    
    def create(db: Session, created: SchemaUser) -> ModelUser:
        _object_username = ServiceUser.get_by_username(db, created.username)
        _object_email = ServiceUser.get_by_email(db, created.email)
        if _object_username or _object_email:
            raise HTTPException(status_code=409, detail="Conflict")
        _object = ModelUser(username=created.username, password=pbkdf2_sha256.hash(created.password), email=created.email)
        db.add(_object)
        db.commit()
        db.refresh(_object)
        return _object
    
    def cancel(db: Session, cancelled: SchemaUser) -> ModelUser:
        _object = ServiceUser.get_by_id(db, cancelled.id)
        if _object:
            db.delete(_object)
            db.commit()
        return _object

    def update(db: Session, updated: SchemaUser) -> ModelUser:
        _object = ServiceUser.get_by_id(db, updated.id)
        if _object:
            _object.username = updated.username
            _object.password = pbkdf2_sha256.hash(updated.password)
            db.commit()
            db.refresh(_object)
        return _object

    def remove(db: Session, id: UUID) -> ModelUser:
        _object = ServiceUser.get_by_id(db, id)
        if _object:
            db.delete(_object)
            db.commit()
        return _object
    
    def creat_jwt(created: SchemaUser):
        claims = {
            'iss': 'fastAPI',
            'sub': created.username,
            'aud': '*',
            'exp': int(time.time()) + (4 * 60 * 60),
            'nbf': int(time.time()),
            'iat': int(time.time()),
            'jti': 'uuid.uuid4()'
        }
        _object = SchemaToken(tokenType='Bearer ', accessToken=jwt.encode(claims, 'secret', algorithm='HS256'), refreshToken='', roles=created.roles)
        return _object