from fastapi import FastAPI, HTTPException, Path, Query, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from auth import autenticar_usuario, crear_token, requerir_rol
from datetime import timedelta
from pydantic import BaseModel
from fastapi.openapi.utils import get_openapi
from banco_central import router as banco_central_router
import requests

app = FastAPI()

# Incluir routers
app.include_router(banco_central_router, prefix="/api", tags=["Banco Central"])

# Configuración base de la API de FERREMAS
FERREMAS_API_URL = "https://ea2p2assets-production.up.railway.app"
AUTH_TOKEN = "SaGrP9ojGS39hU9ljqbXxQ=="

HEADERS = {
    "x-authentication": AUTH_TOKEN,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

TIMEOUT = 10  # segundos

# ------------------- MODELOS ---------------------

class Pedido(BaseModel):
    idArticulo: str
    cantidad: int
    idSucursal: str
    idVendedor: int

# ------------------- ENDPOINTS ---------------------

# Modificar el esquema OpenAPI para mostrar JWT auth en Swagger
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="API de Ferremas",
        version="1.0.0",
        description="API protegida con JWT y roles (admin, maintainer, etc.)",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {  # Solo es un nombre, no depende de la clase usada
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"OAuth2PasswordBearer": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ------------------- LOGIN ---------------------

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    usuario = autenticar_usuario(form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = crear_token(data={"sub": usuario["username"], "rol": usuario["rol"]})
    return {"access_token": access_token, "token_type": "bearer"}

# ------------------- ENDPOINTS ABIERTOS ---------------------

@app.get("/productos")
def obtener_productos():
    try:
        response = requests.get(f"{FERREMAS_API_URL}/data/articulos", headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/productos/{id}")
def obtener_producto(id: str = Path(..., description="ID del artículo, ej: ART001")):
    try:
        response = requests.get(f"{FERREMAS_API_URL}/data/articulos/{id}", headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError:
        raise HTTPException(status_code=response.status_code, detail="Producto no encontrado")
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/sucursales")
def obtener_sucursales():
    try:
        response = requests.get(f"{FERREMAS_API_URL}/data/sucursales", headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/sucursales/{id}")
def obtener_sucursal(id: str = Path(..., description="ID de la sucursal, ej: SC001")):
    try:
        response = requests.get(f"{FERREMAS_API_URL}/data/sucursales/{id}", headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError:
        raise HTTPException(status_code=response.status_code, detail="Sucursal no encontrada")
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))

# ------------------- ENDPOINTS PROTEGIDOS ---------------------

@app.get("/vendedores")
def obtener_vendedores(user=Depends(requerir_rol("admin", "maintainer"))):
    try:
        response = requests.get(f"{FERREMAS_API_URL}/data/vendedores", headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/vendedores/{id}")
def obtener_vendedor(id: str = Path(..., description="ID del vendedor, ej: V001"),
                     user=Depends(requerir_rol("admin", "maintainer"))):
    try:
        response = requests.get(f"{FERREMAS_API_URL}/data/vendedores/{id}", headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError:
        raise HTTPException(status_code=response.status_code, detail="Vendedor no encontrado")
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.put("/productos/venta/{id}")
def registrar_venta(
    id: str = Path(..., description="ID del artículo, ej: ART001"),
    cantidad: int = Query(..., gt=0, description="Cantidad a registrar en la venta"),
    user: dict = Depends(requerir_rol("admin", "maintainer"))
):
    try:
        response = requests.put(
            f"{FERREMAS_API_URL}/data/articulos/venta/{id}",
            params={"cantidad": cantidad},
            headers=HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return {"mensaje": "Productos registrados correctamente"}
    except requests.HTTPError:
        raise HTTPException(status_code=response.status_code, detail="Error al registrar venta")
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))