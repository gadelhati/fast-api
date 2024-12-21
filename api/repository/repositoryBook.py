from sqlalchemy.orm import Session
from typing import List, Optional
from api.models.model import Book
from api.models.schema import BookSchema
from sqlalchemy.dialects.postgresql import UUID

class RepositoryBook:
    def get(db: Session, skip: int=0, limit: int=0) -> List[Book]:
        return db.query(Book).offset(skip).limit(limit).all()

    def get_by_id(db: Session, id: UUID) -> Optional[Book]:
        return db.query(Book).filter(Book.id == id).first()

    def create(db: Session, created: BookSchema) -> Book:
        _object = Book(title=created.title, description=created.description)
        db.add(_object)
        db.commit()
        db.refresh(_object)
        return _object
    
    def cancel(db: Session, cancelled: BookSchema) -> Book:
        _object = RepositoryBook.get_by_id(db, cancelled.id)
        if _object:
            db.delete(_object)
            db.commit()
        return _object

    def update(db: Session, updated: BookSchema) -> Book:
        _object = RepositoryBook.get_by_id(db, updated.id)
        if _object:
            _object.title = updated.title
            _object.description = updated.description
            db.commit()
            db.refresh(_object)
        return _object

    def remove(db: Session, id: UUID) -> Book:
        _object = RepositoryBook.get_by_id(db, id)
        if _object:
            db.delete(_object)
            db.commit()
        return _object