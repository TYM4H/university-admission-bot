from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.core.config import settings
from app.services.embedding_service import embedding_service
from app.rag.qdrant_client import qdrant_client


class Retriever:
    def search(
        self,
        query: str,
        faq_limit: int = 3,
        docs_limit: int = 3,
        faq_score_threshold: float = 0.60,
        docs_score_threshold: float = 0.72,
    ) -> list[dict]:
        query = self._normalize_query(query)

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

        if faq_results:
            return faq_results + docs_results

        return docs_results

    def _normalize_query(self, query: str) -> str:
        query = (query or "").strip().lower()

        replacements = {
            "доки": "документы",
            "доки нужны": "какие документы нужны для поступления",
            "общага": "общежитие",
            "есть ли общага": "предоставляется ли общежитие студентам очной формы обучения",
            "есть ли общежитие": "предоставляется ли общежитие студентам очной формы обучения",
            "егэ": "результаты егэ",
            "сколько действует егэ": "сколько лет действуют результаты егэ",
            "госуслуги": "подача документов через госуслуги",
            "можно через госуслуги": "можно ли подать документы через госуслуги",
        }

        for old, new in replacements.items():
            query = query.replace(old, new)

        return query

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
                    "question": payload.get("question"),
                    "score": result.score,
                }
            )

        return documents


retriever = Retriever()