import bcchapi
import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter()
siete = bcchapi.Siete("nicolas.noimann83@gmail.com", "Pryzalek3")

@router.get("/divisas/buscar")
def buscar_series(palabra_clave: str):
    try:
        resultados = siete.buscar(palabra_clave)
        return resultados.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar: {str(e)}")

@router.get("/divisas/convertir")
def convertir_divisa(codigo_serie: str, fecha: str, monto: float):
    """
    fecha en formato: YYYY-MM-DD
    """
    try:
        df = siete.cuadro(series=[codigo_serie], desde=fecha, hasta=fecha, frecuencia="D")
        if df.empty or df[codigo_serie].isna().all():
            raise HTTPException(status_code=404, detail="No se encontró valor para esa fecha.")
        
        valor_cambio = df[codigo_serie].values[0]
        convertido = monto * valor_cambio

        return {
            "fecha": fecha,
            "codigo_serie": codigo_serie,
            "tipo_cambio": valor_cambio,
            "monto_original": monto,
            "monto_convertido": convertido
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al convertir: {str(e)}")