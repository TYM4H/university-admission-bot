from pathlib import Path

from app.services.embedding_service import embedding_service
from app.rag.faq_loader import faq_loader
from app.rag.pdf_loader import pdf_loader
from app.rag.text_loader import text_loader
from app.rag.text_splitter import text_splitter
from app.rag.vector_store import vector_store


def main():
    data_dir = Path("data")
    all_documents = []

    pdf_files = list(data_dir.rglob("*.pdf"))
    md_files = list(data_dir.rglob("*.md"))
    txt_files = list(data_dir.rglob("*.txt"))

    for pdf_file in pdf_files:
        print(f"Loading PDF {pdf_file.name}")
        documents = pdf_loader.load(str(pdf_file))
        chunked_documents = text_splitter.split_documents(documents)
        all_documents.extend(chunked_documents)

    for md_file in md_files:
        if "faq" in md_file.name.lower():
            print(f"Loading FAQ markdown {md_file.name}")
            documents = faq_loader.load(str(md_file))
            all_documents.extend(documents)
        else:
            print(f"Loading markdown {md_file.name}")
            documents = text_loader.load(str(md_file))
            chunked_documents = text_splitter.split_documents(documents)
            all_documents.extend(chunked_documents)

    for txt_file in txt_files:
        print(f"Loading text {txt_file.name}")
        documents = text_loader.load(str(txt_file))
        chunked_documents = text_splitter.split_documents(documents)
        all_documents.extend(chunked_documents)

    if not all_documents:
        print("No documents found")
        return

    print(f"Total chunks/documents: {len(all_documents)}")

    texts = [document["text"] for document in all_documents]
    embeddings = embedding_service.embed_documents(texts)

    vector_store.create_collection()
    vector_store.upload_documents(all_documents, embeddings)

    print("Documents uploaded to Qdrant")


if __name__ == "__main__":
    main()