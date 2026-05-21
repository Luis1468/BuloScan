from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import os

from core.database import (
    init_db,
    guardar_noticia,
    guardar_bloque,
    obtener_noticias,
    obtener_estadisticas,
    obtener_blockchain_log,
    buscar_noticias
)
from core.blockchain import BuloScanChain
from news.news_monitor import NewsMonitor
from core.analyzer import analizar_noticia

# API

NEWSAPI_KEY = "0b13f669dc444645a24787cd14cf9e01"


app = FastAPI(
    title="BuloScan API",
    description="API REST para detección de noticias falsas en tiempo real.",
    version="1.0.0"
)

# CORS permite que el frontend HTML/JS pueda llamar a esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancias globales se crean una vez al arrancar el servidor
cadena    = BuloScanChain()
monitor   = NewsMonitor(api_key=NEWSAPI_KEY)


@app.on_event("startup")
def startup():
    # Se ejecuta automáticamente al arrancar el servidor.
    init_db()
    print("BuloScan API iniciada.")

# Definen qué campos espera la API en las peticiones POST

class TextoRequest(BaseModel):
    # Cuerpo de la petición para analizar un texto libre.
    texto: str
    fuente: Optional[str] = "Desconocida"
    url: Optional[str] = ""


class BusquedaRequest(BaseModel):
    # Cuerpo de la petición para buscar y analizar noticias por tema.
    query: str
    language: Optional[str] = "es"
    max_results: Optional[int] = 10

# ENDPOINTS

@app.get("/")
def root():
    # Sirve el frontend desde la misma carpeta que main.py.
    index = Path(__file__).parent / "index.html"
    return FileResponse(index)

#  ANÁLISIS 

@app.post("/analizar/texto")
def analizar_texto(request: TextoRequest):
    if not request.texto.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")

    # Construimos una noticia artificial con el texto del usuario
    noticia = {
        "titulo":      request.texto[:150],   # Usamos los primeros 150 chars como título
        "descripcion": request.texto,
        "url":         request.url or f"texto-manual-{hash(request.texto)}",
        "fuente":      request.fuente,
        "dominio":     _extraer_dominio(request.url) if request.url else "",
        "autor":       "Introducido manualmente",
        "publicada_en": "",
        "imagen_url":  "",
        "es_fiable":   False
    }

    resultado = analizar_noticia(noticia)
    _registrar_resultado(resultado)
    return resultado

@app.post("/analizar/busqueda")
def analizar_busqueda(request: BusquedaRequest):
    if not NEWSAPI_KEY:
        raise HTTPException(
            status_code=503,
            detail="NewsAPI no configurada. Contacta con el administrador."
        )

    # Obtenemos noticias del monitor IoT con búsqueda libre
    noticias = monitor.leer_query_libre(
        query=request.query,
        language=request.language,
        max_results=request.max_results
    )

    if not noticias:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron noticias para '{request.query}'."
        )

    # Analizamos cada noticia y registramos el resultado
    resultados = []
    for noticia in noticias:
        resultado = analizar_noticia(noticia)
        _registrar_resultado(resultado)
        resultados.append(resultado)

    return resultados

@app.get("/analizar/monitor")
def analizar_monitor(max_por_sensor: int = Query(default=3, ge=1, le=10)):
    if not NEWSAPI_KEY:
        raise HTTPException(
            status_code=503,
            detail="NewsAPI no configurada. Contacta con el administrador."
        )

    noticias  = monitor.leer_todos(max_por_sensor=max_por_sensor)
    resultados = [analizar_noticia(n) for n in noticias]

    for r in resultados:
        _registrar_resultado(r)

    # Estadísticas rápidas de esta lectura
    falsas      = [r for r in resultados if r["veredicto"] == "FALSA"]
    sospechosas = [r for r in resultados if r["veredicto"] == "SOSPECHOSA"]
    fiables     = [r for r in resultados if r["veredicto"] == "FIABLE"]

    return {
        "total_analizadas": len(resultados),
        "falsas":           len(falsas),
        "sospechosas":      len(sospechosas),
        "fiables":          len(fiables),
        "noticias":         resultados
    }

# HISTORIAL Y ESTADÍSTICAS

@app.get("/noticias")
def listar_noticias(limite: int = Query(default=50, ge=1, le=200)):
    return obtener_noticias(limite=limite)

@app.get("/noticias/buscar")
def buscar(q: str = Query(..., min_length=2)):
    resultados = buscar_noticias(q)
    if not resultados:
        return []
    return resultados

@app.get("/estadisticas")
def estadisticas():
    stats = obtener_estadisticas()
    stats["blockchain_bloques"] = len(cadena)
    stats["blockchain_valida"]  = cadena.is_chain_valid()
    return stats

#  BLOCKCHAIN

@app.get("/blockchain")
def listar_blockchain():
    return {
        "total_bloques": len(cadena),
        "cadena_valida": cadena.is_chain_valid(),
        "bloques":       obtener_blockchain_log()
    }

@app.get("/blockchain/validar")
def validar_blockchain():
    valida = cadena.is_chain_valid()
    return {
        "valida":  valida,
        "mensaje": " La cadena es íntegra." if valida else " La cadena fue manipulada."
    }

# SENSORES IoT 

@app.get("/sensores")
def listar_sensores():
    return monitor.listar_sensores()

# FUNCIÓN AUXILIAR INTERNA

def _registrar_resultado(resultado):

    # 1. Guardar en SQLite
    guardar_noticia(resultado)

    # 2. Añadir a la cadena de bloques y guardar el bloque en SQLite
    bloque = cadena.add_analysis({
        "titulo":     resultado.get("titulo"),
        "url":        resultado.get("url"),
        "fuente":     resultado.get("fuente"),
        "veredicto":  resultado.get("veredicto"),
        "score_fake": resultado.get("score_fake")
    })
    guardar_bloque(bloque.to_dict())

def _extraer_dominio(url):
    # Extrae el dominio limpio de una URL.
    try:
        dominio = url.split("//")[-1].split("/")[0]
        return dominio.replace("www.", "")
    except Exception:
        return ""