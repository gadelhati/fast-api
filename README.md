# install fastapi
pip install "fastapi[standard]"

# install
python -m venv .venv
.venv/Scripts/activate
pip install fastapi sqlalchemy psycopg2-binary uvicorn
uvicorn main:app --reload

# environments variables
PYTHONPATH = C:\Users\gadel\AppData\Local\Programs\Python\Python313
PATH = %PYTHONPATH%; %PYTHONPATH%\Scripts