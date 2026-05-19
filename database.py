import sqlite3
import json
from datetime import datetime

# Nombre del fichero de base de datos — se crea automáticamente si no existe
DB_NAME = "buloscan.db"


def get_connection():
    """
    Abre y devuelve una conexión a la base de datos SQLite.
    row_factory permite acceder a las columnas por nombre (fila["titulo"])
    en lugar de por índice (fila[0]).
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Crea las tablas de la base de datos si no existen todavía.
    Se llama una vez al arrancar el servidor FastAPI.

    Tablas:
        noticias       — Almacena cada noticia analizada con su veredicto.
        blockchain_log — Almacena cada bloque generado tras un análisis.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla principal: una fila por noticia analizada
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS noticias (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo       TEXT NOT NULL,
            descripcion  TEXT,
            url          TEXT UNIQUE,
            fuente       TEXT,
            autor        TEXT,
            publicada_en TEXT,
            imagen_url   TEXT,
            veredicto    TEXT NOT NULL,
            score_fake   REAL NOT NULL,
            analizada_en TEXT NOT NULL
        )
    """)

    # Tabla de auditoría: un bloque por cada análisis registrado en la cadena
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blockchain_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            block_index   INTEGER NOT NULL,
            noticia_url   TEXT,
            veredicto     TEXT,
            hash          TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            nonce         INTEGER NOT NULL,
            timestamp     TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente.")


# =============================================================================
# OPERACIONES SOBRE LA TABLA noticias
# =============================================================================

def guardar_noticia(noticia):
    """
    Inserta una noticia analizada en la base de datos.
    Si la URL ya existe (noticia duplicada), la ignora sin error.

    Args:
        noticia (dict): Debe contener:
            titulo, descripcion, url, fuente, autor,
            publicada_en, imagen_url, veredicto, score_fake.
    
    Returns:
        int | None: ID de la fila insertada, o None si era duplicada.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO noticias 
            (titulo, descripcion, url, fuente, autor, publicada_en, imagen_url, veredicto, score_fake, analizada_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            noticia.get("titulo"),
            noticia.get("descripcion"),
            noticia.get("url"),
            noticia.get("fuente"),
            noticia.get("autor"),
            noticia.get("publicada_en"),
            noticia.get("imagen_url"),
            noticia.get("veredicto"),
            noticia.get("score_fake"),
            datetime.now().isoformat()
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def obtener_noticias(limite=50):
    """
    Devuelve las últimas noticias analizadas ordenadas por más reciente.

    Args:
        limite (int): Máximo de noticias a devolver. Por defecto 50.

    Returns:
        list[dict]: Lista de noticias como diccionarios.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM noticias
        ORDER BY analizada_en DESC
        LIMIT ?
    """, (limite,))

    filas = cursor.fetchall()
    conn.close()
    return [dict(fila) for fila in filas]


def obtener_estadisticas():
    """
    Calcula estadísticas globales sobre las noticias analizadas.
    Se usa para mostrar los contadores en el dashboard del frontend.

    Returns:
        dict: Total de noticias, cuántas son fiables, sospechosas y falsas.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM noticias")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM noticias WHERE veredicto = 'FIABLE'")
    fiables = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM noticias WHERE veredicto = 'SOSPECHOSA'")
    sospechosas = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM noticias WHERE veredicto = 'FALSA'")
    falsas = cursor.fetchone()[0]

    conn.close()
    return {
        "total": total,
        "fiables": fiables,
        "sospechosas": sospechosas,
        "falsas": falsas
    }


def buscar_noticias(query):
    """
    Busca noticias cuyo título o descripción contenga el texto indicado.

    Args:
        query (str): Texto a buscar.

    Returns:
        list[dict]: Noticias que coinciden con la búsqueda.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM noticias
        WHERE titulo LIKE ? OR descripcion LIKE ?
        ORDER BY analizada_en DESC
    """, (f"%{query}%", f"%{query}%"))

    filas = cursor.fetchall()
    conn.close()
    return [dict(fila) for fila in filas]


# =============================================================================
# OPERACIONES SOBRE LA TABLA blockchain_log
# =============================================================================

def guardar_bloque(bloque):
    """
    Guarda el registro de un bloque de la cadena en la base de datos.
    Permite consultar el historial blockchain sin tener la cadena en memoria.

    Args:
        bloque (dict): Resultado de Block.to_dict(). Debe contener:
            index, analysis_data, hash, previous_hash, nonce, timestamp.
    """
    conn = get_connection()
    cursor = conn.cursor()

    analysis = bloque.get("analysis_data", {})

    cursor.execute("""
        INSERT INTO blockchain_log
        (block_index, noticia_url, veredicto, hash, previous_hash, nonce, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        bloque.get("index"),
        analysis.get("url"),
        analysis.get("veredicto"),
        bloque.get("hash"),
        bloque.get("previous_hash"),
        bloque.get("nonce"),
        str(bloque.get("timestamp"))
    ))

    conn.commit()
    conn.close()


def obtener_blockchain_log():
    """
    Devuelve todos los bloques registrados ordenados por índice.

    Returns:
        list[dict]: Historial completo de la cadena de bloques.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM blockchain_log
        ORDER BY block_index ASC
    """)

    filas = cursor.fetchall()
    conn.close()
    return [dict(fila) for fila in filas]
