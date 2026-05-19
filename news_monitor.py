from news_fetcher import NewsSensor

# Temas que BuloScan monitoriza por defecto
# Equivale a los sensores del invernadero del profesor:
# temperatura, humedad, luz → política, salud, tecnología, viral
SENSORES_DEFAULT = [
    {"name": "Política",    "query": "política españa gobierno"},
    {"name": "Salud",       "query": "salud medicina vacuna"},
    {"name": "Tecnología",  "query": "tecnología inteligencia artificial"},
    {"name": "Viral",       "query": "viral bulo fake news desinformación"},
]


class NewsMonitor:
    """
    Gestiona múltiples sensores de noticias y coordina sus lecturas.

    Mismo concepto que la clase Greenhouse del profesor:
    en lugar de gestionar sensores físicos de temperatura y humedad,
    gestiona sensores de noticias por temática.

    Atributos:
        api_key (str): Clave de NewsAPI compartida por todos los sensores.
        sensores (list[NewsSensor]): Lista de sensores activos.
    """

    def __init__(self, api_key):
        self.api_key = api_key
        self.sensores = []
        self._crear_sensores_default()

    def _crear_sensores_default(self):
        """
        Crea los sensores predefinidos al inicializar el monitor.
        Equivale al __init__ de Greenhouse donde el profesor instancia
        temperature_sensor, humidity_sensor, etc.
        """
        for config in SENSORES_DEFAULT:
            sensor = NewsSensor(
                name=config["name"],
                query=config["query"],
                api_key=self.api_key
            )
            self.sensores.append(sensor)
        print(f"✅ NewsMonitor iniciado con {len(self.sensores)} sensores.")

    def agregar_sensor(self, name, query, language="es"):
        """
        Añade un sensor personalizado al monitor.
        Permite ampliar la cobertura sin tocar el código base.

        Args:
            name (str): Nombre descriptivo del sensor.
            query (str): Término de búsqueda para NewsAPI.
            language (str): Idioma de las noticias.
        """
        sensor = NewsSensor(name=name, query=query, api_key=self.api_key, language=language)
        self.sensores.append(sensor)
        print(f"➕ Sensor '{name}' añadido al monitor.")

    def leer_todos(self, max_por_sensor=5):
        """
        Lee noticias de todos los sensores activos.
        Equivale a read_all_sensors() del Greenhouse del profesor.

        Args:
            max_por_sensor (int): Noticias máximas por sensor.

        Returns:
            list[dict]: Todas las noticias recogidas, sin duplicados por URL.
        """
        todas = []
        urls_vistas = set()  # Evitar duplicados si varios sensores traen la misma noticia

        for sensor in self.sensores:
            print(f"📡 Leyendo sensor '{sensor.name}'...")
            noticias = sensor.read(max_results=max_por_sensor)

            for noticia in noticias:
                if noticia["url"] not in urls_vistas:
                    urls_vistas.add(noticia["url"])
                    todas.append(noticia)

            print(f"   → {len(noticias)} noticias recibidas.")

        print(f"\n📦 Total noticias únicas recogidas: {len(todas)}")
        return todas

    def leer_sensor(self, name, max_results=10):
        """
        Lee noticias de un sensor concreto por su nombre.
        Útil cuando el usuario busca un tema específico desde el frontend.

        Args:
            name (str): Nombre del sensor a consultar.
            max_results (int): Número máximo de noticias.

        Returns:
            list[dict]: Noticias del sensor, o lista vacía si no existe.
        """
        for sensor in self.sensores:
            if sensor.name.lower() == name.lower():
                return sensor.read(max_results=max_results)

        print(f"⚠️  Sensor '{name}' no encontrado.")
        return []

    def leer_query_libre(self, query, language="es", max_results=10):
        """
        Crea un sensor temporal para buscar cualquier término libre.
        Se usa cuando el usuario escribe una búsqueda personalizada
        en el frontend sin necesidad de crear un sensor permanente.

        Args:
            query (str): Término de búsqueda libre.
            language (str): Idioma de las noticias.
            max_results (int): Número máximo de noticias.

        Returns:
            list[dict]: Noticias encontradas para ese término.
        """
        sensor_temporal = NewsSensor(
            name="Búsqueda libre",
            query=query,
            api_key=self.api_key,
            language=language
        )
        return sensor_temporal.read(max_results=max_results)

    def listar_sensores(self):
        """
        Devuelve la lista de sensores activos con su configuración.
        Se usa para mostrar las categorías disponibles en el frontend.

        Returns:
            list[dict]: Nombre y query de cada sensor activo.
        """
        return [{"name": s.name, "query": s.query} for s in self.sensores]

    def __repr__(self):
        return f"NewsMonitor(sensores={len(self.sensores)}, api_key={'*' * 8})"
