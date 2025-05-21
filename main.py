from fastapi import FastAPI, HTTPException, Path, Query, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from auth import autenticar_usuario, crear_token
from datetime import timedelta
from pydantic import BaseModel
from auth import requerir_rol
import requests

app = FastAPI()

# Configuración base de la API de FERREMAS
FERREMAS_API_URL = "https://ea2p2assets-production.up.railway.app"
AUTH_TOKEN = "SaGrP9ojGS39hU9ljqbXxQ=="

HEADERS = {
    "x-authentication": AUTH_TOKEN,  # ✅ Header correcto
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
        response = requests.get(
            f"{FERREMAS_API_URL}/data/sucursales/{id}",
            headers=HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError:
        raise HTTPException(status_code=response.status_code, detail="Sucursal no encontrada")
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))    


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
        response = requests.get(
            f"{FERREMAS_API_URL}/data/vendedores/{id}",
            headers=HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError:
        raise HTTPException(status_code=response.status_code, detail="Vendedor no encontrado")
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))


#EN ARREGLO MIENTRAS LO VE EL PROFE
"""@app.post("/pedidos")
def crear_pedido(pedido: Pedido):
    try:
        response = requests.post(
            f"{FERREMAS_API_URL}/data/pedidos/nuevo",
            json=pedido.dict(),  # Convertimos el modelo en dict para pasarlo como JSON
            headers=HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return {
            "mensaje": "Pedido creado correctamente",
            "datos": response.json()
        }
    except requests.HTTPError:
        raise HTTPException(status_code=response.status_code, detail="Error al crear pedido")
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))"""


@app.put("/productos/venta/{id}")
def registrar_venta(
    id: str = Path(..., description="ID del artículo, ej: ART001"),
    cantidad: int = Query(..., gt=0, description="Cantidad a registrar en la venta"),
    user: dict = Depends(requerir_rol("admin", "maintainer"))
):
    try:
        response = requests.put(
            f"{FERREMAS_API_URL}/data/articulos/venta/{id}",
            params={"cantidad": cantidad},  # 👈 enviar como query param
            headers=HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return {"mensaje": "Productos registrados correctamente"}
    except requests.HTTPError:
        raise HTTPException(status_code=response.status_code, detail="Error al registrar venta")
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))