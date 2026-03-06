from pathlib import Path

from pypdf import PdfReader


class PDFLoader:
    def load(self, file_path: str) -> list[dict]:
        path = Path(file_path)
        reader = PdfReader(str(path))

        documents = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()

            if not text:
                continue

            documents.append(
                {
                    "text": text,
                    "metadata": {
                        "source": path.name,
                        "page": page_number,
                    },
                }
            )

        return documents


pdf_loader = PDFLoader()