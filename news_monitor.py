from news.news_fetcher import NewsSensor

# Temas que BuloScan monitoriza por defecto
SENSORES_DEFAULT = [
    {"name": "Política",    "query": "política españa gobierno"},
    {"name": "Salud",       "query": "salud medicina vacuna"},
    {"name": "Tecnología",  "query": "tecnología inteligencia artificial"},
    {"name": "Viral",       "query": "viral bulo fake news desinformación"},
]

class NewsMonitor:

    def __init__(self, api_key):
        self.api_key = api_key
        self.sensores = []
        self._crear_sensores_default()

    def _crear_sensores_default(self):
        for config in SENSORES_DEFAULT:
            sensor = NewsSensor(
                name=config["name"],
                query=config["query"],
                api_key=self.api_key
            )
            self.sensores.append(sensor)
        print(f" NewsMonitor iniciado con {len(self.sensores)} sensores.")

    def agregar_sensor(self, name, query, language="es"):
        sensor = NewsSensor(name=name, query=query, api_key=self.api_key, language=language)
        self.sensores.append(sensor)
        print(f"➕ Sensor '{name}' añadido al monitor.")

    def leer_todos(self, max_por_sensor=5):
        todas = []
        urls_vistas = set()  # Evitar duplicados si varios sensores traen la misma noticia

        for sensor in self.sensores:
            print(f" Leyendo sensor '{sensor.name}'...")
            noticias = sensor.read(max_results=max_por_sensor)

            for noticia in noticias:
                if noticia["url"] not in urls_vistas:
                    urls_vistas.add(noticia["url"])
                    todas.append(noticia)

            print(f"   → {len(noticias)} noticias recibidas.")

        print(f"\n Total noticias únicas recogidas: {len(todas)}")
        return todas

    def leer_sensor(self, name, max_results=10):
        for sensor in self.sensores:
            if sensor.name.lower() == name.lower():
                return sensor.read(max_results=max_results)

        print(f"  Sensor '{name}' no encontrado.")
        return []

    def leer_query_libre(self, query, language="es", max_results=10):
        sensor_temporal = NewsSensor(
            name="Búsqueda libre",
            query=query,
            api_key=self.api_key,
            language=language
        )
        return sensor_temporal.read(max_results=max_results)

    def listar_sensores(self):
        return [{"name": s.name, "query": s.query} for s in self.sensores]

    def __repr__(self):
        return f"NewsMonitor(sensores={len(self.sensores)}, api_key={'*' * 8})"
