from pathlib import Path

from app.services.embedding_service import embedding_service
from app.rag.pdf_loader import pdf_loader
from app.rag.text_splitter import text_splitter
from app.rag.vector_store import vector_store


def main():
    data_dir = Path("data/raw")
    pdf_files = list(data_dir.glob("*.pdf"))

    if not pdf_files:
        print("PDF files not found in data/raw")
        return

    all_documents = []

    for pdf_file in pdf_files:
        print(f"Loading {pdf_file.name}")
        documents = pdf_loader.load(str(pdf_file))
        chunked_documents = text_splitter.split_documents(documents)
        all_documents.extend(chunked_documents)

    print(f"Total chunks: {len(all_documents)}")

    texts = [document["text"] for document in all_documents]
    embeddings = embedding_service.embed_documents(texts)

    vector_store.create_collection()
    vector_store.upload_documents(all_documents, embeddings)

    print("Documents uploaded to Qdrant")


if __name__ == "__main__":
    main()