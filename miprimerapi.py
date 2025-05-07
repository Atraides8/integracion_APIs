#hola empiezo mi codigo ahora

from fastapi import FastAPI

app = FastAPI()

@app.get("/")

def leer_ruta():
    return {"Mensaje": "Hola mundo"}