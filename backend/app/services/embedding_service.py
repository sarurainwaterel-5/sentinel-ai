from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.model = SentenceTransformer(
            self.model_name,
            local_files_only=True
        )

    def generate_embedding(self, text: str):
        return self.model.encode(text).tolist()

    def get_dimension(self):
        return self.model.get_sentence_embedding_dimension()

    def get_model_name(self):
        return self.model_name
