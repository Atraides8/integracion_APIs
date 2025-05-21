from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

# URL del endpoint de login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Usuarios de prueba (sin hash, para simplificar)
USUARIOS_PRUEBA = {
    "javier_thompson": {
        "password": "aONF4d6aNBIxRjlgjBRRzrS",
        "rol": "admin"
    },
    "ignacio_tapia": {
        "password": "f7rWChmQS1JYfThT",
        "rol": "maintainer"
    },
    "stripe_sa": {
        "password": "dzkQqDL9XZH33YDzhmsf",
        "rol": "service_account"
    },
}

# Configuración de JWT
SECRET_KEY = "clave_super_secreta_para_token"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Función para autenticar usuario
def autenticar_usuario(username: str, password: str) -> Optional[dict]:
    user = USUARIOS_PRUEBA.get(username)
    if user and user["password"] == password:
        return {"username": username, "rol": user["rol"]}
    return None

# Crear JWT
def crear_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Obtener usuario actual desde el token
def obtener_usuario_actual(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        rol: str = payload.get("rol")
        if username is None or rol is None:
            raise credentials_exception
        return {"username": username, "rol": rol}
    except JWTError:
        raise credentials_exception

# Dependencia para verificar rol
def requerir_rol(*roles):
    def rol_checker(user: dict = Depends(obtener_usuario_actual)):
        if user["rol"] not in roles:
            raise HTTPException(status_code=403, detail="No tienes permiso para acceder a este recurso")
        return user
    return rol_checker