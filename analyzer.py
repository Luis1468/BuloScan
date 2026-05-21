import re
from textblob import TextBlob
from news.news_fetcher import FUENTES_FIABLES

# DICCIONARIOS DE ANÁLISIS

# Palabras y frases que aparecen frecuentemente en noticias falsas o sensacionalistas
PALABRAS_SOSPECHOSAS = [
    # Alarmismo y urgencia falsa
    "urgente", "exclusivo", "increíble", "impactante", "sorprendente",
    "shockeante", "brutal", "devastador", "catastrófico", "apocalíptico",
    # Conspiraciones y ocultamiento
    "lo que los medios ocultan", "te sorprenderá", "nadie te cuenta",
    "el gobierno oculta", "censurado", "prohibido", "lo que no quieren que sepas",
    "la verdad que esconden", "conspiracion", "conspíración",
    # Llamadas a compartir
    "comparte antes de que lo borren", "difunde esto", "pasa esto a todos",
    "antes de que lo censuren", "comparte urgente",
    # Fuentes vagas
    "fuentes anónimas", "según algunos expertos", "se rumorea",
    "dicen que", "hay quien dice", "algunos afirman",
    # Clickbait clásico
    "no vas a creer", "te dejará sin palabras", "fliparás",
    "alucinante", "esto es lo que pasó", "lo que nadie esperaba",
    # Pseudociencia
    "cura milagrosa", "los médicos no quieren", "remedio casero",
    "big pharma", "veneno en tu", "chemtrails", "microchip"
]

# Palabras que sugieren rigor periodístico y credibilidad
PALABRAS_CREDIBLES = [
    # Fuentes verificables
    "según el ministerio", "declaró el portavoz", "confirmó el gobierno",
    "informó reuters", "según datos oficiales", "fuentes oficiales",
    "el informe señala", "el estudio concluye", "investigadores de",
    # Lenguaje formal y preciso
    "por ciento", "millones de euros", "en declaraciones a",
    "en rueda de prensa", "según el instituto", "datos del ine",
    "el tribunal", "el parlamento", "la comisión europea",
    # Atribución clara
    "ha declarado", "ha confirmado", "ha anunciado", "ha publicado"
]

# Patrones de escritura asociados a desinformación
PATRONES_SOSPECHOSOS = [
    r"[A-ZÁÉÍÓÚ\s]{6,}",        # Texto en MAYÚSCULAS excesivas (6+ chars)
    r"!{2,}",                    # Múltiples signos de exclamación !!
    r"\?{2,}",                   # Múltiples signos de interrogación ??
    r"\.{3,}",                   # Puntos suspensivos excesivos ...
]

# Dominios conocidos por difundir bulos o contenido no verificado
DOMINIOS_SOSPECHOSOS = [
    "noticiasfalsas", "elmundohoy", "infovaticana",
    "lanoticia1", "periodista-digital", "actuall",
    "okdiario", "elboletin", "diariocritico"
]

# Afirmaciones físicamente imposibles o históricamente absurdas
AFIRMACIONES_IMPOSIBLES = [
    # Personas muertas que "siguen vivas"
    "sigue vivo", "está vivo", "continúa vivo", "aún vive", "todavía vive",
    "no murió", "no está muerto", "fingió su muerte", "finge su muerte",
    # Eventos físicamente imposibles
    "viaja en el tiempo", "viaje en el tiempo", "inmortal", "ha resucitado",
    "resucitó", "volvió de la muerte", "nunca murió",
    # Conspiraciones clásicas
    "tierra plana", "la tierra es plana", "aterrizaje lunar fue falso",
    "el hombre nunca llegó a la luna", "reptilianos", "illuminati controlan",
    "5g provoca", "chips en las vacunas", "chemtrails son",
    # Cifras o hechos absurdos
    "ganó por 100%", "cero muertes en", "ha curado el cáncer completamente",
]

# ANALIZADOR PRINCIPAL

class Analyzer:
    # Umbrales para asignar el veredicto final
    UMBRAL_FIABLE     = 0.38   # Por debajo → FIABLE
    UMBRAL_SOSPECHOSA = 0.58   # Entre 0.38 y 0.58 → SOSPECHOSA
                               # Por encima → FALSA

    def analizar(self, noticia):
        titulo      = noticia.get("titulo", "")
        descripcion = noticia.get("descripcion", "")
        dominio     = noticia.get("dominio", "")
        es_fiable   = noticia.get("es_fiable", False)

        # Texto completo para analizar — unimos título y descripción
        texto = f"{titulo} {descripcion}".lower()

        # Los tres análisis independientes 
        score_fuente,      detalle_fuente      = self._analizar_fuente(dominio, es_fiable)
        score_linguistico, detalle_linguistico = self._analizar_linguistico(titulo, texto)
        score_sentimiento, detalle_sentimiento = self._analizar_sentimiento(texto)

        score_fake = (
            score_fuente      * 0.30 +
            score_linguistico * 0.50 +
            score_sentimiento * 0.20
        )
        score_fake = round(min(max(score_fake, 0.0), 1.0), 4)  # Clamping 0-1

        # Veredicto según umbrales 
        if score_fake < self.UMBRAL_FIABLE:
            veredicto = "FIABLE"
        elif score_fake < self.UMBRAL_SOSPECHOSA:
            veredicto = "SOSPECHOSA"
        else:
            veredicto = "FALSA"

        # Resultado completo
        return {
            **noticia,  # Todos los campos originales de la noticia
            "score_fake": score_fake,
            "veredicto":  veredicto,
            "detalle": {
                "fuente":      detalle_fuente,
                "linguistico": detalle_linguistico,
                "sentimiento": detalle_sentimiento
            }
        }

    # FACTOR 1: ANÁLISIS DE FUENTE

    def _analizar_fuente(self, dominio, es_fiable):
        if es_fiable:
            return 0.1, {"resultado": "Fuente conocida y fiable", "dominio": dominio}

        # Dominio sospechoso conocido → penalización máxima
        for sospechoso in DOMINIOS_SOSPECHOSOS:
            if sospechoso in dominio:
                return 0.90, {"resultado": "Dominio sospechoso detectado", "dominio": dominio}

        # Dominio vacío o fuente inventada → bastante sospechoso
        if not dominio or dominio.lower() in ("", "desconocida", "desconocido"):
            return 0.72, {"resultado": "Fuente no identificada", "dominio": "N/A"}

        # Dominio desconocido — no está en ninguna lista → moderadamente sospechoso
        return 0.55, {"resultado": "Fuente desconocida, no verificada", "dominio": dominio}

    # FACTOR 2: ANÁLISIS LINGÜÍSTICO

    def _analizar_linguistico(self, titulo, texto):
        penalizacion  = 0.0
        bonificacion  = 0.0
        hallazgos     = []

        # Detección de afirmaciones físicamente imposibles o históricamente absurdas
        imposibles_encontradas = [a for a in AFIRMACIONES_IMPOSIBLES if a in texto]
        if imposibles_encontradas:
            penalizacion += min(len(imposibles_encontradas) * 0.40, 0.80)
            hallazgos.append(f"Afirmación imposible detectada: {imposibles_encontradas[0]!r}")

        # Buscar palabras sospechosas en el texto
        palabras_encontradas = [p for p in PALABRAS_SOSPECHOSAS if p in texto]
        if palabras_encontradas:
            penalizacion += min(len(palabras_encontradas) * 0.20, 0.70)
            hallazgos.append(f"Palabras sospechosas: {', '.join(palabras_encontradas[:3])}")

        # Buscar palabras que indican rigor periodístico
        palabras_credibles = [p for p in PALABRAS_CREDIBLES if p in texto]
        if palabras_credibles:
            bonificacion += min(len(palabras_credibles) * 0.10, 0.30)
            hallazgos.append(f"Indicadores de rigor: {len(palabras_credibles)}")

        # Detectar patrones de escritura sospechosos en el título original
        for patron in PATRONES_SOSPECHOSOS:
            if re.search(patron, titulo):
                penalizacion += 0.15
                hallazgos.append(f"Patrón sospechoso en título: '{patron}'")
                break  # Un solo patrón es suficiente penalización

        score = round(min(max(0.35 + penalizacion - bonificacion, 0.0), 1.0), 4)

        return score, {
            "resultado": hallazgos if hallazgos else ["Sin indicadores especiales"],
            "penalizacion": round(penalizacion, 4),
            "bonificacion": round(bonificacion, 4)
        }

    # FACTOR 3: ANÁLISIS DE SENTIMIENTO (TextBlob)

    def _analizar_sentimiento(self, texto):
        try:
            blob = TextBlob(texto)
            polaridad    = blob.sentiment.polarity
            subjetividad = blob.sentiment.subjectivity

            # Alta subjetividad → sospechoso
            # Polaridad muy extrema (muy positivo o muy negativo) → sospechoso
            score_subjetividad = subjetividad                    # 0.0 a 1.0
            score_polaridad    = abs(polaridad)                  # 0.0 a 1.0

            score = round((score_subjetividad * 0.6 + score_polaridad * 0.4), 4)

            return score, {
                "polaridad":    round(polaridad, 4),
                "subjetividad": round(subjetividad, 4),
                "interpretacion": self._interpretar_sentimiento(subjetividad, polaridad)
            }

        except Exception:
            # Si TextBlob falla (texto vacío, encoding raro) devolvemos neutro
            return 0.5, {"polaridad": 0, "subjetividad": 0.5, "interpretacion": "No analizable"}

    def _interpretar_sentimiento(self, subjetividad, polaridad):
        # Convierte los valores numéricos de TextBlob en texto
        if subjetividad > 0.7:
            return "Texto muy subjetivo y emotivo — señal de alerta"
        elif subjetividad > 0.4:
            return "Texto moderadamente subjetivo"
        else:
            return "Texto objetivo y neutral — señal positiva"


# FUNCIÓN DE ACCESO RÁPIDO

_analyzer = Analyzer()

def analizar_noticia(noticia):
    return _analyzer.analizar(noticia)
