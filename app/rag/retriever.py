import logging

from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.core.config import settings
from app.services.embedding_service import embedding_service
from app.rag.qdrant_client import qdrant_client


logger = logging.getLogger("rag")


class Retriever:
    def search(
        self,
        query: str,
        faq_limit: int = 10,
        docs_limit: int = 3,
        faq_score_threshold: float = 0.50,
        docs_score_threshold: float = 0.72,
    ) -> list[dict]:
        logger.info(f"QUERY: {query}")

        if not query:
            return []

        query_vector = embedding_service.embed_query(query)

        faq_results = self._search_by_doc_type(
            query_vector=query_vector,
            doc_type="faq",
            limit=faq_limit,
            score_threshold=faq_score_threshold,
        )

        docs_results = self._search_other_documents(
            query_vector=query_vector,
            limit=docs_limit,
            score_threshold=docs_score_threshold,
        )

        logger.info(f"FAQ results: {len(faq_results)}")
        logger.info(f"Docs results: {len(docs_results)}")

        for r in faq_results:
            logger.info(
                f"FAQ MATCH | score={r['score']:.3f} | source={r['source']} | chunk={r['chunk_index']}"
            )

        for r in docs_results:
            logger.info(
                f"DOC MATCH | score={r['score']:.3f} | source={r['source']} | chunk={r['chunk_index']}"
            )

        if faq_results:
            logger.info("Returning FAQ results only")
            return faq_results[:2]

        logger.info("Returning DOC results only")
        return docs_results[:2]

    def _search_by_doc_type(
        self,
        query_vector: list[float],
        doc_type: str,
        limit: int,
        score_threshold: float,
    ) -> list[dict]:
        results = qdrant_client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            limit=limit,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="doc_type",
                        match=MatchValue(value=doc_type),
                    )
                ]
            ),
        ).points

        return self._convert_results(results, score_threshold)

    def _search_other_documents(
        self,
        query_vector: list[float],
        limit: int,
        score_threshold: float,
    ) -> list[dict]:
        results = qdrant_client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            limit=limit,
            query_filter=Filter(
                must_not=[
                    FieldCondition(
                        key="doc_type",
                        match=MatchValue(value="faq"),
                    )
                ]
            ),
        ).points

        return self._convert_results(results, score_threshold)

    def _convert_results(self, results, score_threshold: float) -> list[dict]:
        documents = []

        for result in results:
            if result.score < score_threshold:
                continue

            payload = result.payload or {}

            documents.append(
                {
                    "text": payload.get("text", ""),
                    "source": payload.get("source", ""),
                    "page": payload.get("page"),
                    "chunk_index": payload.get("chunk_index"),
                    "doc_type": payload.get("doc_type", "document"),
                    "question": payload.get("question", ""),
                    "score": result.score,
                }
            )

        return documents


retriever = Retriever()