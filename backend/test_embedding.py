from app.services.embedding_service import EmbeddingService

service = EmbeddingService()

vector = service.generate_embedding(
    "Restart Redis if latency exceeds 200 milliseconds."
)

print("Model:", service.get_model_name())
print("Dimension:", service.get_dimension())
print("Vector length:", len(vector))
print("Preview:", vector[:10])
