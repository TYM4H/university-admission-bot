from fastembed import TextEmbedding


class EmbeddingService:
    def __init__(self):
        self.model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_size = 384

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = list(self.model.embed(texts))
        return [embedding.tolist() for embedding in embeddings]

    def embed_query(self, text: str) -> list[float]:
        embedding = list(self.model.embed([text]))[0]
        return embedding.tolist()


embedding_service = EmbeddingService()