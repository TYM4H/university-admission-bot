from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings
from app.services.embedding_service import embedding_service
from app.rag.qdrant_client import qdrant_client


class VectorStore:
    def create_collection(self):
        collections = qdrant_client.get_collections().collections
        collection_names = {collection.name for collection in collections}

        if settings.qdrant_collection in collection_names:
            return

        qdrant_client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=embedding_service.vector_size,
                distance=Distance.COSINE,
            ),
        )

    def upload_documents(self, documents: list[dict], embeddings: list[list[float]]):
        points = []

        for index, (document, embedding) in enumerate(zip(documents, embeddings), start=1):
            points.append(
                PointStruct(
                    id=index,
                    vector=embedding,
                    payload={
                        "text": document["text"],
                        **document["metadata"],
                    },
                )
            )

        qdrant_client.upsert(
            collection_name=settings.qdrant_collection,
            points=points,
        )


vector_store = VectorStore()