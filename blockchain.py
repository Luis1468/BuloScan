import time
import hashlib
import json


# =============================================================================
# BLOQUE
# Representa un registro individual dentro de la cadena de BuloScan.
# En lugar de certificados académicos (ejemplo del profesor),
# aquí cada bloque guarda el resultado de analizar una noticia.
# =============================================================================

class Block:
    """
    Bloque individual de la cadena de BuloScan.

    Atributos:
        index (int): Posición en la cadena. 0 = bloque génesis.
        timestamp (float): Momento de creación del bloque.
        analysis_data (dict): Resultado del análisis de la noticia.
        previous_hash (str): Hash del bloque anterior (enlaza la cadena).
        nonce (int): Contador usado en el Proof of Work.
        hash (str): Hash SHA-256 de este bloque.
    """

    def __init__(self, index, analysis_data, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.analysis_data = analysis_data  # Datos del análisis de la noticia
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self):
        """
        Calcula el hash SHA-256 del bloque.
        Cualquier cambio en los datos produce un hash completamente distinto,
        garantizando la integridad del registro.
        """
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "analysis_data": self.analysis_data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        """Convierte el bloque a diccionario para guardarlo en SQLite o devolverlo como JSON."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "analysis_data": self.analysis_data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }


# =============================================================================
# CADENA
# Gestiona la lista de bloques: crear el génesis, añadir análisis y validar.
# Mismo patrón que certificate_chain.py del profesor.
# =============================================================================

class BuloScanChain:
    """
    Cadena de bloques de BuloScan.

    Cada análisis de noticia queda registrado de forma inmutable.
    Si alguien intenta modificar un registro antiguo, la validación
    detecta la manipulación automáticamente.
    """

    DIFFICULTY = 2  # Ceros iniciales requeridos en el hash (2 = rápido para demo)

    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """Crea el bloque inicial de la cadena. No tiene bloque anterior (previous_hash = '0')."""
        genesis_data = {
            "titulo": "BuloScan Genesis Block",
            "url": "N/A",
            "fuente": "N/A",
            "veredicto": "SISTEMA",
            "score_fake": 0.0
        }
        genesis_block = Block(0, genesis_data, "0")
        self.chain.append(self.proof_of_work(genesis_block))

    def get_last_block(self):
        """Devuelve el último bloque de la cadena."""
        return self.chain[-1]

    def add_analysis(self, analysis_data):
        """
        Registra un nuevo análisis de noticia en la cadena.

        Args:
            analysis_data (dict): Debe incluir titulo, url, fuente, veredicto, score_fake.

        Returns:
            Block: El bloque minado y añadido a la cadena.
        """
        last_block = self.get_last_block()
        new_block = Block(
            index=last_block.index + 1,
            analysis_data=analysis_data,
            previous_hash=last_block.hash
        )
        mined_block = self.proof_of_work(new_block)
        self.chain.append(mined_block)
        return mined_block

    def proof_of_work(self, block):
        """
        Mina el bloque incrementando el nonce hasta que el hash
        empiece por el número de ceros definido en DIFFICULTY.
        """
        while not block.hash.startswith("0" * self.DIFFICULTY):
            block.nonce += 1
            block.hash = block.compute_hash()
        return block

    def is_chain_valid(self):
        """
        Verifica la integridad de toda la cadena bloque a bloque.
        Comprueba que ningún bloque fue modificado y que los enlaces son correctos.

        Returns:
            bool: True si la cadena es íntegra, False si fue manipulada.
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # El hash almacenado debe coincidir con el recalculado
            if current.hash != current.compute_hash():
                return False

            # El enlace con el bloque anterior debe ser correcto
            if current.previous_hash != previous.hash:
                return False

        return True

    def to_list(self):
        """Devuelve toda la cadena como lista de diccionarios."""
        return [block.to_dict() for block in self.chain]

    def __len__(self):
        return len(self.chain)

    def __repr__(self):
        return f"BuloScanChain(bloques={len(self.chain)}, valida={self.is_chain_valid()})"
