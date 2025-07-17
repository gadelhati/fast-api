from sqlalchemy.orm import Session
from typing import List, Optional
from model.mixin import ModelBook
from src.schema.schema import SchemaBook
from sqlalchemy.dialects.postgresql import UUID

class ServiceBook:
    def get(db: Session, skip: int=0, limit: int=0) -> List[ModelBook]:
        return db.query(ModelBook).offset(skip).limit(limit).all()

    def get_by_id(db: Session, id: UUID) -> Optional[ModelBook]:
        return db.query(ModelBook).filter(ModelBook.id == id).first()

    def create(db: Session, created: SchemaBook) -> ModelBook:
        _object = ModelBook(created.title, description=created.description)
        db.add(_object)
        db.commit()
        db.refresh(_object)
        return _object
    
    def cancel(db: Session, cancelled: SchemaBook) -> ModelBook:
        _object = ServiceBook.get_by_id(db, cancelled.id)
        if _object:
            db.delete(_object)
            db.commit()
        return _object

    def update(db: Session, updated: SchemaBook) -> ModelBook:
        _object = ServiceBook.get_by_id(db, updated.id)
        if _object:
            _object.title = updated.title
            _object.description = updated.description
            db.commit()
            db.refresh(_object)
        return _object

    def remove(db: Session, id: UUID) -> ModelBook:
        _object = ServiceBook.get_by_id(db, id)
        if _object:
            db.delete(_object)
            db.commit()
        return _object