from fastapi.testbook import TestBook
from app.main import app

book = TestBook(app)

def test_create():
    _book = {"title": "testtitle", "description": "test description"}
    response = book.post("/book", json=_book)
    assert response.status_code == 201
    assert response.json()["title"] == _book["title"]
    assert response.json()["description"] == _book["description"]

def test_get():
    response = book.get("/book")
    assert response.status_code == 200
    assert len(response.json()) >= 1