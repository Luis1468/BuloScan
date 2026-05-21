import time
import hashlib
import json

# BLOQUE

class Block:
    def __init__(self, index, analysis_data, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.analysis_data = analysis_data  # Datos del análisis de la noticia
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "analysis_data": self.analysis_data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        # Convierte el bloque a diccionario para guardarlo en SQLite o devolverlo como JSON.
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "analysis_data": self.analysis_data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

# CADENA

class BuloScanChain:
    DIFFICULTY = 2  # Ceros iniciales requeridos en el hash (2 = rápido para demo)

    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        # Crea el bloque inicial de la cadena. No tiene bloque anterior (previous_hash = '0').
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
        # Devuelve el último bloque de la cadena.
        return self.chain[-1]

    def add_analysis(self, analysis_data):
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
        while not block.hash.startswith("0" * self.DIFFICULTY):
            block.nonce += 1
            block.hash = block.compute_hash()
        return block

    def is_chain_valid(self):
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
        # Devuelve toda la cadena como lista de diccionarios.
        return [block.to_dict() for block in self.chain]

    def __len__(self):
        return len(self.chain)

    def __repr__(self):
        return f"BuloScanChain(bloques={len(self.chain)}, valida={self.is_chain_valid()})"
