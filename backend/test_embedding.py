from app.services.embedding_service import EmbeddingService

service = EmbeddingService()

vector = service.generate_embedding(
    "Restart Redis if latency exceeds 200 milliseconds."
)

print(len(vector))
print(vector[:10])
