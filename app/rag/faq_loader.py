import re
from pathlib import Path


class FAQLoader:
    def load(self, file_path: str) -> list[dict]:
        path = Path(file_path)
        content = path.read_text(encoding="utf-8").strip()

        if not content:
            return []

        blocks = re.split(r"\n---\n", content)
        documents = []

        for index, block in enumerate(blocks):
            block = block.strip()
            if not block:
                continue

            question_match = re.search(
                r"## Question\s*\n(.+?)(?=\n## Answer|\Z)",
                block,
                re.DOTALL,
            )
            answer_match = re.search(
                r"## Answer\s*\n(.+)$",
                block,
                re.DOTALL,
            )

            if not question_match or not answer_match:
                continue

            question = question_match.group(1).strip()
            answer = answer_match.group(1).strip()

            if not question or not answer:
                continue

            text = (
                f"Вопрос: {question}\n"
                f"Ответ: {answer}"
            )

            documents.append(
                {
                    "text": text,
                    "metadata": {
                        "source": path.name,
                        "page": None,
                        "chunk_index": index,
                        "doc_type": "faq",
                        "question": question,
                    },
                }
            )

        return documents


faq_loader = FAQLoader()