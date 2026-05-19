import requests
from datetime import datetime

# URL base de NewsAPI — el único endpoint que usamos
NEWSAPI_URL = "https://newsapi.org/v2/everything"

# Fuentes conocidas y fiables — se usan en el analizador para puntuar credibilidad
FUENTES_FIABLES = [
    "elpais.com", "elmundo.es", "bbc.com", "bbc.co.uk",
    "reuters.com", "20minutos.es", "rtve.es", "lavanguardia.com",
    "elconfidencial.com", "abc.es", "marca.com", "expansion.com"
]


class NewsSensor:
    """
    Simula un sensor IoT que "lee" noticias desde NewsAPI.

    Mismo concepto que el Sensor del profesor (sensor.py en el invernadero):
    en lugar de leer temperatura o humedad, lee titulares de noticias reales.

    Atributos:
        name (str): Nombre del sensor / temática que monitoriza.
        query (str): Palabra clave para buscar en NewsAPI.
        language (str): Idioma de las noticias ('es' = español, 'en' = inglés).
        api_key (str): Clave de acceso a NewsAPI.
    """

    def __init__(self, name, query, api_key, language="es"):
        self.name = name
        self.query = query
        self.api_key = api_key
        self.language = language

    def read(self, max_results=10):
        """
        Realiza una lectura del sensor — llama a NewsAPI y devuelve noticias.
        Equivale al método read() del Sensor del profesor.

        Args:
            max_results (int): Número máximo de noticias a obtener.

        Returns:
            list[dict]: Lista de noticias normalizadas, listas para analizar.
                        Lista vacía si hay error de conexión o API key inválida.
        """
        try:
            response = requests.get(NEWSAPI_URL, params={
                "q": self.query,
                "language": self.language,
                "pageSize": max_results,
                "sortBy": "publishedAt",
                "apiKey": self.api_key
            }, timeout=10)

            # Si la API devuelve error HTTP lo registramos y devolvemos vacío
            if response.status_code != 200:
                print(f"⚠️  Sensor '{self.name}' error {response.status_code}: {response.json().get('message')}")
                return []

            articulos = response.json().get("articles", [])
            return [self._normalizar(a) for a in articulos if a.get("title")]

        except requests.exceptions.ConnectionError:
            print(f"❌ Sensor '{self.name}': sin conexión a internet.")
            return []
        except requests.exceptions.Timeout:
            print(f"❌ Sensor '{self.name}': timeout al conectar con NewsAPI.")
            return []

    def _normalizar(self, articulo):
        """
        Transforma el JSON crudo de NewsAPI al formato interno de BuloScan.
        Así el resto del sistema siempre trabaja con la misma estructura,
        independientemente de cambios en la API externa.

        Args:
            articulo (dict): Artículo tal como lo devuelve NewsAPI.

        Returns:
            dict: Noticia normalizada con campos homogéneos.
        """
        fuente = articulo.get("source", {}).get("name", "Desconocida")
        url = articulo.get("url", "")

        # Extraemos el dominio de la URL para comparar con fuentes fiables
        dominio = self._extraer_dominio(url)

        return {
            "titulo":       articulo.get("title", "Sin título"),
            "descripcion":  articulo.get("description", ""),
            "url":          url,
            "fuente":       fuente,
            "dominio":      dominio,
            "autor":        articulo.get("author", "Desconocido"),
            "publicada_en": articulo.get("publishedAt", ""),
            "imagen_url":   articulo.get("urlToImage", ""),
            "contenido":    articulo.get("content", ""),
            "es_fiable":    dominio in FUENTES_FIABLES  # Pista para el analizador
        }

    def _extraer_dominio(self, url):
        """
        Extrae el dominio de una URL para verificar si es fuente fiable.
        Ejemplo: 'https://www.elpais.com/noticia' → 'elpais.com'

        Args:
            url (str): URL completa del artículo.

        Returns:
            str: Dominio limpio o cadena vacía si la URL no es válida.
        """
        try:
            # Quitamos el protocolo y el www. si existe
            dominio = url.split("//")[-1].split("/")[0]
            dominio = dominio.replace("www.", "")
            return dominio
        except Exception:
            return ""

    def __repr__(self):
        return f"NewsSensor(name='{self.name}', query='{self.query}', language='{self.language}')"
