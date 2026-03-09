from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer("BAAI/bge-m3")
        self.vector_size = 1024

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=4,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        embedding = self.model.encode(
            [text],
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=1,
        )[0]
        return embedding.tolist()


embedding_service = EmbeddingService()