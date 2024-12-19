from sqlalchemy.orm import Session
from typing import List, Optional
from api.models.model import Book
from api.models.schema import BookSchema

class Crud:
    def get_book(db: Session, skip: int=0, limit: int=0) -> List[Book]:
        return db.query(Book).offset(skip).limit(limit).all()

    def get_book_by_id(db: Session, book_id: int) -> Optional[Book]:
        return db.query(Book).filter(Book.id == book_id).first()

    def create_book(db: Session, book: BookSchema) -> Book:
        _book = Book(title=book.title, description=book.description)
        db.add(_book)
        db.commit()
        db.refresh(_book)
        return _book

    def remove_book(db: Session, book_id: int) -> None:
        _book = Crud.get_book_by_id(db=db, book_id=book_id)
        if _book:
            db.delete(_book)
            db.commit()

    def update_book(db: Session, book: BookSchema) -> Book:
        _book = Crud.get_book_by_id(db=db, book_id=book.id)
        if _book:
            _book.title = book.title
            _book.description = book.description
            db.commit()
            db.refresh(_book)
        return _book