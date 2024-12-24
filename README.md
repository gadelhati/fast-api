# _FastAPI_

## install
```
python -m venv .venv
.venv/Scripts/activate
pip install fastapi sqlalchemy psycopg2-binary uvicorn python-multipart passlib[bcrypt] python-jose
uvicorn src.main:app --reload
```
## environments variables
```
PYTHONPATH = C:\Users\gadel\AppData\Local\Programs\Python\Python313
PATH = %PYTHONPATH%; %PYTHONPATH%\Scripts
```

## roadmap
### in development
- [x] authorization

### in concept
- [x] implements tests