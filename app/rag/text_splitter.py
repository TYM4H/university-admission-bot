class TextSplitter:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        text = " ".join(text.split())

        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            start = end - self.chunk_overlap

        return chunks

    def split_documents(self, documents: list[dict]) -> list[dict]:
        chunked_documents = []

        for document in documents:
            chunks = self.split_text(document["text"])

            for chunk_index, chunk in enumerate(chunks):
                chunked_documents.append(
                    {
                        "text": chunk,
                        "metadata": {
                            **document["metadata"],
                            "chunk_index": chunk_index,
                        },
                    }
                )

        return chunked_documents


text_splitter = TextSplitter()