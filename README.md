# _FastAPI_

## install
```
python -m venv .venv; .\.venv\Scripts\Activate.ps1; python.exe -m pip install --upgrade pip; pip install --upgrade -r requirements.txt; uvicorn src.main:app --reload
```
```
# create virtual environment
python -m venv .venv

# activate virtual environment
.venv/Scripts/activate

# udpate pip
python.exe -m pip install --upgrade pip

# install dependencies
pip install --upgrade -r requirements.txt

# run application
uvicorn src.main:app --reload

pip install --proxy http://user:password@proxy.fqdn:6060 -r requirements.txt
git config --global http.proxy http://user:password@proxy.fqdn:6060
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