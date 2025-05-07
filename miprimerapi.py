from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List


app: FastAPI = FastAPI(
    debug=True,
    title='Mi primer Api',
    version="0.0.1",
)


class User(BaseModel):
    name: str
    email: EmailStr


fake_users_db = {}


@app.get("/users", response_model=List[User])
def get_users():
    return list(fake_users_db.values())


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    if user_id not in fake_users_db:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return fake_users_db[user_id]


@app.post("/users", response_model=User)
def create_user(user: User):
    user_id = len(fake_users_db) + 1
    fake_users_db[user_id] = user
    return user


@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: User):
    if user_id not in fake_users_db:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    fake_users_db[user_id] = user
    return user


@app.delete("/users/{user_id}", response_model=User)
def delete_user(user_id: int):
    if user_id not in fake_users_db:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return fake_users_db.pop(user_id)


@app.post("/login")
def login(user: User):
    for u in fake_users_db.values():
        if u.email == user.email and u.name == user.name:
            return {"message": "Inicio de sesión exitoso"}
    raise HTTPException(status_code=401, detail="Credenciales inválidas")


@app.get("/search")
def search_user(name: str):
    results = [user for user in fake_users_db.values() if name.lower() in user.name.lower()]
    if not results:
        raise HTTPException(status_code=404, detail="No se encontraron usuarios con ese nombre")
    return results