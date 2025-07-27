from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from src.model.user import User
from src.schema.auth import DTOToken
from src.schema.user import DTOUserRetrieve
from src.schema.user import DTOUserCreate, DTOUserUpdate, DTOUserRetrieve
from sqlalchemy.dialects.postgresql import UUID
from passlib.hash import pbkdf2_sha256
from jose import jwt
from src.database import get_db

import time
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/swagger")

class ServiceUser:
    def get(db: Session, skip: int=0, limit: int=0) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()

    def get_by_id(db: Session, id: UUID) -> Optional[User]:
        return db.query(User).filter(User.id == id).first()
    def get_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def login(db: Session, created: DTOUserRetrieve) -> User:
        _object_username = ServiceUser.get_by_username(db, created.username)
        _match = pbkdf2_sha256.verify(created.password, _object_username.password)
        if not _object_username or not _match:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return ServiceUser.creat_jwt(_object_username)
    
    def create(db: Session, created: DTOUserCreate) -> User:
        _object_username = ServiceUser.get_by_username(db, created.username)
        _object_email = ServiceUser.get_by_email(db, created.email)
        if _object_username or _object_email:
            raise HTTPException(status_code=409, detail="Conflict")
        _object = User(username=created.username, password=pbkdf2_sha256.hash(created.password), email=created.email)
        db.add(_object)
        db.commit()
        db.refresh(_object)
        return _object
    
    def cancel(db: Session, cancelled: DTOUserRetrieve) -> User:
        _object = ServiceUser.get_by_id(db, cancelled.id)
        if _object:
            db.delete(_object)
            db.commit()
        return _object

    def update(db: Session, updated: DTOUserUpdate) -> User:
        _object = ServiceUser.get_by_id(db, updated.id)
        if _object:
            _object.username = updated.username
            _object.password = pbkdf2_sha256.hash(updated.password)
            db.commit()
            db.refresh(_object)
        return _object

    def remove(db: Session, id: UUID) -> User:
        _object = ServiceUser.get_by_id(db, id)
        if _object:
            db.delete(_object)
            db.commit()
        return _object
    
    def creat_jwt(created: DTOUserCreate):
        claims = {
            'iss': 'fastAPI',
            'sub': created.username,
            'aud': '*',
            'exp': int(time.time()) + (4 * 60 * 60),
            'nbf': int(time.time()),
            'iat': int(time.time()),
            'jti': 'uuid.uuid4()'
        }
        _object = DTOToken(accessToken=jwt.encode(claims, 'secret', algorithm='HS256'), refreshToken='', roles=created.roles)
        return _object
    
    def get_current_user(db: Session=Depends(get_db), token: str=Depends(oauth2_scheme)):
        ...