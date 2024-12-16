# from enum import Enum
# from typing import List
from fastapi import Body, FastAPI, HTTPException
# from component import Role, User
from config import engine

import model
import router

model.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
async def Home():
    return "Welcome Home"

app.include_router(router.router, prefix="/book", tags=["book"])

# class RoleName(str, Enum):
#     admin = "admin"
#     moderator = "moderator"
#     user = "user"

# @app.get("/items")
# async def read_all():
#     return {"Hello": "World"}

# @app.get("/role")
# async def read_all(role: Role = Body(embed=True)):
#     return {"Hello": "World"}

# @app.get("/items/{item_id}")
# async def read_item(item_id: int, q: str = None):
#     return {"item_id": item_id, "q": q}
    
# @app.put("/items/{item_id}")
# async def update_item(item_id: int, item: User):
#     #burgers = await get_burgers(2)
#     if item.active:
#         result = {"item_username": item.username, "item_email": item.email}
#     return result
    
# @app.get("/role/{role_name}")
# async def get_model(role_name: RoleName):
#     if role_name in RoleName:
#         return {"role_name": role_name, "message": "Valid role!"}
#     raise HTTPException(status_code=404, detail="Role not found")
    
#@app.put("/items/{item_id}")
#async def read_items(q: Union[str, None] = Query(default=None, min_length=3, max_length=50, pattern="^fixedquery$"),):
#async def update_item(item_id: int, item: Item, q: Union[str, None] = None):
#    result = {"item_id": item_id, **item.dict()}
#    if q:
#        result.update({"q": q})
#    return result