from sentence_transformers import CrossEncoder


class RerankerService:
    def __init__(self):
        self.model = CrossEncoder("BAAI/bge-reranker-base")

    def rerank(self, query: str, documents: list[dict]) -> list[dict]:
        if not documents:
            return documents

        pairs = [[query, doc["text"]] for doc in documents]
        scores = self.model.predict(pairs)

        reranked = []
        for doc, score in zip(documents, scores):
            new_doc = dict(doc)
            new_doc["rerank_score"] = float(score)
            reranked.append(new_doc)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked


reranker_service = RerankerService()