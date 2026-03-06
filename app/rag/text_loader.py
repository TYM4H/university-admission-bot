from pathlib import Path


class TextLoader:
    def load(self, file_path: str) -> list[dict]:
        path = Path(file_path)
        text = path.read_text(encoding="utf-8").strip()

        if not text:
            return []

        return [
            {
                "text": text,
                "metadata": {
                    "source": path.name,
                    "page": None,
                },
            }
        ]


text_loader = TextLoader()