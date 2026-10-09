import os
from functools import lru_cache
import torch
from sentence_transformers import SentenceTransformer

@lru_cache(maxsize=1)
def _load_model(model_name):
    # Avoid oversubscribing desktop CPUs during small local embedding requests.
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    return SentenceTransformer(model_name, local_files_only=True)

class EmbeddingService:
    def __init__(self):
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"

    @property
    def model(self):
        # Share one local model per process and load it only when needed.
        return _load_model(self.model_name)

    def generate_embedding(self, text: str):
        return self.model.encode(text).tolist()

    def generate_embeddings(self, texts: list[str]):
        if not texts:
            return []
        return self.model.encode(texts, batch_size=32).tolist()

    def get_dimension(self):
        return self.model.get_embedding_dimension()

    def get_model_name(self):
        return self.model_name
