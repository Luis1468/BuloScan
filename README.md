# BuloScan — Detector de Noticias Falsas

BuloScan es una aplicación web que analiza noticias en tiempo real y determina si son **fiables**, **sospechosas** o **falsas**. Combina análisis lingüístico, análisis de sentimiento y verificación de fuentes para calcular una puntuación de credibilidad. Cada análisis queda registrado de forma inmutable en una cadena de bloques propia.

---

## Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| **FastAPI** | Backend y API REST |
| **TextBlob** | Análisis de sentimiento del texto |
| **SQLite** | Base de datos local para persistir los análisis |
| **Blockchain** | Registro inmutable de cada análisis realizado |
| **NewsAPI** | Fuente de noticias reales para búsquedas por tema |
| **HTML / CSS / JS** | Frontend sin frameworks adicionales |

---

## Estructura del proyecto

```
buloscan/
├── main.py               # Arranque del servidor y endpoints de la API
├── index.html            # Interfaz web
├── requirements.txt      # Dependencias Python
│
├── core/
│   ├── analyzer.py       # Lógica de análisis de credibilidad
│   ├── blockchain.py     # Implementación de la cadena de bloques
│   └── database.py       # Operaciones con la base de datos SQLite
│
├── news/
│   ├── news_fetcher.py   # Sensor de noticias (llamadas a NewsAPI)
│   └── news_monitor.py   # Gestor de múltiples sensores por temática
│
└── data/
    └── buloscan.db       # Base de datos (se genera automáticamente)
```

---

## Instalación y arranque

**1. Clonar o descargar el proyecto**

**2. Instalar dependencias**
```bash
pip install -r requirements.txt
```

**3. Arrancar el servidor**
```bash
python -m uvicorn main:app --reload
```

**4. Abrir en el navegador**
```
http://127.0.0.1:8000
```

---

## Cómo usarlo

**Analizar una noticia manualmente**
Pega el texto de cualquier noticia en el campo de texto, indica la fuente y URL si las tienes, y pulsa *Analizar*. BuloScan devuelve un veredicto y el desglose del análisis.

**Buscar noticias por tema**
Escribe un tema (por ejemplo: *vacunas*, *elecciones*, *economía*) y BuloScan buscará noticias reales en NewsAPI y las analizará automáticamente.

**Historial**
Todos los análisis realizados quedan guardados y se muestran en el panel de la derecha con su veredicto y puntuación.

---

## Cómo funciona el análisis

Cada noticia se evalúa con tres factores independientes que se combinan en una puntuación final (`score_fake`) entre 0.0 y 1.0:

**1. Análisis de fuente (30%)**
Se comprueba el dominio de la noticia contra una lista de medios fiables conocidos (elpais.com, bbc.com, reuters.com...) y contra una lista de dominios sospechosos. Si la fuente es desconocida, se penaliza moderadamente.

**2. Análisis lingüístico (50%)**
Se buscan en el texto palabras y patrones asociados a desinformación: alarmismo, llamadas a compartir, fuentes vagas, mayúsculas excesivas, signos de exclamación repetidos o afirmaciones imposibles. También se bonifica el uso de lenguaje periodístico riguroso.

**3. Análisis de sentimiento (20%)**
Usando TextBlob se mide la subjetividad y polaridad emocional del texto. Las noticias falsas tienden a ser muy emotivas y subjetivas; una noticia objetiva puntúa mejor.

**Veredicto final**

| Score | Veredicto |
|---|---|
| < 0.38 | FIABLE |
| 0.38 – 0.58 | SOSPECHOSA |
| > 0.58 | FALSA |

---

## Endpoints principales de la API

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/` | Sirve el frontend |
| POST | `/analizar/texto` | Analiza un texto introducido manualmente |
| POST | `/analizar/busqueda` | Busca y analiza noticias por tema en NewsAPI |
| GET | `/analizar/monitor` | Lee todos los sensores y analiza sus noticias |
| GET | `/noticias` | Historial de noticias analizadas |
| GET | `/estadisticas` | Contadores globales del sistema |
| GET | `/blockchain` | Log de todos los bloques registrados |
| GET | `/blockchain/validar` | Verifica la integridad de la cadena |

---

## Autor

**Luis Liébanas Ávila**
